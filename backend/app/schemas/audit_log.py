"""
审计日志Schema
定义审计日志的请求和响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class AuditLogBase(BaseModel):
    """审计日志基础模型"""
    user_id: Optional[str] = Field(None, description="用户ID")
    action_type: str = Field(..., description="操作类型")
    resource_type: str = Field(..., description="资源类型")
    resource_id: Optional[str] = Field(None, description="资源ID")
    changes: Optional[dict] = Field(None, description="变更内容")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="User Agent")


class AuditLogCreate(AuditLogBase):
    """创建审计日志请求模型"""
    pass


class AuditLogResponse(AuditLogBase):
    """审计日志响应模型"""
    id: int = Field(..., description="日志ID")
    created_at: datetime = Field(..., description="创建时间")
    username: Optional[str] = Field(None, description="用户名")

    class Config:
        from_attributes = True


class PaginatedAuditLogResponse(BaseModel):
    """分页审计日志响应"""
    code: int = Field(200, description="响应码")
    message: str = Field("success", description="响应消息")
    data: dict = Field(..., description="响应数据")

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "success",
                "data": {
                    "items": [
                        {
                            "id": 1,
                            "user_id": "U_001",
                            "username": "admin",
                            "action_type": "login",
                            "resource_type": "auth",
                            "resource_id": None,
                            "changes": None,
                            "ip_address": "192.168.1.1",
                            "user_agent": "Mozilla/5.0",
                            "created_at": "2025-12-14T10:00:00"
                        }
                    ],
                    "total": 100,
                    "page": 1,
                    "page_size": 20,
                    "total_pages": 5
                }
            }
        }


class AuditLogExportResponse(BaseModel):
    """审计日志导出响应"""
    code: int = Field(200, description="响应码")
    message: str = Field("success", description="响应消息")
    data: dict = Field(..., description="响应数据")

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "success",
                "data": {
                    "file_url": "/exports/audit_logs_20251214.csv",
                    "file_name": "audit_logs_20251214.csv",
                    "total_records": 1000
                }
            }
        }
