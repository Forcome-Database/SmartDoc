"""
Redis缓存管理模块
提供缓存操作和限流功能
"""
import redis.asyncio as redis
from typing import Optional, Any
import json
import logging
import asyncio
from datetime import timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis连接超时配置（秒）
REDIS_CONNECT_TIMEOUT = 3
REDIS_SOCKET_TIMEOUT = 3


class RedisClient:
    """Redis客户端封装类"""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._connected: bool = False
        self._connection_failed: bool = False
    
    async def connect(self):
        """建立Redis连接（带超时保护）"""
        if self._client is not None and self._connected:
            return
        
        # 如果之前连接失败，跳过重试（避免每次请求都尝试连接）
        if self._connection_failed:
            return
        
        try:
            self._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_connect_timeout=REDIS_CONNECT_TIMEOUT,
                socket_timeout=REDIS_SOCKET_TIMEOUT,
            )
            # 测试连接是否可用
            await asyncio.wait_for(self._client.ping(), timeout=REDIS_CONNECT_TIMEOUT)
            self._connected = True
            logger.info("Redis连接已建立")
        except asyncio.TimeoutError:
            logger.warning(f"Redis连接超时（{REDIS_CONNECT_TIMEOUT}秒），将禁用Redis功能")
            self._connection_failed = True
            self._client = None
        except Exception as e:
            logger.warning(f"Redis连接失败: {str(e)}，将禁用Redis功能")
            self._connection_failed = True
            self._client = None
    
    async def close(self):
        """关闭Redis连接"""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Redis连接已关闭")
    
    async def get(self, key: str) -> Optional[str]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，不存在返回None
        """
        try:
            if not self._client:
                await self.connect()
            if not self._client or not self._connected:
                return None
            return await asyncio.wait_for(self._client.get(key), timeout=REDIS_SOCKET_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning(f"Redis GET超时 [{key}]")
            return None
        except Exception as e:
            logger.error(f"Redis GET错误 [{key}]: {str(e)}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None
    ) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒），None表示永不过期
            
        Returns:
            是否设置成功
        """
        try:
            if not self._client:
                await self.connect()
            if not self._client or not self._connected:
                return False
            
            # 如果value是字典或列表，转换为JSON字符串
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            if expire:
                return await asyncio.wait_for(self._client.setex(key, expire, value), timeout=REDIS_SOCKET_TIMEOUT)
            else:
                return await asyncio.wait_for(self._client.set(key, value), timeout=REDIS_SOCKET_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning(f"Redis SET超时 [{key}]")
            return False
        except Exception as e:
            logger.error(f"Redis SET错误 [{key}]: {str(e)}")
            return False
    
    async def delete(self, *keys: str) -> int:
        """
        删除缓存键
        
        Args:
            *keys: 要删除的键列表
            
        Returns:
            删除的键数量
        """
        try:
            if not self._client:
                await self.connect()
            if not self._client or not self._connected:
                return 0
            return await asyncio.wait_for(self._client.delete(*keys), timeout=REDIS_SOCKET_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning(f"Redis DELETE超时")
            return 0
        except Exception as e:
            logger.error(f"Redis DELETE错误: {str(e)}")
            return 0
    
    async def exists(self, *keys: str) -> int:
        """
        检查键是否存在
        
        Args:
            *keys: 要检查的键列表
            
        Returns:
            存在的键数量
        """
        try:
            if not self._client:
                await self.connect()
            if not self._client or not self._connected:
                return 0
            return await asyncio.wait_for(self._client.exists(*keys), timeout=REDIS_SOCKET_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning(f"Redis EXISTS超时")
            return 0
        except Exception as e:
            logger.error(f"Redis EXISTS错误: {str(e)}")
            return 0
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """
        递增计数器
        
        Args:
            key: 计数器键
            amount: 递增量
            
        Returns:
            递增后的值
        """
        try:
            if not self._client:
                await self.connect()
            if not self._client or not self._connected:
                return 0
            return await asyncio.wait_for(self._client.incrby(key, amount), timeout=REDIS_SOCKET_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning(f"Redis INCR超时 [{key}]")
            return 0
        except Exception as e:
            logger.error(f"Redis INCR错误 [{key}]: {str(e)}")
            return 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        设置键的过期时间
        
        Args:
            key: 键名
            seconds: 过期时间（秒）
            
        Returns:
            是否设置成功
        """
        try:
            if not self._client:
                await self.connect()
            if not self._client or not self._connected:
                return False
            return await asyncio.wait_for(self._client.expire(key, seconds), timeout=REDIS_SOCKET_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning(f"Redis EXPIRE超时 [{key}]")
            return False
        except Exception as e:
            logger.error(f"Redis EXPIRE错误 [{key}]: {str(e)}")
            return False
    
    async def ttl(self, key: str) -> int:
        """
        获取键的剩余生存时间
        
        Args:
            key: 键名
            
        Returns:
            剩余秒数，-1表示永不过期，-2表示不存在
        """
        try:
            if not self._client:
                await self.connect()
            if not self._client or not self._connected:
                return -2
            return await asyncio.wait_for(self._client.ttl(key), timeout=REDIS_SOCKET_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning(f"Redis TTL超时 [{key}]")
            return -2
        except Exception as e:
            logger.error(f"Redis TTL错误 [{key}]: {str(e)}")
            return -2
    
    async def check_rate_limit(
        self, 
        key: str, 
        limit: int, 
        window: int = 60
    ) -> tuple[bool, int]:
        """
        检查限流
        
        Args:
            key: 限流键（如 "ratelimit:api_key:endpoint"）
            limit: 限流阈值
            window: 时间窗口（秒）
            
        Returns:
            (是否允许, 剩余次数)
        """
        try:
            if not self._client:
                await self.connect()
            
            # Redis不可用时，允许请求通过
            if not self._client or not self._connected:
                return True, limit
            
            # 获取当前计数
            current = await asyncio.wait_for(self._client.get(key), timeout=REDIS_SOCKET_TIMEOUT)
            
            if current is None:
                # 首次请求，设置计数为1
                await asyncio.wait_for(self._client.setex(key, window, 1), timeout=REDIS_SOCKET_TIMEOUT)
                return True, limit - 1
            
            current = int(current)
            
            if current >= limit:
                # 超过限流阈值
                return False, 0
            
            # 递增计数
            await asyncio.wait_for(self._client.incr(key), timeout=REDIS_SOCKET_TIMEOUT)
            return True, limit - current - 1
            
        except asyncio.TimeoutError:
            logger.warning(f"限流检查超时 [{key}]")
            # 超时时允许请求通过
            return True, limit
        except Exception as e:
            logger.error(f"限流检查错误 [{key}]: {str(e)}")
            # 出错时允许请求通过
            return True, limit
    
    def reset_connection_state(self):
        """重置连接状态，允许重新尝试连接"""
        self._connection_failed = False
        self._connected = False


# 创建全局Redis客户端实例
redis_client = RedisClient()


async def get_redis() -> Optional[RedisClient]:
    """
    获取Redis客户端实例（依赖注入）
    
    Returns:
        RedisClient实例，如果连接失败返回None
    """
    if not redis_client._connected:
        await redis_client.connect()
    
    # 如果连接失败，返回None
    if redis_client._connection_failed:
        return None
    
    return redis_client
