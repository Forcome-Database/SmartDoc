"""
推送Worker
负责消费推送任务队列，将处理完成的任务结果推送到下游Webhook目标
支持并行推送、指数退避重试和死信队列处理
"""
import asyncio
import json
import logging
import signal
import sys
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, selectinload

from app.core.config import settings
from app.core.mq import RabbitMQClient
from app.models.task import Task, TaskStatus
from app.models.webhook import Webhook
from app.services.push_service import PushService
from app.services.dingtalk_service import dingtalk_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PushWorker:
    """推送Worker类"""
    
    def __init__(self):
        """初始化推送Worker"""
        self.mq_client: Optional[RabbitMQClient] = None
        self.engine = None
        self.async_session = None
        self.running = False
        
        logger.info("推送Worker初始化完成")
    
    async def setup(self):
        """设置数据库连接和消息队列"""
        try:
            # 创建异步数据库引擎
            self.engine = create_async_engine(
                settings.DATABASE_URL,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=False
            )
            
            # 创建异步会话工厂
            self.async_session = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # 初始化RabbitMQ连接
            self.mq_client = RabbitMQClient()
            await self.mq_client.connect()
            
            logger.info("推送Worker设置完成")
            
        except Exception as e:
            logger.error(f"推送Worker设置失败: {str(e)}")
            raise
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.mq_client:
                await self.mq_client.close()
            
            if self.engine:
                await self.engine.dispose()
            
            logger.info("推送Worker资源清理完成")
            
        except Exception as e:
            logger.error(f"推送Worker清理失败: {str(e)}")
    
    async def start(self):
        """启动Worker，开始消费推送任务"""
        try:
            await self.setup()
            
            self.running = True
            logger.info(f"推送Worker已启动，监听队列: {settings.RABBITMQ_QUEUE_PUSH}")
            
            # 开始消费推送任务队列
            await self.mq_client.consume_tasks(
                queue_name=settings.RABBITMQ_QUEUE_PUSH,
                callback=self.process_push
            )
            
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在停止推送Worker...")
            self.running = False
        except Exception as e:
            logger.error(f"推送Worker运行异常: {str(e)}")
            raise
        finally:
            await self.cleanup()
    
    async def process_push(self, task_data: Dict[str, Any]):
        """
        处理单个推送任务
        
        Args:
            task_data: 任务数据，包含task_id、webhook_id（可选）、retry_count等
        """
        task_id = task_data.get("task_id")
        webhook_id = task_data.get("webhook_id")  # 可选，用于单个Webhook重试
        retry_count = task_data.get("retry_count", 0)
        
        logger.info(
            f"开始处理推送任务: task_id={task_id}, "
            f"webhook_id={webhook_id or 'all'}, retry_count={retry_count}"
        )
        
        async with self.async_session() as db:
            try:
                # 1. 加载任务和Webhook配置
                task, webhooks = await self._load_task_and_webhooks(
                    db, task_id, webhook_id
                )
                
                if not task:
                    logger.error(f"任务不存在: task_id={task_id}")
                    return
                
                if not webhooks:
                    logger.warning(f"任务没有关联的Webhook配置: task_id={task_id}")
                    # 更新任务状态为已完成（无需推送）
                    task.status = TaskStatus.COMPLETED
                    await db.commit()
                    return
                
                # 2. 更新任务状态为推送中
                if task.status != TaskStatus.PUSHING:
                    task.status = TaskStatus.PUSHING
                    await db.commit()
                
                # 3. 创建推送服务
                push_service = PushService(db)
                
                # 4. 并行推送到所有关联的Webhook目标
                results = await push_service.batch_push(task, webhooks)
                
                # 5. 检查推送结果
                await self._handle_push_results(
                    db, push_service, task, webhooks, results, retry_count
                )
                
                logger.info(f"推送任务处理完成: task_id={task_id}")
                
            except Exception as e:
                logger.error(f"推送任务处理失败: task_id={task_id}, error={str(e)}")
                
                # 更新任务状态为推送失败
                try:
                    result = await db.execute(
                        select(Task).where(Task.id == task_id)
                    )
                    task = result.scalar_one_or_none()
                    if task:
                        task.status = TaskStatus.PUSH_FAILED
                        task.error_message = f"推送异常: {str(e)}"
                        await db.commit()
                except Exception as update_error:
                    logger.error(f"更新任务状态失败: {str(update_error)}")
                    await db.rollback()
    
    async def _load_task_and_webhooks(
        self,
        db: AsyncSession,
        task_id: str,
        webhook_id: Optional[str] = None
    ) -> tuple[Optional[Task], list[Webhook]]:
        """
        加载任务和Webhook配置
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            webhook_id: Webhook ID（可选，如果指定则只加载该Webhook）
            
        Returns:
            (任务对象, Webhook列表)
        """
        try:
            # 加载任务，预加载规则
            from app.models.rule import Rule
            result = await db.execute(
                select(Task)
                .options(
                    selectinload(Task.rule).selectinload(Rule.webhooks)
                )
                .where(Task.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                return None, []
            
            # 获取Webhook列表
            if webhook_id:
                # 只推送到指定的Webhook
                webhook_result = await db.execute(
                    select(Webhook)
                    .where(
                        Webhook.id == webhook_id,
                        Webhook.is_active == True
                    )
                )
                webhook = webhook_result.scalar_one_or_none()
                webhooks = [webhook] if webhook else []
            else:
                # 推送到所有关联的激活Webhook
                if task.rule and task.rule.webhooks:
                    webhooks = [
                        wh for wh in task.rule.webhooks
                        if wh.is_active
                    ]
                else:
                    webhooks = []
            
            return task, webhooks
            
        except Exception as e:
            logger.error(f"加载任务和Webhook配置失败: {str(e)}")
            return None, []
    
    async def _handle_push_results(
        self,
        db: AsyncSession,
        push_service: PushService,
        task: Task,
        webhooks: list[Webhook],
        results: list,
        retry_count: int
    ):
        """
        处理推送结果，决定是否重试或移入死信队列
        
        Args:
            db: 数据库会话
            push_service: 推送服务
            task: 任务对象
            webhooks: Webhook列表
            results: 推送结果列表
            retry_count: 当前重试次数
        """
        # 统计成功和失败的推送
        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count
        
        logger.info(
            f"推送结果统计: task_id={task.id}, "
            f"成功={success_count}, 失败={failed_count}, 总数={len(results)}"
        )
        
        # 如果全部成功
        if failed_count == 0:
            task.status = TaskStatus.PUSH_SUCCESS
            await db.commit()
            logger.info(f"所有推送成功: task_id={task.id}")
            
            # 发送推送成功通知
            await self._send_push_notification(
                task, webhooks[0].name if webhooks else None, True
            )
            return
        
        # 如果有失败，判断是否需要重试
        if retry_count < settings.PUSH_RETRY_MAX:
            # 对失败的Webhook进行重试
            for i, result in enumerate(results):
                if not result.success:
                    webhook = webhooks[i]
                    
                    # 判断是否应该重试
                    if await push_service.should_retry(result, retry_count):
                        # 计算延迟时间
                        delay = push_service.calculate_retry_delay(retry_count)
                        
                        # 发布延迟重试任务
                        await self.mq_client.publish_task(
                            queue_name=settings.RABBITMQ_QUEUE_PUSH,
                            task_data={
                                "task_id": task.id,
                                "webhook_id": webhook.id,
                                "retry_count": retry_count + 1
                            },
                            delay=delay
                        )
                        
                        logger.info(
                            f"已安排重试: task_id={task.id}, webhook={webhook.name}, "
                            f"retry_count={retry_count + 1}, delay={delay}s"
                        )
                    else:
                        # 不应该重试，直接移入死信队列
                        await push_service.move_to_dlq(
                            task_id=task.id,
                            webhook_id=webhook.id,
                            failure_reason=result.error_message or f"HTTP {result.http_status}",
                            retry_count=retry_count
                        )
                        
                        logger.warning(
                            f"推送失败且不应重试，已移入死信队列: "
                            f"task_id={task.id}, webhook={webhook.name}"
                        )
            
            # 如果部分成功，保持推送中状态
            if success_count > 0:
                task.status = TaskStatus.PUSHING
            else:
                task.status = TaskStatus.PUSH_FAILED
            
            await db.commit()
        
        else:
            # 已达最大重试次数，移入死信队列
            for i, result in enumerate(results):
                if not result.success:
                    webhook = webhooks[i]
                    await push_service.move_to_dlq(
                        task_id=task.id,
                        webhook_id=webhook.id,
                        failure_reason=result.error_message or f"HTTP {result.http_status}",
                        retry_count=retry_count
                    )
            
            # 更新任务状态
            if success_count > 0:
                # 部分成功
                task.status = TaskStatus.PUSH_FAILED
                task.error_message = f"部分推送失败: {failed_count}/{len(results)}"
            else:
                # 全部失败
                task.status = TaskStatus.PUSH_FAILED
                task.error_message = f"所有推送失败，已达最大重试次数: {retry_count}"
            
            await db.commit()
            
            logger.error(
                f"推送失败，已达最大重试次数: task_id={task.id}, "
                f"retry_count={retry_count}, failed={failed_count}/{len(results)}"
            )
            
            # 发送推送失败通知
            failed_webhooks = [webhooks[i].name for i, r in enumerate(results) if not r.success]
            await self._send_push_notification(
                task, 
                ', '.join(failed_webhooks), 
                False, 
                f"已达最大重试次数({retry_count})，已移入死信队列"
            )


    async def _send_push_notification(
        self,
        task: Task,
        webhook_name: Optional[str],
        success: bool,
        error_message: Optional[str] = None
    ):
        """
        发送推送结果钉钉通知
        
        Args:
            task: 任务对象
            webhook_name: Webhook名称
            success: 是否成功
            error_message: 错误信息
        """
        try:
            # 获取规则名称
            rule_name = task.rule.name if task.rule else '未知规则'
            
            await dingtalk_service.notify_push_result(
                task_id=str(task.id),
                file_name=task.file_name,
                rule_id=str(task.rule_id),
                rule_name=rule_name,
                success=success,
                webhook_name=webhook_name,
                error_message=error_message
            )
            
            logger.info(f"推送结果通知已发送: task_id={task.id}, success={success}")
            
        except Exception as e:
            # 通知失败不影响主流程
            logger.warning(f"发送推送结果通知失败: {str(e)}")


# 全局Worker实例
worker: Optional[PushWorker] = None


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"收到信号 {signum}，正在停止Worker...")
    if worker:
        worker.running = False
    sys.exit(0)


async def main():
    """主函数"""
    global worker
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建并启动Worker
    worker = PushWorker()
    
    try:
        await worker.start()
    except Exception as e:
        logger.error(f"推送Worker异常退出: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # 运行Worker
    asyncio.run(main())
