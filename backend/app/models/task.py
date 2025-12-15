"""
任务模型
定义任务表结构和任务状态枚举
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON, Numeric, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base


class TaskStatus(str, Enum):
    """任务状态枚举"""
    QUEUED = "queued"  # 排队中
    PROCESSING = "processing"  # 处理中
    PENDING_AUDIT = "pending_audit"  # 待审核
    COMPLETED = "completed"  # 已完成
    REJECTED = "rejected"  # 已驳回
    PUSHING = "pushing"  # 推送中
    PUSH_SUCCESS = "push_success"  # 推送成功
    PUSH_FAILED = "push_failed"  # 推送失败
    FAILED = "failed"  # 处理失败


class Task(Base):
    """任务模型"""
    __tablename__ = "tasks"

    id = Column(String(50), primary_key=True, comment="任务ID")
    file_name = Column(String(255), nullable=False, comment="文件名")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    file_hash = Column(String(64), nullable=False, index=True, comment="文件哈希")
    page_count = Column(Integer, default=1, comment="页数")
    
    rule_id = Column(String(50), ForeignKey("rules.id"), nullable=False, index=True, comment="规则ID")
    rule_version = Column(String(20), nullable=False, comment="规则版本")
    
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.QUEUED, index=True, comment="任务状态")
    is_instant = Column(Boolean, default=False, comment="是否秒传")
    
    # OCR结果
    ocr_text = Column(Text, nullable=True, comment="合并后的全文")
    ocr_result = Column(JSON, nullable=True, comment="完整OCR结果（含坐标）")
    
    # 提取结果
    extracted_data = Column(JSON, nullable=True, comment="提取的数据")
    confidence_scores = Column(JSON, nullable=True, comment="字段置信度")
    
    # 审核信息
    audit_reasons = Column(JSON, nullable=True, comment="审核原因列表")
    auditor_id = Column(String(50), ForeignKey("users.id"), nullable=True, comment="审核人ID")
    audited_at = Column(DateTime, nullable=True, comment="审核时间")
    
    # LLM信息
    llm_token_count = Column(Integer, default=0, comment="LLM Token消耗")
    llm_cost = Column(Numeric(10, 4), default=0, comment="LLM费用")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment="创建时间")
    started_at = Column(DateTime, nullable=True, comment="开始处理时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    
    # 错误信息
    error_message = Column(Text, nullable=True, comment="错误信息")

    # 关系
    rule = relationship("Rule", back_populates="tasks")
    auditor = relationship("User", back_populates="audited_tasks", foreign_keys=[auditor_id])
    push_logs = relationship("PushLog", back_populates="task", cascade="all, delete-orphan")
    pipeline_executions = relationship("PipelineExecution", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task(id={self.id}, file_name={self.file_name}, status={self.status})>"
