# -*- coding: utf-8 -*-
"""
Webhook Schema定义
用于Webhook配置的请求和响应验证
"""
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class WebhookType(str, Enum):
    """Webhook类型枚举"""
    STANDARD = "standard"  # 标准HTTP Webhook
    KINGDEE = "kingdee"    # 金蝶K3 Cloud


class AuthType(str, Enum):
    """认证类型枚举"""
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"


class KingdeeSaveMode(str, Enum):
    """金蝶保存模式"""
    SMART = "smart"        # 智能模式：先Save，失败后Draft
    SAVE_ONLY = "save_only"  # 仅Save
    DRAFT_ONLY = "draft_only"  # 仅Draft


class KingdeeConfig(BaseModel):
    """
    金蝶K3 Cloud配置
    
    注意：金蝶连接信息（api_url, db_id, username, password）从环境变量读取，
    此处只配置保存模式等业务参数
    """
    save_mode: KingdeeSaveMode = Field(default=KingdeeSaveMode.SMART, description="保存模式")
    
    class Config:
        json_schema_extra = {
            "example": {
                "save_mode": "smart"
            }
        }


class WebhookCreate(BaseModel):
    """创建Webhook请求"""
    name: str = Field(..., description="系统名称", min_length=1, max_length=100)
    webhook_type: WebhookType = Field(default=WebhookType.STANDARD, description="Webhook类型")
    endpoint_url: Optional[str] = Field(default="", description="推送URL（标准类型必填，金蝶类型可留空）")
    auth_type: AuthType = Field(default=AuthType.NONE, description="认证方式（标准类型使用）")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="认证配置（标准类型使用）")
    secret_key: Optional[str] = Field(None, description="签名密钥")
    request_template: Optional[Dict[str, Any]] = Field(default={}, description="请求体模版（标准类型使用）")
    kingdee_config: Optional[KingdeeConfig] = Field(None, description="金蝶配置（金蝶类型使用）")
    is_active: bool = Field(default=True, description="是否激活")
    rule_ids: Optional[List[str]] = Field(default=None, description="关联的规则ID列表")

    @validator('endpoint_url', pre=True, always=True)
    def validate_url(cls, v, values):
        """验证URL格式"""
        webhook_type = values.get('webhook_type', WebhookType.STANDARD)
        # 金蝶类型不需要endpoint_url
        if webhook_type == WebhookType.KINGDEE:
            return v or ""
        # 标准类型必须有有效URL
        if not v or not str(v).startswith(('http://', 'https://')):
            raise ValueError('标准类型Webhook的URL必须以http://或https://开头')
        return v

    @validator('kingdee_config', pre=True, always=True)
    def validate_kingdee_config(cls, v, values):
        """验证金蝶配置"""
        webhook_type = values.get('webhook_type', WebhookType.STANDARD)
        if webhook_type == WebhookType.KINGDEE:
            # 金蝶类型，如果没有配置则使用默认值
            if v is None:
                return KingdeeConfig()
            if isinstance(v, dict):
                return KingdeeConfig(**v)
        return v

    @validator('auth_config')
    def validate_auth_config(cls, v, values):
        """验证认证配置"""
        webhook_type = values.get('webhook_type', WebhookType.STANDARD)
        # 金蝶类型不需要auth_config
        if webhook_type == WebhookType.KINGDEE:
            return v
        
        auth_type = values.get('auth_type')
        
        if auth_type == AuthType.BASIC:
            if not v or 'username' not in v or 'password' not in v:
                raise ValueError('Basic Auth需要提供username和password')
        elif auth_type == AuthType.BEARER:
            if not v or 'token' not in v:
                raise ValueError('Bearer Token需要提供token')
        elif auth_type == AuthType.API_KEY:
            if not v or 'key' not in v or 'value' not in v:
                raise ValueError('API Key需要提供key和value')
        
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "summary": "标准HTTP Webhook",
                    "value": {
                        "name": "下游业务系统A",
                        "webhook_type": "standard",
                        "endpoint_url": "https://api.example.com/webhook",
                        "auth_type": "bearer",
                        "auth_config": {"token": "your_bearer_token"},
                        "request_template": {
                            "task_id": "{{task_id}}",
                            "result": "{{result_json}}"
                        },
                        "is_active": True
                    }
                },
                {
                    "summary": "金蝶K3 Cloud",
                    "value": {
                        "name": "金蝶K3 Cloud",
                        "webhook_type": "kingdee",
                        "endpoint_url": "",
                        "kingdee_config": {
                            "api_url": "http://192.168.16.158/k3cloud/",
                            "db_id": "68f6f3dd8893a2",
                            "username": "administrator",
                            "password": "your_password",
                            "form_id": "PAEZ_PO",
                            "save_mode": "smart"
                        },
                        "is_active": True
                    }
                }
            ]
        }


