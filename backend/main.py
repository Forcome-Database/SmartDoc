"""
Enterprise IDP Platform - Main Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.core.middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware
)

# Application metadata
APP_TITLE = "Enterprise IDP Platform"
APP_DESCRIPTION = """
企业级智能文档处理中台 (Enterprise IDP Platform)

## 核心功能

* **文档上传与去重**: 支持PDF/图片上传，基于哈希的秒传机制
* **OCR识别**: 支持PaddleOCR、Tesseract、UmiOCR
* **智能提取**: 正则、锚点、表格、LLM多种提取策略
* **人工审核**: 可视化审核工作台，支持多页PDF预览和数据修正
* **安全推送**: HMAC签名、多目标推送、失败重试机制
* **规则管理**: 版本控制、沙箱测试、配置热更新
* **仪表盘**: 实时监控、效能分析、异常追踪
"""
APP_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print(f"🚀 {APP_TITLE} v{APP_VERSION} is starting...")
    
    # TODO: Initialize database connection pool
    # TODO: Initialize Redis connection
    # TODO: Initialize RabbitMQ connection
    # TODO: Initialize MinIO client
    
    yield
    
    # Shutdown
    print(f"👋 {APP_TITLE} is shutting down...")
    
    # TODO: Close database connections
    # TODO: Close Redis connections
    # TODO: Close RabbitMQ connections


# Create FastAPI application
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)


# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
        "http://localhost:8080",  # Production frontend
        "http://localhost",       # Production frontend (port 80)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-Response-Time"]
)

# Add custom middlewares (order matters - last added is executed first)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": APP_TITLE,
        "version": APP_VERSION
    }


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {APP_TITLE}",
        "version": APP_VERSION,
        "docs": "/api/docs"
    }


# Include API routers
from app.api.v1 import api_router
app.include_router(api_router, prefix="/api/v1")

# TODO: Include other routers as they are implemented
# from app.api.v1.endpoints import tasks, rules, audit, webhook, dashboard, users, system
# app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
# app.include_router(rules.router, prefix="/api/v1/rules", tags=["Rules"])
# app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit"])
# app.include_router(webhook.router, prefix="/api/v1/webhooks", tags=["Webhooks"])
# app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
# app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
# app.include_router(system.router, prefix="/api/v1/system", tags=["System"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
