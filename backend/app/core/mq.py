"""
RabbitMQ消息队列管理模块
提供消息发布和消费功能
"""
import aio_pika
from aio_pika import Message, DeliveryMode, ExchangeType
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue
from typing import Optional, Callable, Dict, Any
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """RabbitMQ客户端封装类"""
    
    def __init__(self):
        self._connection: Optional[AbstractConnection] = None
        self._channel: Optional[AbstractChannel] = None
        self._queues: Dict[str, AbstractQueue] = {}
    
    async def connect(self):
        """建立RabbitMQ连接"""
        if self._connection is None or self._connection.is_closed:
            self._connection = await aio_pika.connect_robust(
                settings.RABBITMQ_URL,
                timeout=30,
            )
            self._channel = await self._connection.channel()
            
            # 设置QoS（每次只处理一个消息）
            await self._channel.set_qos(prefetch_count=1)
            
            # 声明所有队列
            await self._declare_queues()
            
            logger.info("RabbitMQ连接已建立")
    
    async def _declare_queues(self):
        """声明所有任务队列"""
        # OCR处理队列
        self._queues[settings.RABBITMQ_QUEUE_OCR] = await self._channel.declare_queue(
            settings.RABBITMQ_QUEUE_OCR,
            durable=True,  # 持久化队列
            arguments={
                "x-message-ttl": 3600000,  # 消息TTL 1小时
                "x-max-length": 10000,  # 最大队列长度
            }
        )
        
        # Pipeline处理队列
        self._queues[settings.RABBITMQ_QUEUE_PIPELINE] = await self._channel.declare_queue(
            settings.RABBITMQ_QUEUE_PIPELINE,
            durable=True,
            arguments={
                "x-message-ttl": 3600000,  # 消息TTL 1小时
                "x-max-length": 10000,  # 最大队列长度
            }
        )
        
        # 推送任务队列
        self._queues[settings.RABBITMQ_QUEUE_PUSH] = await self._channel.declare_queue(
            settings.RABBITMQ_QUEUE_PUSH,
            durable=True,
            arguments={
                "x-message-ttl": 3600000,
                "x-max-length": 10000,
            }
        )
        
        # 死信队列
        self._queues[settings.RABBITMQ_QUEUE_DLQ] = await self._channel.declare_queue(
            settings.RABBITMQ_QUEUE_DLQ,
            durable=True,
        )
        
        logger.info(f"队列声明完成: {list(self._queues.keys())}")
    
    async def close(self):
        """关闭RabbitMQ连接"""
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        
        self._connection = None
        self._channel = None
        self._queues = {}
        logger.info("RabbitMQ连接已关闭")
    
    async def publish_task(
        self,
        queue_name: str,
        task_data: Dict[str, Any],
        delay: Optional[int] = None
    ) -> bool:
        """
        发布任务到队列
        
        Args:
            queue_name: 队列名称
            task_data: 任务数据（字典）
            delay: 延迟时间（秒），用于重试
            
        Returns:
            是否发布成功
        """
        try:
            if not self._channel or self._channel.is_closed:
                await self.connect()
            
            # 将任务数据转换为JSON
            message_body = json.dumps(task_data, ensure_ascii=False)
            
            # 创建消息
            message = Message(
                body=message_body.encode(),
                delivery_mode=DeliveryMode.PERSISTENT,  # 持久化消息
                content_type="application/json",
            )
            
            # 如果有延迟，设置过期时间（注意：expiration需要整数毫秒）
            if delay:
                message.expiration = int(delay * 1000)  # 毫秒，整数类型
            
            # 发布消息到队列
            await self._channel.default_exchange.publish(
                message,
                routing_key=queue_name,
            )
            
            logger.info(f"任务已发布到队列 [{queue_name}]: {task_data.get('task_id', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"发布任务失败 [{queue_name}]: {str(e)}")
            return False
    
    async def consume_tasks(
        self,
        queue_name: str,
        callback: Callable,
    ):
        """
        消费队列中的任务
        
        Args:
            queue_name: 队列名称
            callback: 回调函数，接收消息体
        """
        try:
            if not self._channel or self._channel.is_closed:
                await self.connect()
            
            queue = self._queues.get(queue_name)
            if not queue:
                raise ValueError(f"队列不存在: {queue_name}")
            
            logger.info(f"开始消费队列: {queue_name}")
            
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    task_data = None
                    try:
                        # 解析消息体
                        task_data = json.loads(message.body.decode())
                        
                        # 调用回调函数处理任务
                        await callback(task_data)
                        
                        # 消息处理成功，手动ACK
                        await message.ack()
                        logger.info(f"任务处理成功并已确认: {task_data.get('task_id', 'unknown')}")
                        
                    except Exception as e:
                        task_id = task_data.get('task_id', 'unknown') if task_data else 'unknown'
                        logger.error(f"任务处理失败 [{task_id}]: {str(e)}", exc_info=True)
                        # 消息处理失败，NACK但不重新入队（避免无限重试）
                        try:
                            await message.nack(requeue=False)
                        except Exception as nack_error:
                            logger.error(f"NACK失败: {str(nack_error)}")
                            
        except Exception as e:
            logger.error(f"消费队列失败 [{queue_name}]: {str(e)}", exc_info=True)
            raise
    
    async def get_queue_size(self, queue_name: str) -> int:
        """
        获取队列长度
        
        Args:
            queue_name: 队列名称
            
        Returns:
            队列中的消息数量
        """
        try:
            if not self._channel or self._channel.is_closed:
                await self.connect()
            
            queue = self._queues.get(queue_name)
            if queue:
                # 直接返回队列对象的消息计数（如果可用）
                # aio_pika 新版本不支持 passive 参数
                return queue.declaration_result.message_count if hasattr(queue, 'declaration_result') else 0
            return 0
            
        except Exception as e:
            logger.error(f"获取队列长度失败 [{queue_name}]: {str(e)}")
            return 0
    
    async def purge_queue(self, queue_name: str) -> int:
        """
        清空队列
        
        Args:
            queue_name: 队列名称
            
        Returns:
            清除的消息数量
        """
        try:
            if not self._channel or self._channel.is_closed:
                await self.connect()
            
            queue = self._queues.get(queue_name)
            if queue:
                result = await queue.purge()
                logger.info(f"队列已清空 [{queue_name}]: {result} 条消息")
                return result
            return 0
            
        except Exception as e:
            logger.error(f"清空队列失败 [{queue_name}]: {str(e)}")
            return 0


# 创建全局RabbitMQ客户端实例
rabbitmq_client = RabbitMQClient()


async def get_rabbitmq() -> RabbitMQClient:
    """
    获取RabbitMQ客户端实例（依赖注入）
    
    Returns:
        RabbitMQClient实例
    """
    if not rabbitmq_client._connection or rabbitmq_client._connection.is_closed:
        await rabbitmq_client.connect()
    return rabbitmq_client


async def publish_task(queue_name: str, task_data: Dict[str, Any], delay: Optional[int] = None) -> bool:
    """
    便捷函数：发布任务到队列
    
    Args:
        queue_name: 队列名称
        task_data: 任务数据
        delay: 延迟时间（秒）
        
    Returns:
        是否发布成功
    """
    client = await get_rabbitmq()
    return await client.publish_task(queue_name, task_data, delay)
