"""
Pipeline处理Worker

从RabbitMQ消费Pipeline任务，执行数据处理脚本，然后触发Webhook推送
"""
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logger import logger
from app.core.database import SessionLocal
from app.core.mq import rabbitmq_client
from app.core.config import settings
from app.models.task import Task, TaskStatus
from app.models.pipeline import Pipeline, PipelineExecution, ExecutionStatus, PipelineStatus
from app.services.pipeline_service import PipelineService


class PipelineWorker:
    """Pipeline处理Worker类"""
    
    def __init__(self):
        """初始化Worker"""
        self.is_running = False
        logger.info("Pipeline Worker初始化完成")
    
    async def start(self):
        """启动Worker，开始消费消息"""
        if self.is_running:
            logger.warning("Pipeline Worker已在运行中")
            return
        
        self.is_running = True
        logger.info("Pipeline Worker启动，开始消费任务...")
        
        try:
            # 连接RabbitMQ
            await rabbitmq_client.connect()
            
            # 开始消费Pipeline任务队列
            await rabbitmq_client.consume_tasks(
                queue_name=settings.RABBITMQ_QUEUE_PIPELINE,
                callback=self.process_task
            )
            
        except Exception as e:
            logger.error(f"Pipeline Worker运行失败: {str(e)}")
            self.is_running = False
            raise
    
    async def stop(self):
        """停止Worker"""
        self.is_running = False
        await rabbitmq_client.close()
        logger.info("Pipeline Worker已停止")

    async def process_task(self, task_data: Dict[str, Any]):
        """
        处理单个Pipeline任务
        
        Args:
            task_data: 任务数据，包含task_id和retry_count
        """
        task_id = task_data.get('task_id')
        retry_count = task_data.get('retry_count', 0)  # 从消息中获取重试次数
        
        if not task_id:
            logger.error("任务数据缺少task_id")
            return
        
        logger.info(f"开始处理Pipeline任务: {task_id}, 当前重试次数: {retry_count}")
        
        async with SessionLocal() as db:
            try:
                # 1. 获取任务
                stmt = select(Task).where(Task.id == task_id)
                result = await db.execute(stmt)
                task = result.scalar_one_or_none()
                
                if not task:
                    logger.error(f"任务不存在: {task_id}")
                    return
                
                # 2. 获取规则关联的管道
                stmt = select(Pipeline).where(
                    Pipeline.rule_id == task.rule_id,
                    Pipeline.status == "active"
                )
                result = await db.execute(stmt)
                pipeline = result.scalar_one_or_none()
                
                if not pipeline:
                    logger.info(f"任务 {task_id} 没有关联的活跃管道，直接触发推送")
                    await self._trigger_push(task_id)
                    return
                
                # 3. 创建Pipeline服务并执行
                pipeline_service = PipelineService(db)
                
                # 创建执行记录，传递当前重试次数
                execution = await pipeline_service.create_execution(pipeline, task, retry_count)
                logger.info(f"创建Pipeline执行记录: {execution.id}, 重试次数: {retry_count}")
                
                # 执行管道
                execution = await pipeline_service.run_execution(execution, pipeline)
                
                # 4. 根据执行结果处理
                if execution.status == ExecutionStatus.SUCCESS:
                    # 更新任务的提取数据为管道处理后的数据
                    if execution.output_data:
                        task.extracted_data = execution.output_data
                        await db.commit()
                        logger.info(f"任务 {task_id} 数据已更新为管道处理结果")
                    
                    # 触发推送
                    await self._trigger_push(task_id)
                    logger.info(f"Pipeline执行成功，已触发推送: {task_id}")
                    
                else:
                    # 执行失败，根据重试配置决定是否重试
                    # 使用消息中的 retry_count 而不是 execution.retry_count
                    if retry_count < pipeline.max_retries:
                        # 重新入队重试
                        await self._retry_pipeline(task_id, retry_count + 1)
                        logger.warning(f"Pipeline执行失败，安排重试: {task_id}, 重试次数: {retry_count + 1}/{pipeline.max_retries}")
                    else:
                        # 达到最大重试次数，标记任务失败并移入死信队列
                        task.status = TaskStatus.FAILED
                        total_attempts = retry_count + 1  # 总执行次数 = 重试次数 + 首次执行
                        task.error_message = f"Pipeline执行失败（共执行{total_attempts}次）: {execution.error_message}"
                        await db.commit()
                        logger.error(f"Pipeline执行失败，已达最大重试次数: {task_id}, 执行次数: {total_attempts}, 最大重试: {pipeline.max_retries}")
                        
                        # 移入死信队列，便于后续排查和手动重试
                        await self._move_to_dlq(task_id, pipeline.id, execution.error_message, retry_count)
                
            except Exception as e:
                logger.error(f"Pipeline任务处理失败 [{task_id}]: {str(e)}", exc_info=True)
                
                # 更新任务状态为失败
                try:
                    stmt = select(Task).where(Task.id == task_id)
                    result = await db.execute(stmt)
                    task = result.scalar_one_or_none()
                    if task:
                        task.status = TaskStatus.FAILED
                        task.error_message = f"Pipeline处理异常: {str(e)}"
                        await db.commit()
                except Exception as update_error:
                    logger.error(f"更新任务状态失败: {str(update_error)}")
    
    async def _trigger_push(self, task_id: str):
        """触发推送任务"""
        try:
            push_task_data = {
                'task_id': task_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await rabbitmq_client.publish_task(
                queue_name=settings.RABBITMQ_QUEUE_PUSH,
                task_data=push_task_data
            )
            
            logger.info(f"推送任务已触发: {task_id}")
            
        except Exception as e:
            logger.error(f"触发推送任务失败: {str(e)}")
    
    async def _retry_pipeline(self, task_id: str, retry_count: int):
        """重试Pipeline任务"""
        try:
            # 延迟重试（指数退避）
            delay = min(30 * (2 ** retry_count), 300)  # 最大5分钟
            
            await asyncio.sleep(delay)
            
            pipeline_task_data = {
                'task_id': task_id,
                'retry_count': retry_count,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await rabbitmq_client.publish_task(
                queue_name=settings.RABBITMQ_QUEUE_PIPELINE,
                task_data=pipeline_task_data
            )
            
            logger.info(f"Pipeline重试任务已入队: {task_id}, 重试次数: {retry_count}")
            
        except Exception as e:
            logger.error(f"Pipeline重试入队失败: {str(e)}")


# 创建全局Worker实例
pipeline_worker = PipelineWorker()


async def main():
    """主函数，用于独立运行Worker"""
    try:
        logger.info("=" * 60)
        logger.info("Pipeline Worker 启动中...")
        logger.info("=" * 60)
        
        await pipeline_worker.start()
        
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭Worker...")
        await pipeline_worker.stop()
    except Exception as e:
        logger.error(f"Worker运行异常: {str(e)}", exc_info=True)
        await pipeline_worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
