"""
API Key Schema
定义API Key相关的请求和响应模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ============================================================================
# API Key响应模型
# ============================================================================

class APIKeyResponse(BaseModel):
    """API Key响应模型（列表展示）"""
    id: str = Field(..., description="API Key ID")
    key_id: str = Field(..., description="Key标识")
    masked_secret: str = Field(..., description="遮蔽后的Secret（前8位+***）")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    is_active: bool = Field(..., description="是否激活")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    """API Key创建响应模型（包含完整secret，仅此一次）"""
    id: str = Field(..., description="API Key ID")
    key_id: str = Field(..., description="Key标识")
    secret: str = Field(..., description="完整的Secret（仅此一次显示）")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


# ============================================================================
# API Key请求模型
# ============================================================================

class APIKeyCreateRequest(BaseModel):
    """API Key创建请求模型"""
    expires_days: Optional[int] = Field(
        None,
        description="有效期（天数），如30、90、365，不填则永久有效",
        ge=1,
        le=3650
    )


class APIKeyListResponse(BaseModel):
    """API Key列表响应模型"""
    items: list[APIKeyResponse] = Field(..., description="API Key列表")
    total: int = Field(..., description="总数")


# ============================================================================
# API Key操作响应
# ============================================================================

class APIKeyRevokeResponse(BaseModel):
    """API Key撤销响应模型"""
    message: str = Field(..., description="操作结果消息")
    key_id: str = Field(..., description="被撤销的Key标识")

