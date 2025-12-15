"""
OCR处理服务

提供多引擎OCR识别能力，支持PaddleOCR、Tesseract和UmiOCR

PaddleOCR 3.x 性能优化说明：
1. 设置环境变量避免 OpenMP 库冲突
2. 限制线程数以避免 Windows 上的资源竞争
3. 禁用不必要的日志输出
"""
import PyPDF2
from pdf2image import convert_from_path
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import re
import asyncio
from dotenv import load_dotenv
import os

# ============ PaddleOCR 3.x 环境变量配置（必须在导入前设置）============

# 修复OpenMP库冲突问题
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# 限制 OpenMP 线程数，避免 Windows 上的资源竞争
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

# ===== 关键修复：禁用 oneDNN (MKL-DNN) =====
# oneDNN 在 Windows 上初始化时可能会卡住或非常慢
# 这是导致程序卡在 "oneDNN v3.6.2" 的根本原因
os.environ['FLAGS_use_mkldnn'] = '0'

# 禁用模型源检查，加快启动速度
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

# 设置 PaddlePaddle 日志级别，减少不必要的输出
os.environ['GLOG_v'] = '0'
os.environ['GLOG_logtostderr'] = '0'

# 禁用 PaddleX 的进度条和详细日志
os.environ['PADDLEX_DISABLE_PROGRESS_BAR'] = '1'

# 设置 CPU 线程数（根据你的 CPU 核心数调整，建议设为 1-4）
os.environ['CPU_NUM_THREADS'] = '2'

# 配置Tesseract环境变量（必须在导入pytesseract之前设置）
# 从.env文件读取配置
load_dotenv()

tesseract_cmd = os.getenv('TESSERACT_CMD')
tessdata_prefix = os.getenv('TESSDATA_PREFIX')

if tessdata_prefix:
    os.environ['TESSDATA_PREFIX'] = tessdata_prefix
    print(f"[OCR Service] TESSDATA_PREFIX set to: {tessdata_prefix}")


# OCR引擎导入
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    logging.warning("PaddleOCR not available")

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True

    # 设置Tesseract可执行文件路径
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        print(f"[OCR Service] Tesseract CMD set to: {tesseract_cmd}")

except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("Tesseract not available")

# UmiOCR HTTP 客户端（通过 HTTP API 调用）
try:
    import httpx
    UMIOCR_AVAILABLE = True
except ImportError:
    UMIOCR_AVAILABLE = False
    logging.warning("httpx not available, UmiOCR will not work")


logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """OCR识别区域的边界框"""
    x: float
    y: float
    width: float
    height: float
    page: int


@dataclass
class PageOCRResult:
    """单页OCR识别结果"""
    page_num: int
    text: str
    boxes: List[Dict[str, Any]]  # 包含文本和坐标信息
    confidence: float  # 平均置信度


@dataclass
class OCRResult:
    """完整OCR识别结果"""
    merged_text: str  # 合并后的全文
    page_results: List[PageOCRResult]  # 每页的详细结果
    page_count: int
    engine_used: str  # 使用的OCR引擎
    fallback_used: bool = False  # 是否使用了备用引擎


