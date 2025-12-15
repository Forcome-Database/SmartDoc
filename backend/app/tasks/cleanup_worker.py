"""
定时清理Worker

每日凌晨02:00执行定时清理任务，删除超过留存期的文件
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.logger import logger
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.task import Task, TaskStatus
from app.models.system_config import SystemConfig
from app.services.file_service import file_service


class CleanupWorker:
    """定时清理Worker类"""
    
    def __init__(self):
        """初始化Worker"""
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
        logger.info("清理Worker初始化完成")
    
    async def start(self):
        """启动Worker，配置定时任务"""
        if self.is_running:
            logger.warning("清理Worker已在运行中")
            return
        
        self.is_running = True
        logger.info("清理Worker启动中...")
        
        try:
            # 配置定时任务：每日凌晨02:00执行
            self.scheduler.add_job(
                self.execute_cleanup,
                trigger=CronTrigger(hour=2, minute=0),
                id='daily_cleanup',
                name='每日文件清理任务',
                replace_existing=True
            )
            
            # 启动调度器
            self.scheduler.start()
            
            logger.info("清理Worker已启动，定时任务已配置（每日02:00执行）")
            
            # 保持运行
            while self.is_running:
                await asyncio.sleep(60)  # 每分钟检查一次
                
        except Exception as e:
            logger.error(f"清理Worker运行失败: {str(e)}")
            self.is_running = False
            raise
    
    async def stop(self):
        """停止Worker"""
        self.is_running = False
        if self.scheduler.running:
            self.scheduler.shutdown()
        logger.info("清理Worker已停止")
    
    async def execute_cleanup(self):
        """
        执行清理任务
        
        清理逻辑：
        1. 从系统配置中获取文件留存期
        2. 查询超过留存期的任务
        3. 仅删除Completed或Rejected状态的任务文件
        4. 从MinIO删除文件
        5. 更新数据库记录
        6. 记录清理日志
        """
        logger.info("=" * 60)
        logger.info("开始执行定时清理任务")
        logger.info("=" * 60)
        
        start_time = datetime.utcnow()
        
        async with SessionLocal() as db:
            try:
                # 1. 获取文件留存期配置
                retention_days = await self._get_retention_days(db)
                logger.info(f"文件留存期配置: {retention_days} 天")
                
                # 2. 计算截止日期
                cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
                logger.info(f"清理截止日期: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 3. 查询需要清理的任务
                tasks_to_cleanup = await self._find_tasks_to_cleanup(db, cutoff_date)
                
                if not tasks_to_cleanup:
                    logger.info("没有需要清理的文件")
                    return
                
                logger.info(f"找到 {len(tasks_to_cleanup)} 个任务需要清理")
                
                # 4. 执行清理
                cleanup_stats = await self._cleanup_files(tasks_to_cleanup)
                
                # 5. 记录清理日志
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                
                await self._log_cleanup_result(
                    db=db,
                    stats=cleanup_stats,
                    duration=duration
                )
                
                logger.info("=" * 60)
                logger.info(
                    f"清理任务完成: "
                    f"删除文件数={cleanup_stats['deleted_count']}, "
                    f"失败数={cleanup_stats['failed_count']}, "
                    f"释放空间={self._format_size(cleanup_stats['freed_space'])}, "
                    f"耗时={duration:.2f}秒"
                )
                logger.info("=" * 60)
                
            except Exception as e:
                logger.error(f"清理任务执行失败: {str(e)}", exc_info=True)
                # 发送通知给管理员（如果配置了通知服务）
                await self._notify_admin_on_failure(str(e))
    
    async def _get_retention_days(self, db: AsyncSession) -> int:
        """
        从系统配置中获取文件留存期
        
        Args:
            db: 数据库会话
            
        Returns:
            int: 留存天数，默认30天
        """
        try:
            stmt = select(SystemConfig).where(
                SystemConfig.key == 'file_retention_days'
            )
            result = await db.execute(stmt)
            config = result.scalar_one_or_none()
            
            if config and config.value:
                # value是JSON类型，可能是数字或包含数字的字典
                if isinstance(config.value, dict):
                    return int(config.value.get('days', 30))
                else:
                    return int(config.value)
            
            # 默认30天
            return 30
            
        except Exception as e:
            logger.error(f"获取留存期配置失败: {str(e)}")
            # 返回默认值
            return 30
    
    async def _find_tasks_to_cleanup(
        self,
        db: AsyncSession,
        cutoff_date: datetime
    ) -> List[Task]:
        """
        查询需要清理的任务
        
        条件：
        1. 创建时间早于截止日期
        2. 状态为Completed或Rejected
        3. 文件路径不为空
        
        Args:
            db: 数据库会话
            cutoff_date: 截止日期
            
        Returns:
            List[Task]: 需要清理的任务列表
        """
        try:
            stmt = select(Task).where(
                and_(
                    Task.created_at < cutoff_date,
                    Task.status.in_([TaskStatus.COMPLETED, TaskStatus.REJECTED]),
                    Task.file_path.isnot(None),
                    Task.file_path != ''
                )
            )
            
            result = await db.execute(stmt)
            tasks = result.scalars().all()
            
            return list(tasks)
            
        except Exception as e:
            logger.error(f"查询待清理任务失败: {str(e)}")
            return []
    
    async def _cleanup_files(self, tasks: List[Task]) -> Dict[str, Any]:
        """
        清理文件
        
        Args:
            tasks: 需要清理的任务列表
            
        Returns:
            Dict[str, Any]: 清理统计信息
        """
        deleted_count = 0
        failed_count = 0
        freed_space = 0
        
        for task in tasks:
            try:
                # 获取文件信息（用于统计释放空间）
                file_info = file_service.get_file_info(task.file_path)
                file_size = file_info.get('size', 0) if file_info else 0
                
                # 从MinIO删除文件
                success = await file_service.delete_from_storage(task.file_path)
                
                if success:
                    deleted_count += 1
                    freed_space += file_size
                    
                    logger.info(
                        f"文件已删除: {task.file_path} "
                        f"(任务ID: {task.id}, 大小: {self._format_size(file_size)})"
                    )
                else:
                    failed_count += 1
                    logger.warning(f"文件删除失败: {task.file_path} (任务ID: {task.id})")
                
            except Exception as e:
                failed_count += 1
                logger.error(
                    f"清理文件异常: {task.file_path} (任务ID: {task.id}), "
                    f"错误: {str(e)}"
                )
        
        return {
            'deleted_count': deleted_count,
            'failed_count': failed_count,
            'freed_space': freed_space,
            'total_count': len(tasks)
        }
    
    async def _log_cleanup_result(
        self,
        db: AsyncSession,
        stats: Dict[str, Any],
        duration: float
    ):
        """
        记录清理结果到日志
        
        Args:
            db: 数据库会话
            stats: 清理统计信息
            duration: 执行耗时（秒）
        """
        try:
            log_message = (
                f"定时清理任务执行完成 - "
                f"删除文件数: {stats['deleted_count']}, "
                f"失败数: {stats['failed_count']}, "
                f"总数: {stats['total_count']}, "
                f"释放空间: {self._format_size(stats['freed_space'])}, "
                f"耗时: {duration:.2f}秒"
            )
            
            logger.info(log_message)
            
            # 可以选择将清理日志保存到数据库的audit_logs表
            # 这里暂时只记录到日志文件
            
        except Exception as e:
            logger.error(f"记录清理日志失败: {str(e)}")
    
    async def _notify_admin_on_failure(self, error_message: str):
        """
        清理任务失败时通知管理员
        
        Args:
            error_message: 错误信息
        """
        try:
            # TODO: 实现通知功能（邮件、短信等）
            # 这里暂时只记录日志
            logger.error(f"清理任务失败，需要管理员关注: {error_message}")
            
        except Exception as e:
            logger.error(f"发送管理员通知失败: {str(e)}")
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """
        格式化文件大小
        
        Args:
            size_bytes: 字节数
            
        Returns:
            str: 格式化后的大小字符串
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


# 创建全局Worker实例
cleanup_worker = CleanupWorker()


async def main():
    """主函数，用于独立运行Worker"""
    try:
        logger.info("=" * 60)
        logger.info("清理Worker 启动中...")
        logger.info("=" * 60)
        
        await cleanup_worker.start()
        
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭Worker...")
        await cleanup_worker.stop()
    except Exception as e:
        logger.error(f"Worker运行异常: {str(e)}", exc_info=True)
        await cleanup_worker.stop()


if __name__ == "__main__":
    # 独立运行Worker
    asyncio.run(main())
