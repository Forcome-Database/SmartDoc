"""
API v1路由配置
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, upload, tasks, rules, webhook, audit, dashboard, users, api_keys, system, audit_logs, pipelines

api_router = APIRouter()

# 注册各个端点路由
# 注意：不要重复添加prefix，因为各个router已经在自己的文件中定义了prefix
api_router.include_router(auth.router, tags=["认证"])
api_router.include_router(upload.router, tags=["文件上传"])
api_router.include_router(tasks.router, tags=["任务管理"])
api_router.include_router(rules.router, tags=["规则管理"])
api_router.include_router(webhook.router, tags=["Webhook配置"])
api_router.include_router(audit.router, tags=["审核工作台"])
api_router.include_router(dashboard.router, tags=["仪表盘"])
api_router.include_router(users.router, tags=["用户管理"])
api_router.include_router(api_keys.router, tags=["API Key管理"])
api_router.include_router(system.router, tags=["系统配置"])
api_router.include_router(audit_logs.router, tags=["审计日志"])
api_router.include_router(pipelines.router, tags=["数据处理管道"])
