"""
用户模型
定义用户表结构和角色枚举
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base


class RoleEnum(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"  # 超级管理员
    ARCHITECT = "architect"  # 规则架构师
    AUDITOR = "auditor"  # 业务审核员
    VISITOR = "visitor"  # API访客


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, comment="用户ID")
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, index=True, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    role = Column(SQLEnum(RoleEnum), nullable=False, comment="用户角色")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")

    # 关系
    created_rules = relationship("Rule", back_populates="creator", foreign_keys="Rule.created_by")
    audited_tasks = relationship("Task", back_populates="auditor", foreign_keys="Task.auditor_id")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
