"""
用户管理相关的Pydantic schemas
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from app.models.user import RoleEnum


class UserBase(BaseModel):
    """用户基础信息"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    role: RoleEnum = Field(..., description="用户角色")


class UserCreate(UserBase):
    """创建用户请求"""
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    
    @validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        if len(v) < 6:
            raise ValueError('密码长度至少为6个字符')
        return v


class UserUpdate(BaseModel):
    """更新用户请求"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    role: Optional[RoleEnum] = Field(None, description="用户角色")
    old_password: Optional[str] = Field(None, description="旧密码（修改密码时必填）")
    new_password: Optional[str] = Field(None, min_length=6, max_length=50, description="新密码")
    
    @validator('new_password')
    def validate_new_password(cls, v, values):
        """验证新密码"""
        if v is not None:
            if len(v) < 6:
                raise ValueError('密码长度至少为6个字符')
            if 'old_password' not in values or values['old_password'] is None:
                raise ValueError('修改密码时必须提供旧密码')
        return v


class UserStatusUpdate(BaseModel):
    """用户状态更新请求"""
    is_active: bool = Field(..., description="是否激活")


class UserListResponse(BaseModel):
    """用户列表响应"""
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserDetailResponse(UserListResponse):
    """用户详情响应"""
    pass


class UserListRequest(BaseModel):
    """用户列表查询请求"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    username: Optional[str] = Field(None, description="用户名筛选")
    email: Optional[str] = Field(None, description="邮箱筛选")
    role: Optional[RoleEnum] = Field(None, description="角色筛选")
    is_active: Optional[bool] = Field(None, description="状态筛选")


class PaginatedUserResponse(BaseModel):
    """分页用户列表响应"""
    items: list[UserListResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
