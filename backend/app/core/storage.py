"""
MinIO对象存储管理模块
提供文件上传、下载、删除和预签名URL生成功能
"""
from minio import Minio
from minio.error import S3Error
from typing import Optional, BinaryIO
from datetime import timedelta, datetime
import logging
import io
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO客户端封装类"""
    
    def __init__(self):
        self._client: Optional[Minio] = None
        self._bucket = settings.MINIO_BUCKET
    
    def connect(self):
        """建立MinIO连接"""
        if self._client is None:
            self._client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            
            # 确保bucket存在
            self._ensure_bucket_exists()
            
            logger.info(f"MinIO连接已建立，bucket: {self._bucket}")
    
    def _ensure_bucket_exists(self):
        """确保bucket存在，不存在则创建"""
        try:
            if not self._client.bucket_exists(self._bucket):
                self._client.make_bucket(self._bucket)
                logger.info(f"Bucket已创建: {self._bucket}")
            else:
                logger.info(f"Bucket已存在: {self._bucket}")
        except S3Error as e:
            logger.error(f"检查/创建bucket失败: {str(e)}")
            raise
    
    def upload_file(
        self,
        file_data: BinaryIO,
        object_name: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None
    ) -> str:
        """
        上传文件到MinIO
        
        Args:
            file_data: 文件数据流
            object_name: 对象名称（存储路径）
            content_type: 文件MIME类型
            metadata: 文件元数据
            
        Returns:
            对象的完整路径
        """
        try:
            if not self._client:
                self.connect()
            
            # 获取文件大小
            file_data.seek(0, 2)  # 移动到文件末尾
            file_size = file_data.tell()
            file_data.seek(0)  # 重置到文件开头
            
            # 上传文件
            self._client.put_object(
                bucket_name=self._bucket,
                object_name=object_name,
                data=file_data,
                length=file_size,
                content_type=content_type,
                metadata=metadata,
            )
            
            logger.info(f"文件上传成功: {object_name} ({file_size} bytes)")
            return f"{self._bucket}/{object_name}"
            
        except S3Error as e:
            logger.error(f"文件上传失败 [{object_name}]: {str(e)}")
            raise
    
    def download_file(self, object_name: str) -> bytes:
        """
        从MinIO下载文件
        
        Args:
            object_name: 对象名称（存储路径）
            
        Returns:
            文件内容（字节）
        """
        try:
            if not self._client:
                self.connect()
            
            response = self._client.get_object(
                bucket_name=self._bucket,
                object_name=object_name,
            )
            
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"文件下载成功: {object_name} ({len(data)} bytes)")
            return data
            
        except S3Error as e:
            logger.error(f"文件下载失败 [{object_name}]: {str(e)}")
            raise
    
    def download_file_to_path(self, object_name: str, file_path: str):
        """
        从MinIO下载文件到本地路径
        
        Args:
            object_name: 对象名称（存储路径）
            file_path: 本地文件路径
        """
        try:
            if not self._client:
                self.connect()
            
            self._client.fget_object(
                bucket_name=self._bucket,
                object_name=object_name,
                file_path=file_path,
            )
            
            logger.info(f"文件下载到本地: {object_name} -> {file_path}")
            
        except S3Error as e:
            logger.error(f"文件下载失败 [{object_name}]: {str(e)}")
            raise
    
    def delete_file(self, object_name: str) -> bool:
        """
        从MinIO删除文件
        
        Args:
            object_name: 对象名称（存储路径）
            
        Returns:
            是否删除成功
        """
        try:
            if not self._client:
                self.connect()
            
            self._client.remove_object(
                bucket_name=self._bucket,
                object_name=object_name,
            )
            
            logger.info(f"文件删除成功: {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"文件删除失败 [{object_name}]: {str(e)}")
            return False
    
    def generate_presigned_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        生成预签名URL
        
        Args:
            object_name: 对象名称（存储路径）
            expires: 有效期（默认1小时）
            
        Returns:
            预签名URL
        """
        try:
            if not self._client:
                self.connect()
            
            url = self._client.presigned_get_object(
                bucket_name=self._bucket,
                object_name=object_name,
                expires=expires,
            )
            
            logger.info(f"预签名URL生成成功: {object_name}")
            return url
            
        except S3Error as e:
            logger.error(f"预签名URL生成失败 [{object_name}]: {str(e)}")
            raise
    
    def file_exists(self, object_name: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            object_name: 对象名称（存储路径）
            
        Returns:
            文件是否存在
        """
        try:
            if not self._client:
                self.connect()
            
            self._client.stat_object(
                bucket_name=self._bucket,
                object_name=object_name,
            )
            return True
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            logger.error(f"检查文件存在失败 [{object_name}]: {str(e)}")
            return False
    
    def get_file_info(self, object_name: str) -> Optional[dict]:
        """
        获取文件信息
        
        Args:
            object_name: 对象名称（存储路径）
            
        Returns:
            文件信息字典
        """
        try:
            if not self._client:
                self.connect()
            
            stat = self._client.stat_object(
                bucket_name=self._bucket,
                object_name=object_name,
            )
            
            return {
                "size": stat.size,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified,
                "metadata": stat.metadata,
            }
            
        except S3Error as e:
            logger.error(f"获取文件信息失败 [{object_name}]: {str(e)}")
            return None
    
    def list_objects(self, prefix: str = "", recursive: bool = False) -> list:
        """
        列出对象
        
        Args:
            prefix: 对象名称前缀
            recursive: 是否递归列出
            
        Returns:
            对象列表
        """
        try:
            if not self._client:
                self.connect()
            
            objects = self._client.list_objects(
                bucket_name=self._bucket,
                prefix=prefix,
                recursive=recursive,
            )
            
            return [
                {
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                }
                for obj in objects
            ]
            
        except S3Error as e:
            logger.error(f"列出对象失败 [prefix={prefix}]: {str(e)}")
            return []
    
    @staticmethod
    def generate_object_path(task_id: str, filename: str) -> str:
        """
        生成对象存储路径
        格式: {year}/{month}/{day}/{task_id}/{filename}
        
        Args:
            task_id: 任务ID
            filename: 文件名
            
        Returns:
            对象路径
        """
        now = datetime.now()
        return f"{now.year}/{now.month:02d}/{now.day:02d}/{task_id}/{filename}"


# 创建全局MinIO客户端实例
minio_client = MinIOClient()


def get_minio() -> MinIOClient:
    """
    获取MinIO客户端实例（依赖注入）
    
    Returns:
        MinIOClient实例
    """
    if not minio_client._client:
        minio_client.connect()
    return minio_client
