"""
审计日志模型
定义审计日志表结构
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, BigInteger
from sqlalchemy.orm import relationship
from app.core.database import Base


class AuditLog(Base):
    """审计日志模型"""
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="日志ID")
    user_id = Column(String(50), ForeignKey("users.id"), nullable=True, index=True, comment="用户ID")
    action_type = Column(String(50), nullable=False, index=True, comment="操作类型")
    resource_type = Column(String(50), nullable=False, index=True, comment="资源类型")
    resource_id = Column(String(50), nullable=True, comment="资源ID")
    
    changes = Column(JSON, nullable=True, comment="变更内容")
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(String(255), nullable=True, comment="User Agent")
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment="创建时间")

    # 关系
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action_type={self.action_type})>"
