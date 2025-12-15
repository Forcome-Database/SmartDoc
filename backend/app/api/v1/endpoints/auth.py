"""
用户认证端点
实现登录、登出、获取当前用户信息、刷新Token等功能
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, verify_token
from app.core.dependencies import get_current_user, get_current_active_user
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录接口
    
    - 验证用户名和密码
    - 返回JWT访问令牌
    - 更新最后登录时间
    
    Args:
        login_data: 登录请求数据（用户名、密码）
        db: 数据库会话
        
    Returns:
        TokenResponse: 包含access_token和过期时间
        
    Raises:
        HTTPException: 401 - 用户名或密码错误
        HTTPException: 403 - 用户已被禁用
    """
    # 查询用户
    result = await db.execute(
        select(User).where(User.username == login_data.username)
    )
    user = result.scalar_one_or_none()
    
    # 验证用户存在且密码正确
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用，请联系管理员"
        )
    
    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    # 生成访问令牌
    access_token = create_access_token(
        data={
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout", summary="用户登出")
async def logout():
    """
    用户登出接口
    
    由于使用JWT无状态认证，登出操作主要在客户端完成（删除本地Token）
    服务端可以记录登出日志或将Token加入黑名单（可选实现）
    
    Returns:
        dict: 成功消息
    """
    # TODO: 可选实现 - 将Token加入Redis黑名单
    # await redis.setex(f"blacklist:{token}", settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, "1")
    
    return {"message": "登出成功"}


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前登录用户的信息
    
    Args:
        current_user: 当前用户（从Token中解析）
        
    Returns:
        UserResponse: 用户信息
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active
    )


@router.post("/refresh", response_model=TokenResponse, summary="刷新Token")
async def refresh_token(
    current_user: User = Depends(get_current_active_user)
):
    """
    刷新访问令牌
    
    使用当前有效的Token换取新的Token，延长会话时间
    
    Args:
        current_user: 当前用户（从Token中解析）
        
    Returns:
        TokenResponse: 新的访问令牌
    """
    # 生成新的访问令牌
    access_token = create_access_token(
        data={
            "sub": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
