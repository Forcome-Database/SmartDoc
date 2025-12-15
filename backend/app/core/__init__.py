"""
核心模块
包含配置、数据库、缓存、消息队列和存储客户端
"""
from app.core.config import settings
from app.core.database import (
    engine,
    SessionLocal,
    Base,
    get_db,
    init_db,
    close_db,
    check_db_connection,
    get_pool_status,
)
from app.core.cache import redis_client, get_redis, RedisClient
from app.core.mq import rabbitmq_client, get_rabbitmq, RabbitMQClient
from app.core.storage import minio_client, get_minio, MinIOClient

__all__ = [
    # 配置
    "settings",
    # 数据库
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "init_db",
    "close_db",
    "check_db_connection",
    "get_pool_status",
    # Redis
    "redis_client",
    "get_redis",
    "RedisClient",
    # RabbitMQ
    "rabbitmq_client",
    "get_rabbitmq",
    "RabbitMQClient",
    # MinIO
    "minio_client",
    "get_minio",
    "MinIOClient",
]
