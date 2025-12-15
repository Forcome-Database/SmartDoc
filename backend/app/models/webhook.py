"""
Webhook模型
定义Webhook配置表和规则关联表
支持标准HTTP Webhook和金蝶K3 Cloud集成
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Integer, Table, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class WebhookType(str, Enum):
    """Webhook类型枚举"""
    STANDARD = "standard"  # 标准HTTP Webhook
    KINGDEE = "kingdee"    # 金蝶K3 Cloud


class AuthType(str, Enum):
    """认证类型枚举"""
    NONE = "none"  # 无认证
    BASIC = "basic"  # Basic Auth
    BEARER = "bearer"  # Bearer Token
    API_KEY = "api_key"  # API Key


# 规则与Webhook多对多关联表
rule_webhooks = Table(
    'rule_webhooks',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True, comment="关联ID"),
    Column('rule_id', String(50), ForeignKey('rules.id', ondelete='CASCADE'), nullable=False, comment="规则ID"),
    Column('webhook_id', String(50), ForeignKey('webhooks.id', ondelete='CASCADE'), nullable=False, comment="Webhook ID"),
    Column('created_at', DateTime, default=datetime.utcnow, comment="创建时间")
)


class Webhook(Base):
    """Webhook配置模型"""
    __tablename__ = "webhooks"

    id = Column(String(50), primary_key=True, comment="Webhook ID")
    name = Column(String(100), nullable=False, comment="系统名称")
    webhook_type = Column(SQLEnum(WebhookType), default=WebhookType.STANDARD, comment="Webhook类型")
    endpoint_url = Column(String(500), nullable=True, comment="推送URL（标准类型必填）")
    auth_type = Column(SQLEnum(AuthType), default=AuthType.NONE, comment="认证方式（标准类型使用）")
    auth_config = Column(JSON, nullable=True, comment="认证配置（标准类型使用）")
    secret_key = Column(String(255), nullable=True, comment="签名密钥（加密存储）")
    request_template = Column(JSON, nullable=True, comment="请求体模版（标准类型使用）")
    kingdee_config = Column(JSON, nullable=True, comment="金蝶配置（金蝶类型使用）")
    is_active = Column(Boolean, default=True, index=True, comment="是否激活")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    rules = relationship("Rule", secondary=rule_webhooks, back_populates="webhooks")
    push_logs = relationship("PushLog", back_populates="webhook")

    def __repr__(self):
        return f"<Webhook(id={self.id}, name={self.name}, endpoint_url={self.endpoint_url})>"
