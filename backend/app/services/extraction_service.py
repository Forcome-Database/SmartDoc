"""
数据提取服务

提供多种数据提取策略：正则提取、锚点定位提取、表格提取等
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .ocr_service import OCRResult, PageOCRResult

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """字段提取结果"""
    field_name: str
    value: Any
    confidence: float
    source_page: Optional[int] = None
    extraction_method: Optional[str] = None


class ExtractionService:
    """数据提取服务"""

    def __init__(self):
        """初始化提取服务"""
        pass

    def _is_field_in_schema(self, field_name: str, schema: Dict[str, Any]) -> bool:
        """
        检查字段是否在schema中定义（支持嵌套字段）

        Args:
            field_name: 字段名，支持点号分隔的嵌套路径，如 "jinge.ext_price"
            schema: schema定义

        Returns:
            字段是否存在于schema中
        """
        if not field_name or not schema:
            return False

        # 如果是顶层字段，直接检查
        if field_name in schema:
            return True

        # 处理嵌套字段（如 jinge.ext_price）
        parts = field_name.split('.')
        current = schema

        for i, part in enumerate(parts):
            if part not in current:
                return False

            node = current[part]

            # 如果是最后一个部分，找到了
            if i == len(parts) - 1:
                return True

            # 继续向下查找
            node_type = node.get('nodeType', '')
            if node_type == 'object' and 'properties' in node:
                current = node['properties']
            elif node_type == 'array' and 'items' in node:
                current = node['items']
            elif node_type == 'table' and 'columns' in node:
                current = node['columns']
            else:
                # 无法继续向下查找
                return False

        return False

    def _get_field_schema(self, field_name: str, schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        获取字段的schema定义（支持嵌套字段）

        Args:
            field_name: 字段名，支持点号分隔的嵌套路径
            schema: schema定义

        Returns:
            字段的schema定义，如果不存在返回None
        """
        if not field_name or not schema:
            return None

        # 如果是顶层字段，直接返回
        if field_name in schema:
            return schema[field_name]

        # 处理嵌套字段
        parts = field_name.split('.')
        current = schema

        for i, part in enumerate(parts):
            if part not in current:
                return None

            node = current[part]

            # 如果是最后一个部分，返回该节点
            if i == len(parts) - 1:
                return node

            # 继续向下查找
            node_type = node.get('nodeType', '')
            if node_type == 'object' and 'properties' in node:
                current = node['properties']
            elif node_type == 'array' and 'items' in node:
                current = node['items']
            elif node_type == 'table' and 'columns' in node:
                current = node['columns']
            else:
                return None

        return None

    async def extract_fields(
        self,
        ocr_result: OCRResult,
        schema: Dict[str, Any],
        extraction_rules: List[Dict[str, Any]],
        extraction_config: Optional[Dict[str, Any]] = None
    ) -> tuple[Dict[str, ExtractionResult], Dict[str, Any]]:
        """
        提取字段主函数

        遍历schema中的所有字段，根据extraction_rules执行提取
        支持批量LLM提取（一次请求提取所有LLM类型字段，严格按Schema结构输出）

        Args:
            ocr_result: OCR识别结果
            schema: 字段schema定义
            extraction_rules: 提取规则列表
            extraction_config: 原始提取配置字典（用于LLM提取时构建output schema）

        Returns:
            (字段提取结果字典, LLM统计信息)
            结果格式: {field_name: ExtractionResult}
            统计信息格式: {token_count: int, cost: float}
        """
        results = {}
        llm_stats = {'token_count': 0, 'cost': 0.0}

        # 如果没有传入extraction_config，从extraction_rules构建
        if extraction_config is None:
            extraction_config = {}
            for rule in extraction_rules:
                field_name = rule.get('field')
                if field_name:
                    extraction_config[field_name] = rule

        # 分离LLM提取规则和其他提取规则
        llm_rules = []
        other_rules = []

        for rule in extraction_rules:
            field_name = rule.get('field')
            if not field_name:
                logger.warning(f"提取规则缺少field字段: {rule}")
                continue

            # 检查字段是否在schema中定义（支持嵌套字段）
            if not self._is_field_in_schema(field_name, schema):
                logger.warning(f"字段 {field_name} 未在schema中定义")
                continue

            extraction_type = rule.get('type')
            if extraction_type == 'llm':
                llm_rules.append(rule)
            else:
                other_rules.append(rule)

        # 1. 先处理非LLM提取规则
        for rule in other_rules:
            field_name = rule.get('field')
            extraction_type = rule.get('type')

            # 获取字段的schema定义，用于判断字段类型
            field_schema = self._get_field_schema(field_name, schema)

            try:
                if extraction_type == 'regex':
                    value, confidence, source_page = await self._extract_by_regex(
                        ocr_result, rule, field_schema
                    )
                elif extraction_type == 'anchor':
                    value, confidence, source_page = await self._extract_by_anchor(
                        ocr_result, rule, field_schema
                    )
                elif extraction_type == 'table':
                    value, confidence, source_page = await self._extract_from_table(
                        ocr_result, rule, field_schema
                    )
                else:
                    logger.warning(f"不支持的提取类型: {extraction_type}")
                    continue

                results[field_name] = ExtractionResult(
                    field_name=field_name,
                    value=value,
                    confidence=confidence,
                    source_page=source_page,
                    extraction_method=extraction_type
                )

                logger.info(
                    f"字段 {field_name} 提取成功: value={value}, confidence={confidence}")

            except Exception as e:
                logger.error(f"字段 {field_name} 提取失败: {str(e)}")
                results[field_name] = ExtractionResult(
                    field_name=field_name,
                    value=None,
                    confidence=0.0,
                    source_page=None,
                    extraction_method=extraction_type
                )

        # 2. 批量处理LLM提取规则（一次请求提取所有字段，严格按Schema结构输出）
        if llm_rules:
            llm_results, batch_llm_stats = await self._extract_with_llm_batch(
                ocr_result, llm_rules, schema, extraction_config
            )

            # 累计LLM统计信息
            llm_stats['token_count'] += batch_llm_stats.get('token_count', 0)
            
            # 计算费用
            from app.services.llm_service import llm_service
            llm_stats['cost'] = llm_service.calculate_cost(llm_stats['token_count'])

            # LLM返回的是顶层字段结构，直接使用
            for field_name, llm_result in llm_results.items():
                results[field_name] = ExtractionResult(
                    field_name=field_name,
                    value=llm_result.get('value'),
                    confidence=llm_result.get('confidence', 0.0),
                    source_page=llm_result.get('source_page'),
                    extraction_method='llm'
                )

        return results, llm_stats

    async def _extract_with_llm_batch(
        self,
        ocr_result: OCRResult,
        llm_rules: List[Dict[str, Any]],
        schema: Dict[str, Any],
        extraction_config: Dict[str, Any]
    ) -> tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
        """
        批量使用LLM提取多个字段（一次请求，严格按Schema结构输出）

        Args:
            ocr_result: OCR识别结果
            llm_rules: LLM提取规则列表
            schema: schema定义
            extraction_config: 提取配置字典

        Returns:
            (提取结果字典, LLM统计信息)
            提取结果格式: {field_name: {value: 原始值（可能是嵌套结构）, confidence, ...}}
            统计信息格式: {token_count: int, duration: float}
        """
        llm_stats = {'token_count': 0, 'duration': 0.0}
        
        try:
            from app.services.llm_service import llm_service, AGENTLY_AVAILABLE

            if not AGENTLY_AVAILABLE:
                logger.warning("Agently未安装，LLM批量提取功能不可用")
                return {}, llm_stats

            # 转换OCR结果为字典格式
            ocr_result_dict = {
                'merged_text': ocr_result.merged_text,
                'page_results': [
                    {
                        'text': page.text,
                        'page_num': page.page_num,
                        'confidence': page.confidence,
                        'blocks': page.boxes
                    }
                    for page in ocr_result.page_results
                ]
            }

            # 获取上下文配置（使用第一个规则的配置）
            first_rule = llm_rules[0] if llm_rules else {}
            context_scope = first_rule.get('contextScope', 'all_pages')
            n_pages = first_rule.get('pageCount', 3)

            logger.info(f"开始LLM Schema提取: {len(llm_rules)}个字段")

            # 调用LLM Schema提取（一次请求，严格按Schema结构输出）
            llm_result = await llm_service.extract_by_schema(
                ocr_result_dict,
                schema,
                extraction_config,
                context_scope,
                n_pages
            )

            if not llm_result:
                logger.warning("LLM Schema提取返回空结果")
                return {}, llm_stats

            # 提取LLM统计信息
            llm_stats = {
                'token_count': llm_result.get('token_count', 0),
                'duration': llm_result.get('duration', 0.0)
            }

            # 从LLM结果中提取数据（保持原始嵌套结构）
            extracted_data = llm_result.get('data', {})

            # 直接返回LLM的原始结构，每个顶层字段作为一个结果
            results = {}
            for field_key, field_value in extracted_data.items():
                # 获取字段的schema定义用于置信度计算
                field_schema = schema.get(field_key, {})

                # 动态计算置信度
                confidence = self._calculate_llm_confidence(
                    ocr_result, field_value, field_schema
                )

                results[field_key] = {
                    'value': field_value,  # 保持原始结构（可能是数组、对象等）
                    'confidence': confidence,
                    'explanation': 'LLM Schema提取',
                    'source_page': None
                }
                logger.info(
                    f"LLM提取成功: {field_key}={field_value}, 置信度={confidence}%")

            return results, llm_stats

        except Exception as e:
            logger.error(f"LLM批量提取失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}, llm_stats

    def _flatten_extraction_results(
        self,
        data: Any,
        schema: Dict[str, Any],
        extraction_config: Dict[str, Any],
        results: Dict[str, Dict[str, Any]],
        ocr_result: OCRResult,
        parent_path: str
    ):
        """
        将嵌套的LLM提取结果展平为 field_path -> value 的格式

        Args:
            data: LLM返回的数据
            schema: Schema定义
            extraction_config: 提取配置
            results: 结果字典（会被修改）
            ocr_result: OCR结果（用于查找来源页码）
            parent_path: 父路径
        """
        if not isinstance(data, dict) or not isinstance(schema, dict):
            return

        for field_key, field_def in schema.items():
            field_path = f"{parent_path}.{field_key}" if parent_path else field_key
            node_type = field_def.get('nodeType', 'field')

            field_value = data.get(field_key)

            # 检查该字段是否配置了LLM提取
            if field_path in extraction_config:
                # 该字段配置了LLM提取，记录结果
                # 动态计算置信度
                confidence = self._calculate_llm_confidence(
                    ocr_result, field_value, field_def)

                if node_type == 'field':
                    # 普通字段
                    source_page = self._find_text_page(
                        ocr_result, str(field_value)) if field_value else None
                    results[field_path] = {
                        'value': field_value,
                        'confidence': confidence,
                        'explanation': 'LLM Schema提取',
                        'source_page': source_page
                    }
                    logger.info(
                        f"LLM提取成功: {field_path}={field_value}, 置信度={confidence}%")

                elif node_type in ('array', 'table'):
                    # 数组/表格类型
                    results[field_path] = {
                        'value': field_value,
                        'confidence': confidence,
                        'explanation': 'LLM Schema提取（数组）',
                        'source_page': None
                    }
                    logger.info(
                        f"LLM提取成功: {field_path}={field_value}, 置信度={confidence}%")

            # 递归处理嵌套结构
            if node_type == 'object' and isinstance(field_value, dict):
                properties = field_def.get('properties', {})
                self._flatten_extraction_results(
                    field_value, properties, extraction_config, results, ocr_result, field_path
                )
            elif node_type in ('array', 'table') and isinstance(field_value, list):
                # 对于数组，检查子字段是否有单独的提取配置
                items = field_def.get('items', field_def.get('columns', {}))
                for item in field_value:
                    if isinstance(item, dict):
                        self._flatten_extraction_results(
                            item, items, extraction_config, results, ocr_result, field_path
                        )

    async def _extract_by_regex(
        self,
        ocr_result: OCRResult,
        rule: Dict[str, Any],
        field_schema: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[Any], float, Optional[int]]:
        """
        正则提取函数

        在Global_Context_String中执行正则匹配
        支持提取第一个匹配或所有匹配
        支持捕获组功能
        根据字段schema类型决定返回格式（数组字段返回数组）

        Args:
            ocr_result: OCR识别结果
            rule: 提取规则，包含pattern、match_mode等
            field_schema: 字段的schema定义，用于判断字段类型

        Returns:
            (提取值, 置信度, 来源页码)
        """
        pattern = rule.get('pattern')
        if not pattern:
            raise ValueError("正则提取规则缺少pattern字段")

        # 获取匹配模式：first（第一个）或 all（所有）
        # 前端使用matchMode，后端使用match_mode
        match_mode = rule.get('match_mode') or rule.get('matchMode', 'first')

        # 捕获组索引
        # 前端使用captureGroup，后端使用capture_group
        # 注意：0是有效值（表示整个匹配），不能用 or 运算符
        capture_group = rule.get('captureGroup')
        if capture_group is None:
            capture_group = rule.get('capture_group')
        if capture_group is None:
            capture_group = 1  # 默认使用第一个捕获组

        # 是否使用捕获组（0表示整个匹配，>0表示使用指定捕获组）
        use_group = capture_group > 0

        # 正则标志
        flags = re.IGNORECASE if rule.get('ignore_case', False) else 0

        try:
            # 在合并文本中执行正则匹配
            text = ocr_result.merged_text

            if match_mode == 'all':
                # 提取所有匹配
                matches = re.finditer(pattern, text, flags)
                values = []

                for match in matches:
                    if use_group and match.groups():
                        # 使用指定的捕获组
                        try:
                            values.append(match.group(capture_group))
                        except IndexError:
                            values.append(match.group(0))
                    else:
                        # 使用完整匹配
                        values.append(match.group(0))

                if not values:
                    return None, 0.0, None

                # 返回数组格式（适用于数组类型字段）
                # 如果只有一个匹配且不是数组字段，返回字符串
                result_value = values

            else:
                # 提取第一个匹配
                match = re.search(pattern, text, flags)

                if not match:
                    return None, 0.0, None

                if use_group and match.groups():
                    # 使用指定的捕获组
                    try:
                        result_value = match.group(capture_group)
                    except IndexError:
                        result_value = match.group(0)
                else:
                    # 使用完整匹配
                    result_value = match.group(0)

            # 判断字段是否为数组类型
            is_array_field = False
            if field_schema:
                node_type = field_schema.get('nodeType', 'field')
                is_array_field = node_type in ('array', 'table')

            # 如果字段是数组类型，确保返回数组格式
            if is_array_field:
                if not isinstance(result_value, list):
                    result_value = [result_value]

            # 查找匹配文本所在的页码
            if isinstance(result_value, list):
                # 数组类型，使用第一个元素查找页码
                first_value = result_value[0] if result_value else ''
                source_page = self._find_text_page(ocr_result, first_value)
            else:
                source_page = self._find_text_page(ocr_result, result_value)

            # 计算置信度（基于OCR置信度）
            confidence = self._calculate_confidence(
                ocr_result,
                result_value[0] if isinstance(
                    result_value, list) else result_value,
                source_page
            )

            return result_value, confidence, source_page

        except re.error as e:
            logger.error(f"正则表达式错误: {pattern}, error: {str(e)}")
            raise ValueError(f"无效的正则表达式: {pattern}")
        except Exception as e:
            logger.error(f"正则提取失败: {str(e)}")
            raise

    async def _extract_by_anchor(
        self,
        ocr_result: OCRResult,
        rule: Dict[str, Any],
        field_schema: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[Any], float, Optional[int]]:
        """
        锚点定位提取函数

        查找锚点关键词位置，根据相对位置（右侧、下方、右下方）提取目标文本
        支持配置提取范围（最大字符数或坐标偏移）
        根据字段schema类型决定返回格式：
        - 普通字段：找第一个锚点，返回字符串
        - 数组/表格字段：找所有锚点，返回数组

        Args:
            ocr_result: OCR识别结果
            rule: 提取规则，包含anchor_text、direction、max_distance等
            field_schema: 字段的schema定义，用于判断字段类型

        Returns:
            (提取值, 置信度, 来源页码)
        """
        # 支持前端字段名映射
        anchor_text = rule.get('anchor_text') or rule.get('anchorKeyword')
        if not anchor_text:
            raise ValueError("锚点提取规则缺少anchor_text或anchorKeyword字段")

        # 提取方向：right（右侧）、below（下方）、right_below（右下方）
        direction = rule.get('direction') or rule.get(
            'relativePosition', 'right')

        # 最大距离（字符数）
        max_distance = rule.get('max_distance') or rule.get('maxDistance', 200)

        # 最大字符数
        max_chars = rule.get('max_chars') or rule.get('maxDistance', 100)

        # 结束标记
        end_marker = rule.get('end_marker') or rule.get('endMarker')
        if end_marker:
            if end_marker == '\\n':
                end_marker = '\n'
            elif end_marker == '\\t':
                end_marker = '\t'

        # 是否使用正则匹配锚点
        anchor_regex = rule.get('anchor_regex', False)

        # 判断字段是否为数组类型
        is_array_field = False
        if field_schema:
            node_type = field_schema.get('nodeType', 'field')
            is_array_field = node_type in ('array', 'table')

        try:
            # 收集所有匹配的结果
            all_extracted_values = []
            all_confidences = []
            first_source_page = None

            # 在合并文本中查找所有锚点（适用于数组类型）
            merged_text = ocr_result.merged_text

            if is_array_field:
                # 数组类型：查找所有锚点位置
                if anchor_regex:
                    import re as regex_module
                    matches = list(regex_module.finditer(
                        anchor_text, merged_text))
                else:
                    # 查找所有锚点出现的位置
                    matches = []
                    start = 0
                    while True:
                        pos = merged_text.find(anchor_text, start)
                        if pos == -1:
                            break
                        # 创建一个类似match对象的结构

                        class MatchLike:
                            def __init__(self, start_pos, end_pos):
                                self._start = start_pos
                                self._end = end_pos

                            def start(self):
                                return self._start

                            def end(self):
                                return self._end
                        matches.append(MatchLike(pos, pos + len(anchor_text)))
                        start = pos + 1

                if not matches:
                    logger.warning(f"未找到锚点: {anchor_text}")
                    return None, 0.0, None

                # 对每个锚点位置提取右侧文本
                for match in matches:
                    anchor_end = match.end()

                    # 提取锚点右侧的文本
                    right_text = merged_text[anchor_end:anchor_end +
                                             max_distance].strip()

                    # 如果有结束标记，截取到结束标记
                    if end_marker and end_marker in right_text:
                        right_text = right_text[:right_text.index(
                            end_marker)].strip()

                    # 限制字符数
                    if len(right_text) > max_chars:
                        right_text = right_text[:max_chars]

                    # 清理文本
                    right_text = ' '.join(right_text.split())

                    if right_text:
                        all_extracted_values.append(right_text)
                        all_confidences.append(80.0)  # 默认置信度

                if not all_extracted_values:
                    return None, 0.0, None

                # 计算平均置信度
                avg_confidence = sum(all_confidences) / len(all_confidences)

                return all_extracted_values, avg_confidence, 1

            else:
                # 普通字段：只找第一个锚点
                if anchor_regex:
                    match = re.search(anchor_text, merged_text)
                    if not match:
                        logger.warning(f"未找到锚点: {anchor_text}")
                        return None, 0.0, None
                    anchor_end = match.end()
                else:
                    anchor_pos = merged_text.find(anchor_text)
                    if anchor_pos == -1:
                        logger.warning(f"未找到锚点: {anchor_text}")
                        return None, 0.0, None
                    anchor_end = anchor_pos + len(anchor_text)

                # 提取锚点右侧的文本
                right_text = merged_text[anchor_end:anchor_end +
                                         max_distance].strip()

                # 如果有结束标记，截取到结束标记
                if end_marker and end_marker in right_text:
                    right_text = right_text[:right_text.index(
                        end_marker)].strip()

                # 限制字符数
                if len(right_text) > max_chars:
                    right_text = right_text[:max_chars]

                # 清理文本
                right_text = ' '.join(right_text.split())

                if not right_text:
                    return None, 0.0, None

                return right_text, 80.0, 1

        except Exception as e:
            logger.error(f"锚点提取失败: {str(e)}")
            raise

    async def _extract_from_table(
        self,
        ocr_result: OCRResult,
        rule: Dict[str, Any],
        field_schema: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[Any], float, Optional[int]]:
        """
        表格提取函数

        检测表格并提取数据，支持跨页表格合并
        根据字段schema类型决定返回格式（数组字段返回数组）

        Args:
            ocr_result: OCR识别结果
            rule: 提取规则，包含table_header、column_name等
            field_schema: 字段的schema定义，用于判断字段类型

        Returns:
            (提取值, 置信度, 来源页码)
        """
        # 检测所有页面的表格
        all_tables = []

        for page_result in ocr_result.page_results:
            tables = await self._detect_tables(page_result)
            all_tables.extend(tables)

        if not all_tables:
            logger.warning("未检测到表格")
            return None, 0.0, None

        # 合并跨页表格
        merged_tables = await self._merge_cross_page_tables(all_tables)

        # 根据规则提取目标数据
        table_header = rule.get('table_header')
        column_name = rule.get('column_name')
        row_filter = rule.get('row_filter')

        if not column_name:
            raise ValueError("表格提取规则缺少column_name字段")

        # 查找目标表格
        target_table = None

        if table_header:
            # 根据表头查找表格
            for table in merged_tables:
                if table_header in table.get('header', []):
                    target_table = table
                    break
        else:
            # 使用第一个表格
            target_table = merged_tables[0] if merged_tables else None

        if not target_table:
            logger.warning(f"未找到包含表头 {table_header} 的表格")
            return None, 0.0, None

        # 提取列数据
        header = target_table.get('header', [])
        rows = target_table.get('rows', [])

        # 查找目标列索引
        column_index = None
        for i, col in enumerate(header):
            if column_name in col:
                column_index = i
                break

        if column_index is None:
            logger.warning(f"未找到列 {column_name}")
            return None, 0.0, None

        # 提取列值
        values = []
        for row in rows:
            if len(row) > column_index:
                cell_value = row[column_index]

                # 应用行过滤器
                if row_filter:
                    # 简单的键值对过滤
                    filter_column = row_filter.get('column')
                    filter_value = row_filter.get('value')

                    if filter_column and filter_value:
                        filter_index = None
                        for i, col in enumerate(header):
                            if filter_column in col:
                                filter_index = i
                                break

                        if filter_index is not None and len(row) > filter_index:
                            if filter_value not in row[filter_index]:
                                continue

                values.append(cell_value)

        if not values:
            return None, 0.0, None

        # 返回结果（如果只有一个值，返回字符串；否则返回列表）
        result_value = values[0] if len(values) == 1 else values

        # 计算置信度
        confidence = target_table.get('confidence', 0.8)
        source_page = target_table.get('page', None)

        return result_value, confidence, source_page

    async def _detect_tables(
        self,
        page_result: PageOCRResult
    ) -> List[Dict[str, Any]]:
        """
        检测单页中的表格

        通过分析文本框的位置关系，识别表格结构

        Args:
            page_result: 单页OCR结果

        Returns:
            表格列表，每个表格包含header、rows、page等信息
        """
        boxes = page_result.boxes

        if not boxes:
            return []

        # 按y坐标排序（从上到下）
        sorted_boxes = sorted(boxes, key=lambda b: b['box']['y'])

        # 检测行（y坐标相近的文本框为同一行）
        rows = []
        current_row = []
        current_y = None
        y_threshold = 10  # y坐标差异阈值

        for box in sorted_boxes:
            box_y = box['box']['y']

            if current_y is None:
                current_y = box_y
                current_row = [box]
            elif abs(box_y - current_y) <= y_threshold:
                # 同一行
                current_row.append(box)
            else:
                # 新行
                if current_row:
                    # 按x坐标排序
                    current_row.sort(key=lambda b: b['box']['x'])
                    rows.append(current_row)
                current_row = [box]
                current_y = box_y

        # 添加最后一行
        if current_row:
            current_row.sort(key=lambda b: b['box']['x'])
            rows.append(current_row)

        # 检测表格（连续的多列行）
        tables = []
        current_table_rows = []
        expected_columns = None

        for row in rows:
            num_columns = len(row)

            # 表格至少需要2列
            if num_columns < 2:
                # 结束当前表格
                if len(current_table_rows) >= 2:
                    tables.append(self._build_table_structure(
                        current_table_rows,
                        page_result.page_num
                    ))
                current_table_rows = []
                expected_columns = None
                continue

            # 检查列数是否一致
            if expected_columns is None:
                expected_columns = num_columns
                current_table_rows = [row]
            elif abs(num_columns - expected_columns) <= 1:
                # 允许列数有1的差异
                current_table_rows.append(row)
            else:
                # 列数差异过大，结束当前表格
                if len(current_table_rows) >= 2:
                    tables.append(self._build_table_structure(
                        current_table_rows,
                        page_result.page_num
                    ))
                current_table_rows = [row]
                expected_columns = num_columns

        # 添加最后一个表格
        if len(current_table_rows) >= 2:
            tables.append(self._build_table_structure(
                current_table_rows,
                page_result.page_num
            ))

        return tables

    def _build_table_structure(
        self,
        table_rows: List[List[Dict[str, Any]]],
        page_num: int
    ) -> Dict[str, Any]:
        """
        构建表格结构

        Args:
            table_rows: 表格行列表
            page_num: 页码

        Returns:
            表格结构字典
        """
        # 第一行作为表头
        header_row = table_rows[0]
        header = [box['text'] for box in header_row]

        # 其余行作为数据行
        data_rows = []
        confidences = []

        for row in table_rows[1:]:
            row_data = [box['text'] for box in row]
            data_rows.append(row_data)

            # 收集置信度
            for box in row:
                confidences.append(box.get('confidence', 0.0))

        # 计算平均置信度（OCR返回0-1，需要转换为0-100）
        avg_confidence = sum(confidences) / \
            len(confidences) if confidences else 0.0

        return {
            'header': header,
            'rows': data_rows,
            'page': page_num,
            'confidence': avg_confidence * 100,
            'row_count': len(data_rows),
            'column_count': len(header)
        }

    async def _merge_cross_page_tables(
        self,
        tables: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        合并跨页表格

        根据表头逻辑判断表格是否延续，去除重复的表头行

        Args:
            tables: 表格列表

        Returns:
            合并后的表格列表
        """
        if len(tables) <= 1:
            return tables

        merged_tables = []
        current_table = None

        for table in tables:
            if current_table is None:
                current_table = table
                continue

            # 检查表头是否相同（判断是否为跨页表格）
            if self._is_same_header(current_table['header'], table['header']):
                # 合并表格，去除重复表头
                current_table['rows'].extend(table['rows'])
                current_table['row_count'] += table['row_count']

                # 更新置信度（加权平均）
                total_rows = current_table['row_count']
                current_table['confidence'] = (
                    current_table['confidence'] * (total_rows - table['row_count']) +
                    table['confidence'] * table['row_count']
                ) / total_rows

                logger.info(
                    f"合并跨页表格: 页{current_table['page']}和页{table['page']}")
            else:
                # 不同的表格，保存当前表格并开始新表格
                merged_tables.append(current_table)
                current_table = table

        # 添加最后一个表格
        if current_table:
            merged_tables.append(current_table)

        return merged_tables

    def _is_same_header(
        self,
        header1: List[str],
        header2: List[str]
    ) -> bool:
        """
        判断两个表头是否相同

        Args:
            header1: 表头1
            header2: 表头2

        Returns:
            是否相同
        """
        if len(header1) != len(header2):
            return False

        # 检查每列是否相似（允许部分差异）
        match_count = 0
        for h1, h2 in zip(header1, header2):
            if h1 == h2 or h1 in h2 or h2 in h1:
                match_count += 1

        # 至少80%的列匹配
        return match_count >= len(header1) * 0.8

    def _calculate_confidence(
        self,
        ocr_result: OCRResult,
        extracted_value: str,
        source_page: Optional[int] = None
    ) -> float:
        """
        计算置信度（用于正则/锚点提取）

        根据OCR置信度、匹配度等因素综合计算
        返回0-100的置信度分数

        Args:
            ocr_result: OCR识别结果
            extracted_value: 提取的值
            source_page: 来源页码

        Returns:
            置信度分数（0-100）
        """
        if not extracted_value:
            return 0.0

        # 查找提取值对应的OCR文本框
        matching_boxes = []

        if source_page:
            # 在指定页面查找
            page_result = next(
                (p for p in ocr_result.page_results if p.page_num == source_page),
                None
            )
            if page_result:
                for box in page_result.boxes:
                    if extracted_value in box['text'] or box['text'] in extracted_value:
                        matching_boxes.append(box)
        else:
            # 在所有页面查找
            for page_result in ocr_result.page_results:
                for box in page_result.boxes:
                    if extracted_value in box['text'] or box['text'] in extracted_value:
                        matching_boxes.append(box)

        if not matching_boxes:
            # 未找到匹配的文本框，使用默认置信度
            return 60.0

        # 计算OCR置信度的平均值
        ocr_confidences = [box.get('confidence', 0.0)
                           for box in matching_boxes]
        avg_ocr_confidence = sum(ocr_confidences) / len(ocr_confidences)

        # 转换为0-100范围
        confidence_score = avg_ocr_confidence * 100

        # 根据匹配度调整置信度
        # 如果提取值完全匹配某个文本框，提高置信度
        exact_match = any(
            box['text'] == extracted_value for box in matching_boxes)
        if exact_match:
            confidence_score = min(confidence_score * 1.1, 100.0)

        # 如果提取值很短（可能不准确），降低置信度
        if len(extracted_value.strip()) < 3:
            confidence_score *= 0.9

        return round(confidence_score, 2)

    def _calculate_llm_confidence(
        self,
        ocr_result: OCRResult,
        field_value: Any,
        field_schema: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        计算LLM提取的置信度

        根据以下因素动态计算：
        1. 值是否为空
        2. 值是否在OCR文本中能找到
        3. 值的类型和复杂度
        4. 字段类型（普通字段/对象/数组）

        Args:
            ocr_result: OCR识别结果
            field_value: LLM提取的值
            field_schema: 字段的schema定义

        Returns:
            置信度分数（0-100）
        """
        # 基础置信度：LLM提取默认70%
        base_confidence = 70.0

        # 1. 空值检查
        if field_value is None:
            return 0.0

        if isinstance(field_value, str) and field_value.strip() == '':
            return 0.0

        if isinstance(field_value, (list, dict)) and len(field_value) == 0:
            return 0.0

        # 2. 根据字段类型调整
        node_type = field_schema.get(
            'nodeType', 'field') if field_schema else 'field'

        if node_type == 'field':
            # 普通字段：检查值是否在OCR文本中
            value_str = str(field_value)
            merged_text = ocr_result.merged_text

            if value_str in merged_text:
                # 完全匹配，高置信度
                base_confidence = 90.0
            elif self._fuzzy_match_in_text(value_str, merged_text):
                # 模糊匹配，中等置信度
                base_confidence = 75.0
            else:
                # 未找到匹配，可能是LLM推理的结果
                base_confidence = 60.0

            # 值长度调整
            if len(value_str.strip()) < 2:
                base_confidence *= 0.8  # 太短的值可能不准确
            elif len(value_str.strip()) > 100:
                base_confidence *= 0.9  # 太长的值可能包含噪音

        elif node_type == 'object':
            # 对象类型：检查子字段的填充率
            if isinstance(field_value, dict):
                total_fields = len(field_value)
                non_empty_fields = sum(1 for v in field_value.values()
                                       if v is not None and v != '')
                if total_fields > 0:
                    fill_rate = non_empty_fields / total_fields
                    base_confidence = 60.0 + (fill_rate * 30.0)  # 60-90%
                else:
                    base_confidence = 50.0
            else:
                base_confidence = 40.0  # 类型不匹配

        elif node_type in ('array', 'table'):
            # 数组类型：检查元素数量和内容
            if isinstance(field_value, list):
                if len(field_value) == 0:
                    return 0.0
                elif len(field_value) == 1:
                    base_confidence = 65.0  # 只有一个元素，可能不完整
                else:
                    base_confidence = 75.0  # 多个元素，较可信

                # 检查数组元素是否在OCR文本中
                merged_text = ocr_result.merged_text
                match_count = 0
                for item in field_value:
                    item_str = str(item) if not isinstance(item, dict) else str(
                        list(item.values())[0]) if item else ''
                    if item_str and item_str in merged_text:
                        match_count += 1

                if len(field_value) > 0:
                    match_rate = match_count / len(field_value)
                    base_confidence += match_rate * 15.0  # 最多+15%
            else:
                base_confidence = 40.0  # 类型不匹配

        return round(min(base_confidence, 100.0), 1)

    def _fuzzy_match_in_text(self, value: str, text: str, threshold: float = 0.8) -> bool:
        """
        模糊匹配检查值是否在文本中

        Args:
            value: 要查找的值
            text: 文本内容
            threshold: 匹配阈值

        Returns:
            是否找到模糊匹配
        """
        if not value or not text:
            return False

        value = value.strip().lower()
        text = text.lower()

        # 直接包含
        if value in text:
            return True

        # 去除空格后匹配
        value_no_space = value.replace(' ', '').replace('\n', '')
        text_no_space = text.replace(' ', '').replace('\n', '')
        if value_no_space in text_no_space:
            return True

        # 检查值的主要部分是否在文本中（至少80%的字符匹配）
        if len(value) > 5:
            match_chars = sum(1 for c in value if c in text)
            if match_chars / len(value) >= threshold:
                return True

        return False

    def _find_text_page(
        self,
        ocr_result: OCRResult,
        text: str
    ) -> Optional[int]:
        """
        查找文本所在的页码

        Args:
            ocr_result: OCR识别结果
            text: 要查找的文本

        Returns:
            页码（从1开始），如果未找到返回None
        """
        for page_result in ocr_result.page_results:
            if text in page_result.text:
                return page_result.page_num

        return None

    async def _extract_with_llm(
        self,
        ocr_result: OCRResult,
        rule: Dict[str, Any],
        field_name: str,
        field_schema: Dict[str, Any]
    ) -> Tuple[Optional[str], float, Optional[int]]:
        """
        使用LLM进行智能提取

        Args:
            ocr_result: OCR识别结果
            rule: 提取规则，包含prompt_template、context_scope等
            field_name: 字段名
            field_schema: 字段schema定义

        Returns:
            (提取值, 置信度, 来源页码)
        """
        try:
            # 导入LLM服务
            from app.services.llm_service import llm_service, AGENTLY_AVAILABLE

            if not AGENTLY_AVAILABLE:
                logger.warning("Agently未安装，LLM提取功能不可用")
                return None, 0.0, None

            # 转换OCR结果为字典格式（LLM服务期望的格式）
            ocr_result_dict = {
                'merged_text': ocr_result.merged_text,
                'page_results': [
                    {
                        'text': page.text,
                        'page_num': page.page_num,
                        'confidence': page.confidence,
                        'blocks': page.boxes
                    }
                    for page in ocr_result.page_results
                ]
            }

            # 转换提取规则格式（前端字段名 -> 后端字段名）
            extraction_rule = {
                'context_scope': rule.get('contextScope', 'all_pages'),
                'n_pages': rule.get('pageCount', 3),
                'prompt': rule.get('promptTemplate', ''),
                'output_schema': {
                    'value': ('String', f'提取的{field_name}字段值'),
                    'confidence': ('Float', '置信度分数，范围0-1'),
                    'explanation': ('String', '提取依据说明')
                }
            }

            # 调用LLM服务
            result = await llm_service.extract_by_llm(
                ocr_result_dict,
                field_name,
                extraction_rule
            )

            if not result:
                logger.warning(f"LLM提取返回空结果: {field_name}")
                return None, 0.0, None

            # 提取结果
            value = result.get('value')
            confidence = result.get('confidence', 50.0)  # 0-100
            explanation = result.get('explanation', '')

            logger.info(
                f"LLM提取成功: {field_name}={value}, 置信度={confidence}%, 说明={explanation}")

            # 查找来源页码
            source_page = self._find_text_page(
                ocr_result, str(value)) if value else None

            return value, confidence, source_page

        except Exception as e:
            logger.error(f"LLM提取失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, 0.0, None


# 便捷函数
async def create_extraction_service() -> ExtractionService:
    """
    创建数据提取服务实例

    Returns:
        数据提取服务实例
    """
    return ExtractionService()
