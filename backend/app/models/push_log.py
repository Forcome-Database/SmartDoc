"""
推送日志模型
定义推送日志表结构
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Text, BigInteger
from sqlalchemy.orm import relationship
from app.core.database import Base


class PushLog(Base):
    """推送日志模型"""
    __tablename__ = "push_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="日志ID")
    task_id = Column(String(50), ForeignKey("tasks.id"), nullable=False, index=True, comment="任务ID")
    webhook_id = Column(String(50), ForeignKey("webhooks.id"), nullable=False, index=True, comment="Webhook ID")
    
    http_status = Column(Integer, nullable=True, comment="HTTP状态码")
    request_headers = Column(JSON, nullable=True, comment="请求头")
    request_body = Column(Text, nullable=True, comment="请求体")
    response_headers = Column(JSON, nullable=True, comment="响应头")
    response_body = Column(Text, nullable=True, comment="响应体")
    
    duration_ms = Column(Integer, nullable=True, comment="耗时（毫秒）")
    retry_count = Column(Integer, default=0, comment="重试次数")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment="创建时间")

    # 关系
    task = relationship("Task", back_populates="push_logs")
    webhook = relationship("Webhook", back_populates="push_logs")

    def __repr__(self):
        return f"<PushLog(id={self.id}, task_id={self.task_id}, http_status={self.http_status})>"
