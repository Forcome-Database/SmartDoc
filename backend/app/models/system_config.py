"""
系统配置模型
定义系统配置表结构
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class SystemConfig(Base):
    """系统配置模型"""
    __tablename__ = "system_configs"

    key = Column(String(100), primary_key=True, comment="配置键")
    value = Column(JSON, nullable=False, comment="配置值")
    description = Column(String(255), nullable=True, comment="配置描述")
    
    updated_by = Column(String(50), ForeignKey("users.id"), nullable=True, comment="更新人ID")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    updater = relationship("User", foreign_keys=[updated_by])

    def __repr__(self):
        return f"<SystemConfig(key={self.key}, description={self.description})>"
