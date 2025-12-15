"""
数据库连接池管理模块
使用SQLAlchemy创建异步数据库引擎和会话
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
from typing import AsyncGenerator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# 创建异步数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # 开发环境打印SQL语句
    pool_size=settings.DB_POOL_SIZE,  # 连接池大小
    max_overflow=settings.DB_MAX_OVERFLOW,  # 最大溢出连接数
    pool_timeout=settings.DB_POOL_TIMEOUT,  # 连接超时时间（秒）
    pool_recycle=settings.DB_POOL_RECYCLE,  # 连接回收时间（秒）
    pool_pre_ping=True,  # 连接前检查连接是否有效
    poolclass=QueuePool,  # 使用队列池
    connect_args={
        "connect_timeout": 10,  # 连接超时10秒
    }
)

# 创建SessionLocal工厂函数
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不过期对象
    autocommit=False,
    autoflush=False,
)

# 创建Base类用于模型定义
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    依赖注入函数，提供数据库会话
    
    使用方式:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    
    Yields:
        AsyncSession: 数据库会话对象
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话错误: {str(e)}")
            raise
        finally:
            await session.close()


async def init_db():
    """
    初始化数据库
    创建所有表（仅用于开发环境，生产环境使用Alembic迁移）
    """
    async with engine.begin() as conn:
        # 导入所有模型以确保它们被注册
        from app.models import user, rule, task, webhook, audit_log, push_log, api_key, system_config
        
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表创建完成")


async def close_db():
    """
    关闭数据库连接池
    应用关闭时调用
    """
    await engine.dispose()
    logger.info("数据库连接池已关闭")


async def check_db_connection():
    """
    检查数据库连接是否正常
    
    Returns:
        bool: 连接是否正常
    """
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        logger.info("数据库连接正常")
        return True
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        return False


def get_pool_status():
    """
    获取连接池状态信息
    
    Returns:
        dict: 连接池状态信息
    """
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total": pool.size() + pool.overflow(),
    }
