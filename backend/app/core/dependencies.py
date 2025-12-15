"""
FastAPI依赖注入函数
提供认证、授权等通用依赖，支持JWT Token和API Key两种认证方式
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Callable, Optional
from functools import wraps
from datetime import datetime

from app.core.database import get_db
from app.core.security import verify_token, verify_api_key_secret
from app.models.user import User, RoleEnum
from app.models.api_key import APIKey

# OAuth2密码流
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# API Key Header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_secret_header = APIKeyHeader(name="X-API-Secret", auto_error=False)


async def get_user_from_jwt(
    token: str,
    db: AsyncSession
) -> Optional[User]:
    """
    从JWT Token中提取并验证用户
    """
    payload = verify_token(token)
    if payload is None:
        return None
    
    user_id: str = payload.get("sub")
    if user_id is None:
        return None
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_from_api_key(
    key_id: str,
    secret: str,
    db: AsyncSession
) -> Optional[User]:
    """
    从API Key中验证并获取用户
    """
    # 查询API Key
    result = await db.execute(
        select(APIKey).where(
            APIKey.key_id == key_id,
            APIKey.is_active == True
        )
    )
    api_key = result.scalar_one_or_none()
    
    if api_key is None:
        return None
    
    # 检查是否过期
    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        return None
    
    # 验证Secret
    if not verify_api_key_secret(secret, api_key.secret_hash):
        return None
    
    # 更新最后使用时间
    api_key.last_used_at = datetime.utcnow()
    await db.commit()
    
    # 获取关联的用户
    user_result = await db.execute(
        select(User).where(User.id == api_key.user_id)
    )
    return user_result.scalar_one_or_none()


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    x_api_key: Optional[str] = Depends(api_key_header),
    x_api_secret: Optional[str] = Depends(api_secret_header),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前用户，支持多种认证方式：
    1. JWT Token (Authorization: Bearer <token>)
    2. API Key (X-API-Key + X-API-Secret headers)
    3. Bearer格式的API Key (Authorization: Bearer <key_id>:<secret>)
    
    Args:
        request: 请求对象
        token: JWT Token或Bearer格式的API Key
        x_api_key: API Key ID (通过X-API-Key header)
        x_api_secret: API Secret (通过X-API-Secret header)
        db: 数据库会话
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 401 - 认证失败
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user = None
    
    # 方式1: 尝试使用X-API-Key和X-API-Secret headers
    if x_api_key and x_api_secret:
        user = await get_user_from_api_key(x_api_key, x_api_secret, db)
        if user:
            return user
    
    # 方式2: 尝试解析Bearer token
    if token:
        # 检查是否是API Key格式 (key_id:secret)
        if ':' in token:
            parts = token.split(':', 1)
            if len(parts) == 2:
                key_id, secret = parts
                user = await get_user_from_api_key(key_id, secret, db)
                if user:
                    return user
        
        # 尝试作为JWT Token解析
        user = await get_user_from_jwt(token, db)
        if user:
            return user
    
    # 所有认证方式都失败
    raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    验证用户是否激活
    
    在get_current_user的基础上，额外检查用户是否被禁用
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 激活的用户对象
        
    Raises:
        HTTPException: 403 - 用户已被禁用
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用，请联系管理员"
        )
    return current_user


def require_role(*allowed_roles: str):
    """
    角色权限装饰器工厂
    
    创建一个依赖函数，检查用户是否具有指定的角色权限
    
    Args:
        *allowed_roles: 允许的角色列表（如"admin", "architect"）
        
    Returns:
        Callable: 依赖函数
        
    Example:
        @router.post("/rules")
        async def create_rule(
            current_user: User = Depends(require_role("admin", "architect"))
        ):
            ...
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        """检查用户角色"""
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一: {', '.join(allowed_roles)}"
            )
        return current_user
    
    return role_checker


# 预定义的角色依赖
require_admin = require_role(RoleEnum.ADMIN.value)
require_architect = require_role(RoleEnum.ADMIN.value, RoleEnum.ARCHITECT.value)
require_auditor = require_role(RoleEnum.ADMIN.value, RoleEnum.AUDITOR.value)


class RoleChecker:
    """
    角色检查器类（可选的实现方式）
    
    提供更灵活的角色检查功能，支持链式调用
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        """检查用户角色"""
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一: {', '.join(self.allowed_roles)}"
            )
        return current_user


# 使用示例：
# admin_only = RoleChecker([RoleEnum.ADMIN.value])
# architect_or_admin = RoleChecker([RoleEnum.ADMIN.value, RoleEnum.ARCHITECT.value])
