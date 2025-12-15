"""
FastAPI中间件
实现限流、请求日志等功能
"""
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Callable, Dict, Optional
import time
import json
from datetime import datetime

from app.core.cache import get_redis
from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    API限流中间件
    
    使用Redis实现分布式限流，支持不同端点的不同限流策略
    """
    
    # 限流配置：{路径模式: (请求数, 时间窗口秒数)}
    RATE_LIMITS: Dict[str, tuple] = {
        "/api/v1/ocr/upload": (100, 60),      # 上传接口：100次/分钟
        "/api/v1/tasks": (1000, 60),          # 查询接口：1000次/分钟
        "/api/v1/rules": (500, 60),           # 规则接口：500次/分钟
        "/api/v1/audit": (500, 60),           # 审核接口：500次/分钟
        "/api/v1/dashboard": (200, 60),       # 仪表盘：200次/分钟
        "default": (200, 60),                 # 默认限制：200次/分钟
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求，执行限流检查
        
        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: 响应对象
        """
        # 跳过健康检查和文档端点
        if request.url.path in ["/health", "/api/docs", "/api/redoc", "/api/openapi.json"]:
            return await call_next(request)
        
        # 获取限流标识（优先使用API Key，否则使用IP）
        identifier = await self._get_identifier(request)
        
        # 获取当前端点的限流配置
        limit, window = self._get_rate_limit(request.url.path)
        
        # 执行限流检查
        allowed, remaining, reset_time = await self._check_rate_limit(
            identifier, 
            request.url.path, 
            limit, 
            window
        )
        
        # 如果超过限流
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "code": 429,
                    "message": "请求过于频繁，请稍后再试",
                    "detail": f"限制: {limit}次/{window}秒"
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(int(reset_time - time.time()))
                }
            )
        
        # 处理请求
        response = await call_next(request)
        
        # 添加限流信息头
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response
    
    async def _get_identifier(self, request: Request) -> str:
        """
        获取限流标识
        
        优先使用API Key，否则使用客户端IP
        
        Args:
            request: 请求对象
            
        Returns:
            str: 限流标识
        """
        # 尝试从Authorization头获取API Key
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            # 使用Token的前16个字符作为标识（避免存储完整Token）
            return f"token:{token[:16]}"
        
        # 使用客户端IP（考虑代理）
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.headers.get("X-Real-IP", "")
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"
    
    def _get_rate_limit(self, path: str) -> tuple:
        """
        获取指定路径的限流配置
        
        Args:
            path: 请求路径
            
        Returns:
            tuple: (限制次数, 时间窗口秒数)
        """
        # 精确匹配
        if path in self.RATE_LIMITS:
            return self.RATE_LIMITS[path]
        
        # 前缀匹配
        for pattern, limit_config in self.RATE_LIMITS.items():
            if pattern != "default" and path.startswith(pattern):
                return limit_config
        
        # 返回默认配置
        return self.RATE_LIMITS["default"]
    
    async def _check_rate_limit(
        self, 
        identifier: str, 
        path: str, 
        limit: int, 
        window: int
    ) -> tuple:
        """
        检查是否超过限流
        
        使用Redis的滑动窗口算法实现限流
        
        Args:
            identifier: 限流标识
            path: 请求路径
            limit: 限制次数
            window: 时间窗口（秒）
            
        Returns:
            tuple: (是否允许, 剩余次数, 重置时间戳)
        """
        try:
            redis = await get_redis()
            if redis is None:
                # Redis不可用时，允许请求通过
                return True, limit, int(time.time() + window)
            
            # 构造Redis key
            current_minute = int(time.time() / window)
            key = f"ratelimit:{identifier}:{path}:{current_minute}"
            
            # 增加计数
            count = await redis.incr(key)
            
            # 第一次请求时设置过期时间
            if count == 1:
                await redis.expire(key, window)
            
            # 计算剩余次数和重置时间
            remaining = max(0, limit - count)
            reset_time = (current_minute + 1) * window
            
            # 判断是否超过限制
            allowed = count <= limit
            
            return allowed, remaining, reset_time
            
        except Exception as e:
            # Redis操作失败时，允许请求通过
            print(f"Rate limit check failed: {e}")
            return True, limit, int(time.time() + window)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    
    记录所有API请求的详细信息
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求，记录日志
        
        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: 响应对象
        """
        # 记录请求开始时间
        start_time = time.time()
        
        # 提取请求信息
        request_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("User-Agent", ""),
        }
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算耗时
            duration_ms = int((time.time() - start_time) * 1000)
            
            # 记录响应信息
            log_data = {
                **request_info,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
            
            # 输出日志
            self._log_request(log_data)
            
            # 添加响应时间头
            response.headers["X-Response-Time"] = f"{duration_ms}ms"
            
            return response
            
        except Exception as e:
            # 记录异常
            duration_ms = int((time.time() - start_time) * 1000)
            log_data = {
                **request_info,
                "status_code": 500,
                "duration_ms": duration_ms,
                "error": str(e),
            }
            self._log_request(log_data, level="ERROR")
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端真实IP
        
        Args:
            request: 请求对象
            
        Returns:
            str: 客户端IP
        """
        # 考虑代理情况
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP", "")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _log_request(self, log_data: dict, level: str = "INFO"):
        """
        输出请求日志
        
        Args:
            log_data: 日志数据
            level: 日志级别
        """
        # 格式化日志
        log_message = (
            f"{log_data['method']} {log_data['path']} "
            f"- {log_data['status_code']} "
            f"- {log_data['duration_ms']}ms "
            f"- {log_data['client_ip']}"
        )
        
        # 根据状态码和耗时判断日志级别
        if log_data['status_code'] >= 500:
            level = "ERROR"
        elif log_data['status_code'] >= 400:
            level = "WARNING"
        elif log_data['duration_ms'] > 1000:  # 超过1秒
            level = "WARNING"
        
        # 输出日志（实际项目中应使用专业的日志库如loguru）
        if level == "ERROR":
            print(f"[ERROR] {log_message}")
            if "error" in log_data:
                print(f"  Error: {log_data['error']}")
        elif level == "WARNING":
            print(f"[WARNING] {log_message}")
        else:
            print(f"[INFO] {log_message}")
        
        # 详细日志（可选，用于调试）
        if settings.DEBUG:
            print(f"  Details: {json.dumps(log_data, ensure_ascii=False)}")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全响应头中间件
    
    添加安全相关的HTTP响应头
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求，添加安全头
        
        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: 响应对象
        """
        response = await call_next(request)
        
        # 添加安全响应头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