class OCRService:
    """OCR处理服务"""

    def __init__(self, config: Optional[Dict[str, Any]] = None, fast_mode: bool = True):
        """
        初始化OCR服务

        Args:
            config: 配置字典，包含OCR引擎参数
            fast_mode: 快速模式，使用轻量级模型
        """
        import threading

        self.config = config or {}
        self.fast_mode = fast_mode

        # PaddleOCR引擎（延迟加载）
        self.paddleocr = None
        self._paddleocr_initialized = False
        # PaddleOCR 线程锁，确保同一时间只有一个线程访问 PaddleOCR 实例
        self._paddle_lock = threading.Lock()

        # 初始化Tesseract配置
        # OCR Engine Mode 3, Page Segmentation Mode 6
        self.tesseract_config = '--oem 3 --psm 6'
        if TESSERACT_AVAILABLE:
            logger.info("Tesseract engine available and configured")

        # 初始化 UmiOCR 配置
        self.umiocr_endpoint = self.config.get('umiocr_endpoint') or os.getenv('UMIOCR_ENDPOINT', 'http://localhost:1224')
        self.umiocr_timeout = self.config.get('umiocr_timeout') or int(os.getenv('UMIOCR_TIMEOUT', '60'))
        
        if UMIOCR_AVAILABLE:
            logger.info(f"UmiOCR endpoint configured: {self.umiocr_endpoint}")

    def _ensure_paddleocr(self):
        """
        确保PaddleOCR引擎已初始化（延迟加载）

        PaddleOCR 3.x 重要说明：
        1. 使用简化的初始化方式，让 PaddleOCR 自动选择最优模型
        2. 禁用不必要的预处理模块以提升性能
        3. 在 Windows 上需要特别注意线程安全问题
        """
        if not self._paddleocr_initialized and PADDLEOCR_AVAILABLE:
            try:
                logger.info("Initializing PaddleOCR 3.x engine...")

                # PaddleOCR 3.x 推荐的初始化方式
                # 参考官方文档: https://paddlepaddle.github.io/PaddleOCR/latest/quick_start.html
                #
                # 重要：使用 mobile 模型而不是 server 模型
                # mobile 模型更小、更快，适合大多数场景
                # server 模型在 Windows 上初始化非常慢
                self.paddleocr = PaddleOCR(
                    # 使用 mobile 模型（更快，避免 server 模型的初始化问题）
                    text_detection_model_name='PP-OCRv5_mobile_det',
                    text_recognition_model_name='PP-OCRv5_mobile_rec',
                    # 禁用文档方向分类（提升速度）
                    use_doc_orientation_classify=False,
                    # 禁用文档矫正（提升速度）
                    use_doc_unwarping=False,
                    # 禁用文本行方向分类（提升速度）
                    use_textline_orientation=False,
                )

                logger.info("PaddleOCR engine initialized successfully")
                self._paddleocr_initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize PaddleOCR: {str(e)}")
                self.paddleocr = None
                self._paddleocr_initialized = True  # 标记为已尝试，避免重复尝试

    def _get_page_count(self, file_path: str) -> int:
        """
        获取PDF文件的页数

        Args:
            file_path: PDF文件路径

        Returns:
            页数
        """
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                return len(pdf_reader.pages)
        except Exception as e:
            logger.error(f"Failed to get page count: {str(e)}")
            # 如果是图片文件，返回1
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                return 1
            raise

    def _parse_page_strategy(self, page_strategy: Dict[str, Any], total_pages: int) -> List[int]:
        """
        解析页面处理策略，返回需要处理的页码列表

        Args:
            page_strategy: 页面策略配置
            total_pages: 总页数

        Returns:
            需要处理的页码列表（从1开始）
        """
        mode = page_strategy.get('mode', 'multi_page')

        if mode == 'single_page':
            # 仅处理第一页
            return [1]

        elif mode == 'multi_page':
            # 处理所有页面
            return list(range(1, total_pages + 1))

        elif mode == 'specified_pages':
            # 解析指定页码表达式
            page_expr = page_strategy.get('pages', '1')
            return self._parse_page_expression(page_expr, total_pages)

        else:
            logger.warning(
                f"Unknown page strategy mode: {mode}, defaulting to all pages")
            return list(range(1, total_pages + 1))

    def _parse_page_expression(self, expr: str, total_pages: int) -> List[int]:
        """
        解析页码表达式

        支持的格式:
        - "1": 第1页
        - "1-3": 第1到3页
        - "1,3,5": 第1、3、5页
        - "Last Page": 最后一页
        - "1-3,5,Last Page": 组合表达式

        Args:
            expr: 页码表达式
            total_pages: 总页数

        Returns:
            页码列表
        """
        pages = set()

        # 处理"Last Page"
        expr = expr.replace('Last Page', str(total_pages))
        expr = expr.replace('last page', str(total_pages))

        # 分割逗号
        parts = expr.split(',')

        for part in parts:
            part = part.strip()

            if '-' in part:
                # 范围表达式
                try:
                    start, end = part.split('-')
                    start = int(start.strip())
                    end = int(end.strip())
                    pages.update(range(start, end + 1))
                except ValueError:
                    logger.warning(f"Invalid page range: {part}")
            else:
                # 单个页码
                try:
                    page_num = int(part)
                    if 1 <= page_num <= total_pages:
                        pages.add(page_num)
                except ValueError:
                    logger.warning(f"Invalid page number: {part}")

        return sorted(list(pages))

    async def _ocr_single_page(
        self,
        file_path: str,
        page_num: int,
        engine: str,
        language: str = 'eng'
    ) -> PageOCRResult:
        """
        对单页执行OCR识别

        Args:
            file_path: 文件路径
            page_num: 页码（从1开始）
            engine: OCR引擎名称 ('paddleocr', 'tesseract', 'azure')
            language: 语言设置

        Returns:
            单页OCR结果
        """
        # 如果是PDF，先转换为图片
        if file_path.lower().endswith('.pdf'):
            image_path = await self._convert_pdf_page_to_image(file_path, page_num)
        else:
            image_path = file_path

        try:
            if engine == 'paddleocr':
                return await self._ocr_with_paddleocr(image_path, page_num)
            elif engine == 'tesseract':
                return await self._ocr_with_tesseract(image_path, page_num, language)
            elif engine == 'umiocr':
                return await self._ocr_with_umiocr(image_path, page_num, language)
            else:
                raise ValueError(f"Unsupported OCR engine: {engine}")
        finally:
            # 清理临时图片文件
            if file_path.lower().endswith('.pdf') and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temp image: {str(e)}")

    async def _convert_pdf_page_to_image(self, pdf_path: str, page_num: int) -> str:
        """
        将PDF的指定页转换为图片

        Args:
            pdf_path: PDF文件路径
            page_num: 页码（从1开始）

        Returns:
            图片文件路径
        """
        try:
            # 使用pdf2image转换，DPI=300
            images = convert_from_path(
                pdf_path,
                dpi=300,
                first_page=page_num,
                last_page=page_num,
                fmt='png'
            )

            if not images:
                raise ValueError(f"Failed to convert page {page_num}")

            # 保存到临时文件
            import tempfile
            import uuid
            temp_dir = tempfile.gettempdir()
            ocr_temp_dir = os.path.join(temp_dir, 'ocr_processing')
            os.makedirs(ocr_temp_dir, exist_ok=True)

            # 使用UUID确保文件名唯一，避免并发冲突
            unique_id = str(uuid.uuid4())[:8]
            temp_path = os.path.join(
                ocr_temp_dir, f"page_{page_num}_{os.getpid()}_{unique_id}.png")
            images[0].save(temp_path, 'PNG')
            logger.debug(
                f"PDF page {page_num} converted to image: {temp_path}")

            return temp_path
        except Exception as e:
            logger.error(f"Failed to convert PDF page to image: {str(e)}")
            raise

    async def _ocr_with_paddleocr(self, image_path: str, page_num: int, max_retries: int = 3) -> PageOCRResult:
        """
        使用PaddleOCR进行识别

        Args:
            image_path: 图片路径
            page_num: 页码
            max_retries: 最大重试次数（用于处理 Windows 上的 Unknown exception）

        Returns:
            OCR结果

        注意：
            PaddleOCR 3.x 在 Windows 上存在已知的 "Unknown exception" 问题，
            这通常是由于底层推理引擎的资源竞争导致的。
            解决方案：
            1. 使用线程锁确保串行访问
            2. 增加重试机制
            3. 在重试前释放资源并等待
        """
        # 延迟初始化PaddleOCR
        self._ensure_paddleocr()

        if not self.paddleocr:
            raise RuntimeError("PaddleOCR engine not available")

        last_error = None

        for attempt in range(max_retries + 1):
            try:
                # 验证图片文件存在
                if not os.path.exists(image_path):
                    raise FileNotFoundError(
                        f"Image file not found: {image_path}")

                # 检查文件大小
                file_size = os.path.getsize(image_path)
                if attempt > 0:
                    logger.info(
                        f"Retry {attempt}/{max_retries} for page {page_num}")
                    # 在重试前等待更长时间，让资源完全释放
                    # Windows 上 PaddlePaddle 的资源释放可能较慢
                    await asyncio.sleep(1.0 + attempt * 0.5)

                    # 强制进行垃圾回收，帮助释放资源
                    import gc
                    gc.collect()

                logger.info(
                    f"Starting PaddleOCR prediction for page {page_num}, image: {image_path}, size: {file_size} bytes")

                # PaddleOCR 3.x 使用 predict() 方法
                # 注意：PaddleOCR 实例不是线程安全的
                # 使用锁确保同一时间只有一个线程访问 PaddleOCR 实例
                def _predict_sync():
                    with self._paddle_lock:
                        return self.paddleocr.predict(image_path)

                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    _predict_sync
                )

                # 如果成功，跳出重试循环
                break

            except RuntimeError as e:
                last_error = e
                error_msg = str(e)
                # 检查是否是 "Unknown exception" 错误，这是 Windows 上 PaddleX 的已知问题
                if "Unknown exception" in error_msg and attempt < max_retries:
                    logger.warning(
                        f"PaddleOCR RuntimeError for page {page_num} (attempt {attempt + 1}): {error_msg}, will retry...")
                    continue
                else:
                    raise
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    logger.warning(
                        f"PaddleOCR error for page {page_num} (attempt {attempt + 1}): {str(e)}, will retry...")
                    continue
                else:
                    raise
        # 处理结果
        try:
            # 调试：打印返回结果
            logger.info(f"PaddleOCR prediction completed")
            logger.info(f"Result type: {type(result)}")
            logger.info(f"Result is None: {result is None}")
            logger.info(f"Result length: {len(result) if result else 'N/A'}")

            # 打印 result 的前100个字符
            result_str = str(result)[:200]
            logger.info(f"Result preview: {result_str}")

            # PaddleOCR 3.x 的 predict() 返回一个列表，每个元素对应一个输入图像的结果
            # 结果是一个 Result 对象，需要访问其属性
            if not result or len(result) == 0:
                logger.warning(
                    f"PaddleOCR returned empty result for page {page_num}")
                return PageOCRResult(
                    page_num=page_num,
                    text="",
                    boxes=[],
                    confidence=0.0
                )

            # 获取第一个结果（因为我们只传入了一张图片）
            ocr_result = result[0]
            logger.info(f"OCR result object type: {type(ocr_result)}")
            logger.info(f"OCR result attributes: {dir(ocr_result)}")

            # 访问结果的 json 属性获取数据
            result_data = ocr_result.json
            logger.info(
                f"Result data keys: {result_data.keys() if isinstance(result_data, dict) else 'not a dict'}")

            # PaddleOCR 3.x 的结果在 res 字段中
            res = result_data.get('res', {})
            logger.info(
                f"res keys: {res.keys() if isinstance(res, dict) else 'not a dict'}")

            # 检查是否有识别结果
            rec_texts = res.get('rec_texts', [])
            rec_scores = res.get('rec_scores', [])
            rec_polys = res.get('rec_polys', [])

            if not rec_texts:
                logger.warning(f"No text recognized for page {page_num}")
                return PageOCRResult(
                    page_num=page_num,
                    text="",
                    boxes=[],
                    confidence=0.0
                )

            # 解析结果
            texts = []
            boxes = []
            confidences = []

            # 遍历识别结果
            import numpy as np
            for i, (text, score, poly) in enumerate(zip(rec_texts, rec_scores, rec_polys)):
                if not text:
                    continue

                texts.append(text)
                confidences.append(score)

                # poly 是一个 numpy 数组，形状为 (4, 2)，表示四个顶点坐标
                if isinstance(poly, np.ndarray):
                    x_coords = poly[:, 0]
                    y_coords = poly[:, 1]
                else:
                    # 如果是列表格式
                    x_coords = [p[0] for p in poly]
                    y_coords = [p[1] for p in poly]

                boxes.append({
                    'text': text,
                    'confidence': float(score),
                    'box': {
                        'x': int(min(x_coords)),
                        'y': int(min(y_coords)),
                        'width': int(max(x_coords) - min(x_coords)),
                        'height': int(max(y_coords) - min(y_coords))
                    },
                    'page': page_num
                })

            # 合并文本
            merged_text = '\n'.join(texts)
            avg_confidence = sum(confidences) / \
                len(confidences) if confidences else 0.0

            logger.info(
                f"PaddleOCR recognized {len(texts)} text blocks for page {page_num}")

            return PageOCRResult(
                page_num=page_num,
                text=merged_text,
                boxes=boxes,
                confidence=avg_confidence
            )

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            logger.error(
                f"PaddleOCR result parsing failed for page {page_num}: {str(e)}\nTraceback:\n{error_detail}")
            raise RuntimeError(
                f"PaddleOCR failed for page {page_num}: {str(e)}")

    async def _ocr_with_tesseract(
        self,
        image_path: str,
        page_num: int,
        language: str = 'eng'
    ) -> PageOCRResult:
        """
        使用Tesseract进行识别

        Args:
            image_path: 图片路径
            page_num: 页码
            language: 语言设置 (chi_sim=简体中文, eng=英文)
                     注意: 需要先安装对应的语言包

        Returns:
            OCR结果
        """
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("Tesseract engine not available")

        try:
            # 打开图片
            image = Image.open(image_path)

            # Tesseract识别（同步调用，在线程池中执行）
            loop = asyncio.get_event_loop()

            # 获取文本
            text = await loop.run_in_executor(
                None,
                pytesseract.image_to_string,
                image,
                language,
                self.tesseract_config
            )

            # 获取详细数据（包含坐标和置信度）
            # pytesseract.image_to_data 需要使用 output_type 参数
            from pytesseract import Output
            data = await loop.run_in_executor(
                None,
                lambda: pytesseract.image_to_data(
                    image,
                    lang=language,
                    config=self.tesseract_config,
                    output_type=Output.DICT
                )
            )

            # 解析结果
            boxes = []
            confidences = []

            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:  # 过滤无效结果
                    boxes.append({
                        'text': data['text'][i],
                        # 转换为0-1范围
                        'confidence': float(data['conf'][i]) / 100.0,
                        'box': {
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        },
                        'page': page_num
                    })
                    confidences.append(float(data['conf'][i]) / 100.0)

            avg_confidence = sum(confidences) / \
                len(confidences) if confidences else 0.0

            return PageOCRResult(
                page_num=page_num,
                text=text.strip(),
                boxes=boxes,
                confidence=avg_confidence
            )

        except Exception as e:
            logger.error(f"Tesseract failed for page {page_num}: {str(e)}")
            raise

    async def _ocr_with_umiocr(self, image_path: str, page_num: int, language: str = 'ch') -> PageOCRResult:
        """
        使用 UmiOCR 进行识别（通过 HTTP API）

        UmiOCR 是一个开源的离线 OCR 软件，支持多种语言。
        通过 Docker 部署后提供 HTTP 接口服务。

        API 文档: https://github.com/hiroi-sora/Umi-OCR/blob/main/docs/http/api_ocr.md

        Args:
            image_path: 图片路径
            page_num: 页码
            language: 语言设置 (ch=简体中文, en=英文, japan=日语等)

        Returns:
            OCR结果
        """
        if not UMIOCR_AVAILABLE:
            raise RuntimeError("httpx not available, UmiOCR cannot be used")

        try:
            import base64
            
            # 读取图片并转换为 Base64
            with open(image_path, 'rb') as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            # 构建请求参数
            # UmiOCR 语言映射
            language_map = {
                'ch': 'models/config_chinese.txt',
                'chi_sim': 'models/config_chinese.txt',
                'eng': 'models/config_en.txt',
                'en': 'models/config_en.txt',
                'chi_tra': 'models/config_chinese_cht(v2).txt',
                'jpn': 'models/config_japan.txt',
                'japan': 'models/config_japan.txt',
                'kor': 'models/config_korean.txt',
                'korean': 'models/config_korean.txt',
                'rus': 'models/config_cyrillic.txt',
            }
            
            ocr_language = language_map.get(language, 'models/config_chinese.txt')
            
            request_data = {
                'base64': image_base64,
                'options': {
                    'ocr.language': ocr_language,
                    'data.format': 'dict',  # 返回详细信息（包含坐标和置信度）
                    'tbpu.parser': 'multi_para',  # 多栏-按自然段换行
                }
            }

            # 调用 UmiOCR API
            api_url = f"{self.umiocr_endpoint}/api/ocr"
            
            async with httpx.AsyncClient(timeout=self.umiocr_timeout) as client:
                response = await client.post(
                    api_url,
                    json=request_data,
                    headers={'Content-Type': 'application/json'}
                )
                response.raise_for_status()
                result = response.json()

            # 解析结果
            # UmiOCR 返回格式:
            # {
            #     "code": 100,  # 100=成功, 101=无文本, 其他=失败
            #     "data": [...],  # 识别结果列表
            #     "time": 0.5,  # 耗时
            # }
            
            code = result.get('code', -1)
            
            if code == 101:
                # 无文本
                logger.info(f"UmiOCR: No text found on page {page_num}")
                return PageOCRResult(
                    page_num=page_num,
                    text="",
                    boxes=[],
                    confidence=0.0
                )
            
            if code != 100:
                # 识别失败
                error_msg = result.get('data', 'Unknown error')
                raise RuntimeError(f"UmiOCR failed: {error_msg}")

            # 解析识别结果
            data = result.get('data', [])
            
            texts = []
            boxes = []
            confidences = []

            for item in data:
                text = item.get('text', '')
                if not text:
                    continue
                    
                score = item.get('score', 1.0)
                box_coords = item.get('box', [[0, 0], [0, 0], [0, 0], [0, 0]])
                end_char = item.get('end', '')
                
                texts.append(text + end_char)
                confidences.append(score)

                # box 格式: [[左上x,y], [右上x,y], [右下x,y], [左下x,y]]
                x_coords = [p[0] for p in box_coords]
                y_coords = [p[1] for p in box_coords]

                boxes.append({
                    'text': text,
                    'confidence': float(score),
                    'box': {
                        'x': int(min(x_coords)),
                        'y': int(min(y_coords)),
                        'width': int(max(x_coords) - min(x_coords)),
                        'height': int(max(y_coords) - min(y_coords))
                    },
                    'page': page_num
                })

            merged_text = ''.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            logger.info(f"UmiOCR recognized {len(texts)} text blocks for page {page_num}")

            return PageOCRResult(
                page_num=page_num,
                text=merged_text,
                boxes=boxes,
                confidence=avg_confidence
            )

        except httpx.TimeoutException:
            logger.error(f"UmiOCR timeout for page {page_num}")
            raise RuntimeError(f"UmiOCR timeout for page {page_num}")
        except httpx.HTTPStatusError as e:
            logger.error(f"UmiOCR HTTP error for page {page_num}: {e.response.status_code}")
            raise RuntimeError(f"UmiOCR HTTP error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"UmiOCR failed for page {page_num}: {str(e)}")
            raise

    async def _sequential_ocr(
        self,
        file_path: str,
        pages: List[int],
        engine: str,
        language: str = 'eng'
    ) -> List[PageOCRResult]:
        """
        顺序处理OCR（用于少量页面）

        Args:
            file_path: 文件路径
            pages: 页码列表
            engine: OCR引擎
            language: 语言设置

        Returns:
            OCR结果列表
        """
        results = []
        for page_num in pages:
            try:
                result = await self._ocr_single_page(file_path, page_num, engine, language)
                results.append(result)
            except Exception as e:
                logger.error(f"OCR failed for page {page_num}: {str(e)}")
                # 添加空结果
                results.append(PageOCRResult(
                    page_num=page_num,
                    text="",
                    boxes=[],
                    confidence=0.0
                ))

        return results

    async def _parallel_ocr(
        self,
        file_path: str,
        pages: List[int],
        engine: str,
        language: str = 'eng',
        max_parallel: int = 4
    ) -> List[PageOCRResult]:
        """
        并行处理OCR（用于多页文档）

        Args:
            file_path: 文件路径
            pages: 页码列表
            engine: OCR引擎
            language: 语言设置
            max_parallel: 最大并行数

        Returns:
            OCR结果列表（按页码顺序）
        """
        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(max_parallel)

        async def process_with_semaphore(page_num: int) -> PageOCRResult:
            async with semaphore:
                try:
                    return await self._ocr_single_page(file_path, page_num, engine, language)
                except Exception as e:
                    logger.error(f"OCR failed for page {page_num}: {str(e)}")
                    return PageOCRResult(
                        page_num=page_num,
                        text="",
                        boxes=[],
                        confidence=0.0
                    )

        # 并行处理所有页面
        tasks = [process_with_semaphore(page_num) for page_num in pages]
        results = await asyncio.gather(*tasks)

        # 按页码排序
        results.sort(key=lambda x: x.page_num)

        return results

    def _merge_ocr_text(
        self,
        page_results: List[PageOCRResult],
        separator: str = '\n'
    ) -> str:
        """
        合并多页OCR文本

        Args:
            page_results: 页面OCR结果列表
            separator: 页面分隔符（默认换行符）

        Returns:
            合并后的全文（Global_Context_String）
        """
        texts = [result.text for result in page_results if result.text]
        return separator.join(texts)

    async def _try_fallback_engine(
        self,
        file_path: str,
        pages: List[int],
        primary_engine: str,
        fallback_engine: str,
        language: str = 'eng'
    ) -> Tuple[List[PageOCRResult], bool]:
        """
        尝试使用备用引擎

        Args:
            file_path: 文件路径
            pages: 页码列表
            primary_engine: 主引擎
            fallback_engine: 备用引擎
            language: 语言设置

        Returns:
            (OCR结果列表, 是否使用了备用引擎)
        """
        # 先尝试主引擎
        try:
            # PaddleOCR 必须顺序处理，避免并发导致的 RuntimeError
            if primary_engine == 'paddleocr':
                results = await self._sequential_ocr(file_path, pages, primary_engine, language)
            elif len(pages) > 5:
                results = await self._parallel_ocr(file_path, pages, primary_engine, language)
            else:
                results = await self._sequential_ocr(file_path, pages, primary_engine, language)

            # 检查是否有有效结果
            has_valid_result = any(result.text.strip() for result in results)

            if has_valid_result:
                return results, False

            # 主引擎返回空结果，尝试备用引擎
            logger.warning(
                f"Primary engine {primary_engine} returned empty results, trying fallback engine {fallback_engine}")

        except Exception as e:
            logger.error(
                f"Primary engine {primary_engine} failed: {str(e)}, trying fallback engine {fallback_engine}")

        # 使用备用引擎
        try:
            # PaddleOCR 必须顺序处理
            if fallback_engine == 'paddleocr':
                results = await self._sequential_ocr(file_path, pages, fallback_engine, language)
            elif len(pages) > 5:
                results = await self._parallel_ocr(file_path, pages, fallback_engine, language)
            else:
                results = await self._sequential_ocr(file_path, pages, fallback_engine, language)

            logger.info(f"Fallback engine {fallback_engine} used successfully")
            return results, True

        except Exception as e:
            logger.error(
                f"Fallback engine {fallback_engine} also failed: {str(e)}")
            # 返回空结果
            return [
                PageOCRResult(page_num=p, text="", boxes=[], confidence=0.0)
                for p in pages
            ], True

    async def process_document(
        self,
        file_path: str,
        engine: str = 'paddleocr',
        page_strategy: Optional[Dict[str, Any]] = None,
        language: str = 'eng',
        enable_fallback: bool = False,
        fallback_engine: Optional[str] = None
    ) -> OCRResult:
        """
        处理文档OCR识别

        Args:
            file_path: 文件路径
            engine: OCR引擎 ('paddleocr', 'tesseract', 'azure')
            page_strategy: 页面处理策略
            language: 语言设置
            enable_fallback: 是否启用备用引擎
            fallback_engine: 备用引擎名称

        Returns:
            完整OCR结果
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # 获取页数
        page_count = self._get_page_count(file_path)
        logger.info(
            f"Processing document: {file_path}, total pages: {page_count}")

        # 解析页面策略
        if page_strategy is None:
            page_strategy = {'mode': 'multi_page'}

        pages_to_process = self._parse_page_strategy(page_strategy, page_count)
        logger.info(f"Pages to process: {pages_to_process}")

        # 执行OCR
        if enable_fallback and fallback_engine:
            # 使用备用引擎降级机制
            page_results, fallback_used = await self._try_fallback_engine(
                file_path,
                pages_to_process,
                engine,
                fallback_engine,
                language
            )
            engine_used = fallback_engine if fallback_used else engine
        else:
            # 不使用备用引擎
            # 注意：PaddleOCR 的底层推理引擎在 Windows 上不支持真正的并发
            # 强制使用顺序处理以避免 "Unknown exception" 错误
            if engine == 'paddleocr':
                # PaddleOCR 必须顺序处理，避免并发导致的 RuntimeError
                logger.info(
                    f"Using sequential processing for PaddleOCR (thread-safety)")
                page_results = await self._sequential_ocr(
                    file_path,
                    pages_to_process,
                    engine,
                    language
                )
            elif len(pages_to_process) > 5:
                # 其他引擎可以并行处理
                page_results = await self._parallel_ocr(
                    file_path,
                    pages_to_process,
                    engine,
                    language,
                    max_parallel=self.config.get('max_parallel', 4)
                )
            else:
                page_results = await self._sequential_ocr(
                    file_path,
                    pages_to_process,
                    engine,
                    language
                )
            engine_used = engine
            fallback_used = False

        # 合并文本
        separator = page_strategy.get('separator', '\n')
        merged_text = self._merge_ocr_text(page_results, separator)

        logger.info(f"OCR completed: {len(page_results)} pages processed, "
                    f"merged text length: {len(merged_text)}, "
                    f"engine: {engine_used}, fallback: {fallback_used}")

        return OCRResult(
            merged_text=merged_text,
            page_results=page_results,
            page_count=len(page_results),
            engine_used=engine_used,
            fallback_used=fallback_used
        )


# 便捷函数
async def create_ocr_service(config: Optional[Dict[str, Any]] = None) -> OCRService:
    """
    创建OCR服务实例

    Args:
        config: 配置字典

    Returns:
        OCR服务实例
    """
    return OCRService(config)
