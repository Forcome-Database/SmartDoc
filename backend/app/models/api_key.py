"""
API Key模型
定义API Key表结构
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class APIKey(Base):
    """API Key模型"""
    __tablename__ = "api_keys"

    id = Column(String(50), primary_key=True, comment="API Key ID")
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    key_id = Column(String(50), unique=True, nullable=False, index=True, comment="Key标识")
    secret_hash = Column(String(255), nullable=False, comment="Secret哈希")
    
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
    is_active = Column(Boolean, default=True, comment="是否激活")
    last_used_at = Column(DateTime, nullable=True, comment="最后使用时间")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关系
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey(id={self.id}, key_id={self.key_id}, user_id={self.user_id})>"
