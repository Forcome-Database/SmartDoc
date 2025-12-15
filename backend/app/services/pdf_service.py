"""
PDF处理服务

提供PDF页数获取、PDF转图片等功能
"""
import os
import tempfile
from typing import List, Optional
from pathlib import Path
import PyPDF2
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image

from app.core.logger import logger


class PDFService:
    """PDF处理服务类"""
    
    def __init__(self):
        """初始化PDF服务"""
        self.default_dpi = 300
        self.default_format = "PNG"
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        获取PDF文件的页数
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            int: PDF页数
            
        Raises:
            FileNotFoundError: 文件不存在
            Exception: PDF读取失败
        """
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
            
            logger.info(f"PDF页数: {page_count}, 文件: {pdf_path}")
            return page_count
            
        except Exception as e:
            logger.error(f"获取PDF页数失败: {pdf_path}, 错误: {str(e)}")
            raise
    
    def get_page_count_from_bytes(self, pdf_content: bytes) -> int:
        """
        从字节内容获取PDF页数
        
        Args:
            pdf_content: PDF文件二进制内容
            
        Returns:
            int: PDF页数
            
        Raises:
            Exception: PDF读取失败
        """
        try:
            import io
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            page_count = len(pdf_reader.pages)
            
            logger.info(f"PDF页数: {page_count}")
            return page_count
            
        except Exception as e:
            logger.error(f"从字节内容获取PDF页数失败: {str(e)}")
            raise
    
    async def convert_pdf_to_images(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None,
        dpi: int = 300,
        fmt: str = "PNG",
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> List[str]:
        """
        将PDF转换为图片
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录（如果为None，使用临时目录）
            dpi: 图片分辨率（默认300）
            fmt: 输出格式（默认PNG）
            first_page: 起始页码（从1开始，None表示第一页）
            last_page: 结束页码（None表示最后一页）
            
        Returns:
            List[str]: 生成的图片文件路径列表
            
        Raises:
            FileNotFoundError: PDF文件不存在
            Exception: 转换失败
        """
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
            
            # 如果未指定输出目录，使用临时目录
            if output_dir is None:
                output_dir = tempfile.mkdtemp(prefix="pdf_images_")
            else:
                os.makedirs(output_dir, exist_ok=True)
            
            logger.info(f"开始转换PDF为图片: {pdf_path}, DPI: {dpi}, 格式: {fmt}")
            
            # 转换PDF为图片
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                fmt=fmt.lower(),
                first_page=first_page,
                last_page=last_page
            )
            
            # 保存图片
            image_paths = []
            for i, image in enumerate(images, start=1):
                # 计算实际页码
                page_num = (first_page or 1) + i - 1
                image_filename = f"page_{page_num}.{fmt.lower()}"
                image_path = os.path.join(output_dir, image_filename)
                
                image.save(image_path, fmt)
                image_paths.append(image_path)
                
                logger.debug(f"保存图片: {image_path}")
            
            logger.info(f"PDF转图片完成: 共{len(image_paths)}页")
            return image_paths
            
        except Exception as e:
            logger.error(f"PDF转图片失败: {pdf_path}, 错误: {str(e)}")
            raise
    
    async def convert_pdf_bytes_to_images(
        self,
        pdf_content: bytes,
        output_dir: Optional[str] = None,
        dpi: int = 300,
        fmt: str = "PNG",
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> List[str]:
        """
        将PDF字节内容转换为图片
        
        Args:
            pdf_content: PDF文件二进制内容
            output_dir: 输出目录（如果为None，使用临时目录）
            dpi: 图片分辨率（默认300）
            fmt: 输出格式（默认PNG）
            first_page: 起始页码（从1开始，None表示第一页）
            last_page: 结束页码（None表示最后一页）
            
        Returns:
            List[str]: 生成的图片文件路径列表
            
        Raises:
            Exception: 转换失败
        """
        try:
            # 如果未指定输出目录，使用临时目录
            if output_dir is None:
                output_dir = tempfile.mkdtemp(prefix="pdf_images_")
            else:
                os.makedirs(output_dir, exist_ok=True)
            
            logger.info(f"开始从字节内容转换PDF为图片, DPI: {dpi}, 格式: {fmt}")
            
            # 转换PDF为图片
            images = convert_from_bytes(
                pdf_content,
                dpi=dpi,
                fmt=fmt.lower(),
                first_page=first_page,
                last_page=last_page
            )
            
            # 保存图片
            image_paths = []
            for i, image in enumerate(images, start=1):
                # 计算实际页码
                page_num = (first_page or 1) + i - 1
                image_filename = f"page_{page_num}.{fmt.lower()}"
                image_path = os.path.join(output_dir, image_filename)
                
                image.save(image_path, fmt)
                image_paths.append(image_path)
                
                logger.debug(f"保存图片: {image_path}")
            
            logger.info(f"PDF转图片完成: 共{len(image_paths)}页")
            return image_paths
            
        except Exception as e:
            logger.error(f"从字节内容转换PDF为图片失败: {str(e)}")
            raise
    
    async def convert_single_page_to_image(
        self,
        pdf_path: str,
        page_number: int,
        output_path: Optional[str] = None,
        dpi: int = 300,
        fmt: str = "PNG"
    ) -> str:
        """
        将PDF的单个页面转换为图片
        
        Args:
            pdf_path: PDF文件路径
            page_number: 页码（从1开始）
            output_path: 输出文件路径（如果为None，使用临时文件）
            dpi: 图片分辨率（默认300）
            fmt: 输出格式（默认PNG）
            
        Returns:
            str: 生成的图片文件路径
            
        Raises:
            FileNotFoundError: PDF文件不存在
            Exception: 转换失败
        """
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
            
            # 如果未指定输出路径，使用临时文件
            if output_path is None:
                temp_dir = tempfile.mkdtemp(prefix="pdf_page_")
                output_path = os.path.join(temp_dir, f"page_{page_number}.{fmt.lower()}")
            else:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            logger.info(f"转换PDF单页为图片: {pdf_path}, 页码: {page_number}")
            
            # 转换单页
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                fmt=fmt.lower(),
                first_page=page_number,
                last_page=page_number
            )
            
            if not images:
                raise Exception(f"无法转换页码 {page_number}")
            
            # 保存图片
            images[0].save(output_path, fmt)
            
            logger.info(f"单页转换完成: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"转换PDF单页失败: {pdf_path}, 页码: {page_number}, 错误: {str(e)}")
            raise
    
    def cleanup_temp_files(self, file_paths: List[str]) -> int:
        """
        清理临时文件
        
        Args:
            file_paths: 要删除的文件路径列表
            
        Returns:
            int: 成功删除的文件数量
        """
        deleted_count = 0
        
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_count += 1
                    logger.debug(f"删除临时文件: {file_path}")
            except Exception as e:
                logger.warning(f"删除临时文件失败: {file_path}, 错误: {str(e)}")
        
        logger.info(f"清理临时文件完成: 删除 {deleted_count}/{len(file_paths)} 个文件")
        return deleted_count
    
    def cleanup_temp_directory(self, directory: str) -> bool:
        """
        清理临时目录及其所有内容
        
        Args:
            directory: 要删除的目录路径
            
        Returns:
            bool: 是否成功删除
        """
        try:
            if os.path.exists(directory):
                import shutil
                shutil.rmtree(directory)
                logger.info(f"删除临时目录: {directory}")
                return True
            return False
        except Exception as e:
            logger.warning(f"删除临时目录失败: {directory}, 错误: {str(e)}")
            return False
    
    def is_pdf_file(self, file_path: str) -> bool:
        """
        检查文件是否为PDF格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否为PDF文件
        """
        try:
            with open(file_path, 'rb') as file:
                # 检查PDF文件头
                header = file.read(4)
                return header == b'%PDF'
        except Exception:
            return False
    
    def validate_pdf(self, pdf_path: str) -> dict:
        """
        验证PDF文件的有效性
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            dict: 验证结果，包含is_valid、page_count、error等信息
        """
        result = {
            "is_valid": False,
            "page_count": 0,
            "error": None
        }
        
        try:
            if not os.path.exists(pdf_path):
                result["error"] = "文件不存在"
                return result
            
            if not self.is_pdf_file(pdf_path):
                result["error"] = "不是有效的PDF文件"
                return result
            
            # 尝试读取PDF
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                if page_count == 0:
                    result["error"] = "PDF文件为空"
                    return result
                
                result["is_valid"] = True
                result["page_count"] = page_count
            
            logger.info(f"PDF验证通过: {pdf_path}, 页数: {page_count}")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"PDF验证失败: {pdf_path}, 错误: {str(e)}")
        
        return result


# 创建全局实例
pdf_service = PDFService()
