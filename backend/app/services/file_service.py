"""
文件上传服务

提供MinIO对象存储的文件上传、下载、删除功能
"""
import os
from datetime import datetime, timedelta
from typing import BinaryIO, Optional
from minio import Minio
from minio.error import S3Error
import io

from app.core.config import settings
from app.core.logger import logger


class FileService:
    """文件存储服务类"""
    
    def __init__(self):
        """初始化MinIO客户端"""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在，不存在则创建"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"创建MinIO存储桶: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"检查/创建存储桶失败: {str(e)}")
            raise
    
    def generate_file_path(self, task_id: str, filename: str) -> str:
        """
        生成文件存储路径
        
        路径格式: {bucket}/{year}/{month}/{day}/{task_id}/{filename}
        例如: idp-files/2025/12/14/T_20251214_0001/invoice.pdf
        
        Args:
            task_id: 任务ID
            filename: 原始文件名
            
        Returns:
            str: 文件存储路径（不包含bucket名称）
        """
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        
        # 构建路径
        file_path = f"{year}/{month}/{day}/{task_id}/{filename}"
        return file_path
    
    async def upload_to_storage(
        self,
        file_content: bytes,
        task_id: str,
        filename: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        上传文件到MinIO对象存储
        
        Args:
            file_content: 文件二进制内容
            task_id: 任务ID
            filename: 文件名
            content_type: 文件MIME类型
            
        Returns:
            str: 文件存储路径
            
        Raises:
            S3Error: MinIO操作失败
        """
        try:
            # 生成存储路径
            file_path = self.generate_file_path(task_id, filename)
            
            # 将bytes转换为BytesIO对象
            file_data = io.BytesIO(file_content)
            file_size = len(file_content)
            
            # 上传文件
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
                data=file_data,
                length=file_size,
                content_type=content_type
            )
            
            logger.info(f"文件上传成功: {file_path}, 大小: {file_size} bytes")
            return file_path
            
        except S3Error as e:
            logger.error(f"文件上传失败: {str(e)}")
            raise
    
    async def upload_file_stream(
        self,
        file: BinaryIO,
        task_id: str,
        filename: str,
        file_size: int,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        流式上传文件到MinIO（适用于大文件）
        
        Args:
            file: 文件对象
            task_id: 任务ID
            filename: 文件名
            file_size: 文件大小（字节）
            content_type: 文件MIME类型
            
        Returns:
            str: 文件存储路径
            
        Raises:
            S3Error: MinIO操作失败
        """
        try:
            # 生成存储路径
            file_path = self.generate_file_path(task_id, filename)
            
            # 重置文件指针
            file.seek(0)
            
            # 流式上传
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
                data=file,
                length=file_size,
                content_type=content_type
            )
            
            logger.info(f"文件流式上传成功: {file_path}, 大小: {file_size} bytes")
            return file_path
            
        except S3Error as e:
            logger.error(f"文件流式上传失败: {str(e)}")
            raise
    
    async def download_from_storage(self, file_path: str) -> bytes:
        """
        从MinIO下载文件
        
        Args:
            file_path: 文件存储路径
            
        Returns:
            bytes: 文件二进制内容
            
        Raises:
            S3Error: MinIO操作失败
        """
        try:
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=file_path
            )
            
            # 读取所有数据
            file_content = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"文件下载成功: {file_path}, 大小: {len(file_content)} bytes")
            return file_content
            
        except S3Error as e:
            logger.error(f"文件下载失败: {file_path}, 错误: {str(e)}")
            raise
    
    async def download_to_file(self, file_path: str, local_path: str) -> str:
        """
        从MinIO下载文件到本地路径
        
        Args:
            file_path: MinIO中的文件路径
            local_path: 本地保存路径
            
        Returns:
            str: 本地文件路径
            
        Raises:
            S3Error: MinIO操作失败
        """
        try:
            # 确保本地目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # 下载文件
            self.client.fget_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
                file_path=local_path
            )
            
            logger.info(f"文件下载到本地: {file_path} -> {local_path}")
            return local_path
            
        except S3Error as e:
            logger.error(f"文件下载到本地失败: {file_path}, 错误: {str(e)}")
            raise
    
    async def delete_from_storage(self, file_path: str) -> bool:
        """
        从MinIO删除文件
        
        Args:
            file_path: 文件存储路径
            
        Returns:
            bool: 删除是否成功
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=file_path
            )
            
            logger.info(f"文件删除成功: {file_path}")
            return True
            
        except S3Error as e:
            logger.error(f"文件删除失败: {file_path}, 错误: {str(e)}")
            return False
    
    def generate_presigned_url(
        self,
        file_path: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        生成预签名URL（临时访问链接）
        
        Args:
            file_path: 文件存储路径
            expires: 有效期（默认1小时）
            
        Returns:
            str: 预签名URL
            
        Raises:
            S3Error: MinIO操作失败
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
                expires=expires
            )
            
            logger.info(f"生成预签名URL: {file_path}, 有效期: {expires}")
            return url
            
        except S3Error as e:
            logger.error(f"生成预签名URL失败: {file_path}, 错误: {str(e)}")
            raise
    
    def file_exists(self, file_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件存储路径
            
        Returns:
            bool: 文件是否存在
        """
        try:
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=file_path
            )
            return True
        except S3Error:
            return False
    
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """
        获取文件信息
        
        Args:
            file_path: 文件存储路径
            
        Returns:
            Optional[dict]: 文件信息字典，包含size、last_modified等
        """
        try:
            stat = self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=file_path
            )
            
            return {
                "size": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "content_type": stat.content_type
            }
        except S3Error as e:
            logger.error(f"获取文件信息失败: {file_path}, 错误: {str(e)}")
            return None


# 创建全局实例
file_service = FileService()
