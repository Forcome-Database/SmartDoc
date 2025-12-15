"""
系统配置Schema
定义系统配置相关的请求和响应模型
"""
from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime


class SystemConfigBase(BaseModel):
    """系统配置基础模型"""
    key: str = Field(..., description="配置键")
    value: Any = Field(..., description="配置值（JSON格式）")
    description: Optional[str] = Field(None, description="配置描述")


class SystemConfigCreate(SystemConfigBase):
    """创建系统配置请求"""
    pass


class SystemConfigUpdate(BaseModel):
    """更新系统配置请求"""
    value: Any = Field(..., description="配置值（JSON格式）")
    description: Optional[str] = Field(None, description="配置描述")


class SystemConfigResponse(SystemConfigBase):
    """系统配置响应"""
    updated_by: Optional[str] = Field(None, description="更新人ID")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class SystemConfigListResponse(BaseModel):
    """系统配置列表响应"""
    configs: list[SystemConfigResponse] = Field(..., description="配置列表")
    total: int = Field(..., description="总数")


class RetentionConfigResponse(BaseModel):
    """数据生命周期配置响应"""
    file_retention_days: int = Field(..., description="文件留存期（天）")
    data_retention_days: int = Field(..., description="数据留存期（天，0表示永久保留）")
    next_cleanup_time: Optional[str] = Field(None, description="下次清理时间")


class RetentionConfigUpdate(BaseModel):
    """数据生命周期配置更新请求"""
    file_retention_days: int = Field(..., ge=1, le=365, description="文件留存期（天，1-365）")
    data_retention_days: int = Field(..., ge=0, le=3650, description="数据留存期（天，0表示永久保留，最大3650天）")