class WebhookUpdate(BaseModel):
    """更新Webhook请求"""
    name: Optional[str] = Field(None, description="系统名称", min_length=1, max_length=100)
    endpoint_url: Optional[str] = Field(None, description="推送URL")
    auth_type: Optional[AuthType] = Field(None, description="认证方式")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="认证配置")
    secret_key: Optional[str] = Field(None, description="签名密钥")
    request_template: Optional[Dict[str, Any]] = Field(None, description="请求体模版")
    is_active: Optional[bool] = Field(None, description="是否激活")
    rule_ids: Optional[List[str]] = Field(None, description="关联的规则ID列表")

    @validator('endpoint_url')
    def validate_url(cls, v):
        """验证URL格式"""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URL必须以http://或https://开头')
        return v


class WebhookListItem(BaseModel):
    """Webhook列表项"""
    id: str = Field(..., description="Webhook ID")
    name: str = Field(..., description="系统名称")
    webhook_type: WebhookType = Field(default=WebhookType.STANDARD, description="Webhook类型")
    endpoint_url: str = Field(default="", description="推送URL")
    auth_type: AuthType = Field(default=AuthType.NONE, description="认证方式")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    rule_count: int = Field(default=0, description="关联规则数量")

    class Config:
        from_attributes = True


class WebhookDetail(BaseModel):
    """Webhook详情"""
    id: str = Field(..., description="Webhook ID")
    name: str = Field(..., description="系统名称")
    webhook_type: WebhookType = Field(default=WebhookType.STANDARD, description="Webhook类型")
    endpoint_url: str = Field(default="", description="推送URL")
    auth_type: AuthType = Field(default=AuthType.NONE, description="认证方式")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="认证配置（敏感信息已脱敏）")
    secret_key_masked: Optional[str] = Field(None, description="签名密钥（已遮蔽）")
    request_template: Optional[Dict[str, Any]] = Field(default=None, description="请求体模版")
    kingdee_config: Optional[Dict[str, Any]] = Field(None, description="金蝶配置（敏感信息已脱敏）")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    rule_count: int = Field(default=0, description="关联规则数量")
    push_count: int = Field(default=0, description="推送次数")
    rule_ids: List[str] = Field(default_factory=list, description="关联的规则ID列表")

    class Config:
        from_attributes = True


class WebhookListResponse(BaseModel):
    """Webhook列表响应"""
    items: List[WebhookListItem] = Field(..., description="Webhook列表")
    total: int = Field(..., description="总数")


class WebhookResponse(BaseModel):
    """Webhook操作响应"""
    id: str = Field(..., description="Webhook ID")
    message: str = Field(..., description="操作结果消息")


class WebhookTestRequest(BaseModel):
    """Webhook测试请求"""
    mock_data: Optional[Dict[str, Any]] = Field(None, description="Mock数据")

    class Config:
        json_schema_extra = {
            "example": {
                "mock_data": {
                    "task_id": "T_20251214_0001",
                    "result": {"field1": "value1"},
                    "file_url": "https://example.com/file.pdf"
                }
            }
        }


class WebhookTestResponse(BaseModel):
    """Webhook测试响应"""
    success: bool = Field(..., description="测试是否成功")
    status_code: Optional[int] = Field(None, description="HTTP状态码")
    response_headers: Optional[Dict[str, str]] = Field(None, description="响应头")
    response_body: Optional[str] = Field(None, description="响应体")
    error: Optional[str] = Field(None, description="错误信息")
    duration_ms: int = Field(..., description="请求耗时（毫秒）")


class RuleWebhookAssociation(BaseModel):
    """规则与Webhook关联请求"""
    webhook_ids: List[str] = Field(..., description="Webhook ID列表")

    class Config:
        json_schema_extra = {
            "example": {
                "webhook_ids": ["webhook_id_1", "webhook_id_2"]
            }
        }
