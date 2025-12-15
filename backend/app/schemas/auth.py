"""
认证相关的Pydantic schemas
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒


class UserResponse(BaseModel):
    """用户信息响应"""
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: Optional[str] = None
