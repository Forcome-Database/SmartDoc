"""
文件哈希服务

提供文件SHA256哈希计算、Task Key生成和去重判断功能
"""
import hashlib
from typing import Optional, BinaryIO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.task import Task, TaskStatus


class HashService:
    """文件哈希服务类"""
    
    @staticmethod
    def calculate_file_hash(file_content: bytes) -> str:
        """
        计算文件的SHA256哈希值
        
        Args:
            file_content: 文件二进制内容
            
        Returns:
            str: 64位十六进制哈希字符串
        """
        sha256_hash = hashlib.sha256()
        sha256_hash.update(file_content)
        return sha256_hash.hexdigest()
    
    @staticmethod
    async def calculate_file_hash_stream(file: BinaryIO, chunk_size: int = 8192) -> str:
        """
        流式计算文件的SHA256哈希值（适用于大文件）
        
        Args:
            file: 文件对象
            chunk_size: 每次读取的块大小（默认8KB）
            
        Returns:
            str: 64位十六进制哈希字符串
        """
        sha256_hash = hashlib.sha256()
        
        # 重置文件指针到开始位置
        file.seek(0)
        
        # 分块读取并计算哈希
        while chunk := file.read(chunk_size):
            sha256_hash.update(chunk)
        
        # 重置文件指针以便后续使用
        file.seek(0)
        
        return sha256_hash.hexdigest()
    
    @staticmethod
    def generate_task_key(file_hash: str, rule_id: str, rule_version: str) -> str:
        """
        生成任务唯一标识Key
        
        Task Key = file_hash + rule_id + rule_version
        用于去重判断，相同文件+相同规则+相同版本 = 相同任务
        
        Args:
            file_hash: 文件SHA256哈希值
            rule_id: 规则ID
            rule_version: 规则版本号
            
        Returns:
            str: 任务唯一标识Key
        """
        return f"{file_hash}_{rule_id}_{rule_version}"
    
    @staticmethod
    async def check_duplicate(
        db: AsyncSession,
        file_hash: str,
        rule_id: str,
        rule_version: str
    ) -> Optional[Task]:
        """
        检查是否存在重复任务（去重判断）
        
        查询数据库中是否存在相同的file_hash + rule_id + rule_version组合，
        且任务状态为已完成（COMPLETED或PUSH_SUCCESS）的记录。
        如果存在，则可以直接复用历史结果（秒传）。
        
        Args:
            db: 数据库会话
            file_hash: 文件SHA256哈希值
            rule_id: 规则ID
            rule_version: 规则版本号
            
        Returns:
            Optional[Task]: 如果找到已完成的重复任务，返回该任务对象；否则返回None
        """
        from sqlalchemy import or_
        
        # 查询相同file_hash、rule_id、rule_version且状态为已完成的任务
        # 包括 COMPLETED（处理完成）和 PUSH_SUCCESS（推送成功）两种状态
        # 使用 limit(1) 获取最新的一条记录，避免多条记录导致的错误
        stmt = select(Task).where(
            Task.file_hash == file_hash,
            Task.rule_id == rule_id,
            Task.rule_version == rule_version,
            or_(
                Task.status == TaskStatus.COMPLETED,
                Task.status == TaskStatus.PUSH_SUCCESS
            )
        ).order_by(Task.created_at.desc()).limit(1)
        
        result = await db.execute(stmt)
        existing_task = result.scalar_one_or_none()
        
        return existing_task


# 创建全局实例
hash_service = HashService()
