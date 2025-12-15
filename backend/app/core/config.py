"""
配置管理模块
使用Pydantic BaseSettings加载环境变量
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """系统配置类"""
    
    # 应用基础配置
    APP_NAME: str = "Enterprise IDP Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development / production
    
    # 数据库配置
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    # Redis配置
    REDIS_URL: str
    REDIS_MAX_CONNECTIONS: int = 50
    
    # RabbitMQ配置
    RABBITMQ_URL: str
    RABBITMQ_QUEUE_OCR: str = "ocr_tasks"
    RABBITMQ_QUEUE_PIPELINE: str = "pipeline_tasks"
    RABBITMQ_QUEUE_PUSH: str = "push_tasks"
    RABBITMQ_QUEUE_DLQ: str = "push_dlq"
    
    # MinIO配置
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "idp-files"
    MINIO_SECURE: bool = False
    
    # 安全配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENCRYPTION_KEY: Optional[str] = None
    
    # OCR配置
    OCR_TIMEOUT: int = 300  # 秒
    OCR_MAX_PARALLEL: int = 4
    OCR_DEFAULT_ENGINE: str = "paddleocr"
    OCR_DEFAULT_LANGUAGE: str = "ch"
    
    # Tesseract配置
    TESSERACT_CMD: Optional[str] = None  # Tesseract可执行文件路径
    TESSDATA_PREFIX: Optional[str] = None  # Tesseract语言包目录
    
    # LLM配置（OpenAI兼容协议）
    LLM_BASE_URL: Optional[str] = "https://api.openai.com/v1"
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_TIMEOUT: int = 60  # 秒
    LLM_TOKEN_PRICE: float = 0.002  # 每Token价格
    LLM_MAX_TOKENS: int = 4000
    LLM_PROXY: Optional[str] = None  # 代理地址（可选）
    
    # UmiOCR配置（可选，通过 Docker 部署的 HTTP 服务）
    UMIOCR_ENDPOINT: str = "http://localhost:1224"
    UMIOCR_TIMEOUT: int = 60  # 秒
    
    # 文件处理配置
    MAX_FILE_SIZE: int = 20 * 1024 * 1024  # 20MB
    MAX_PAGE_COUNT: int = 50
    ALLOWED_FILE_TYPES: list = ["application/pdf", "image/png", "image/jpeg"]
    
    # 限流配置
    RATE_LIMIT_UPLOAD: int = 100  # 每分钟
    RATE_LIMIT_QUERY: int = 1000  # 每分钟
    
    # 数据生命周期配置
    FILE_RETENTION_DAYS: int = 30
    DATA_RETENTION_DAYS: int = 0  # 0表示永久保留
    
    # 缓存配置
    CACHE_TTL_RULE_CONFIG: int = 3600  # 规则配置缓存1小时
    CACHE_TTL_DASHBOARD: int = 300  # 仪表盘数据缓存5分钟
    CACHE_TTL_PREVIEW: int = 3600  # PDF预览缓存1小时
    
    # 推送配置
    PUSH_RETRY_MAX: int = 3
    PUSH_RETRY_DELAYS: list = [10, 30, 90]  # 秒
    PUSH_TIMEOUT: int = 30  # 秒
    
    # 熔断器配置
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 300  # 秒
    
    # CORS配置
    CORS_ORIGINS: list = ["http://localhost", "http://localhost:80"]
    
    # 金蝶K3 Cloud配置
    KINGDEE_API_URL: Optional[str] = None
    KINGDEE_DB_ID: Optional[str] = None
    KINGDEE_USERNAME: Optional[str] = None
    KINGDEE_PASSWORD: Optional[str] = None
    KINGDEE_SAVE_MODE: str = "smart"  # smart | save_only | draft_only
    KINGDEE_TIMEOUT: int = 30  # 秒
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()
