"""
规则模型
定义规则表和规则版本表结构
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base


class RuleStatus(str, Enum):
    """规则状态枚举"""
    DRAFT = "draft"  # 草稿
    PUBLISHED = "published"  # 已发布
    ARCHIVED = "archived"  # 已归档


class Rule(Base):
    """规则模型"""
    __tablename__ = "rules"

    id = Column(String(50), primary_key=True, comment="规则ID")
    name = Column(String(100), nullable=False, comment="规则名称")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="规则编码")
    document_type = Column(String(50), index=True, comment="文档类型")
    current_version = Column(String(20), comment="当前发布版本")
    
    created_by = Column(String(50), ForeignKey("users.id"), comment="创建人ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    creator = relationship("User", back_populates="created_rules", foreign_keys=[created_by])
    versions = relationship("RuleVersion", back_populates="rule", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="rule")
    webhooks = relationship("Webhook", secondary="rule_webhooks", back_populates="rules")
    pipeline = relationship("Pipeline", back_populates="rule", uselist=False)

    def __repr__(self):
        return f"<Rule(id={self.id}, code={self.code}, name={self.name})>"


class RuleVersion(Base):
    """规则版本模型"""
    __tablename__ = "rule_versions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="版本ID")
    rule_id = Column(String(50), ForeignKey("rules.id", ondelete="CASCADE"), nullable=False, comment="规则ID")
    version = Column(String(20), nullable=False, comment="版本号")
    status = Column(SQLEnum(RuleStatus), default=RuleStatus.DRAFT, index=True, comment="版本状态")
    
    # 配置内容（JSON格式）
    config = Column(JSON, nullable=False, comment="规则配置")
    
    published_at = Column(DateTime, nullable=True, comment="发布时间")
    published_by = Column(String(50), ForeignKey("users.id"), nullable=True, comment="发布人ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关系
    rule = relationship("Rule", back_populates="versions")
    publisher = relationship("User", foreign_keys=[published_by])

    def __repr__(self):
        return f"<RuleVersion(id={self.id}, rule_id={self.rule_id}, version={self.version}, status={self.status})>"
