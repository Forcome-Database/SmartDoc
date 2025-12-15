"""
数据处理管道模型
定义管道配置和执行记录
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum
from app.core.database import Base
import uuid


def generate_pipeline_id() -> str:
    """生成管道ID"""
    return f"PL_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"


def generate_execution_id() -> str:
    """生成执行记录ID"""
    return f"PE_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6].upper()}"


class PipelineStatus(str, Enum):
    """管道状态"""
    DRAFT = "draft"          # 草稿
    ACTIVE = "active"        # 激活
    INACTIVE = "inactive"    # 停用


class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 执行中
    SUCCESS = "success"      # 成功
    FAILED = "failed"        # 失败
    TIMEOUT = "timeout"      # 超时


class Pipeline(Base):
    """数据处理管道模型"""
    __tablename__ = "pipelines"

    id = Column(String(50), primary_key=True,
                default=generate_pipeline_id, comment="管道ID")
    name = Column(String(100), nullable=False, comment="管道名称")
    description = Column(Text, nullable=True, comment="管道描述")

    # 关联规则（一个规则可以有一个管道）
    rule_id = Column(String(50), ForeignKey("rules.id"),
                     nullable=False, unique=True, index=True, comment="规则ID")

    # 管道配置
    status = Column(String(20), default="draft", comment="管道状态")

    # Python脚本内容
    script_content = Column(Text, nullable=False, comment="Python脚本内容")

    # 依赖包配置 (requirements.txt 内容)
    requirements = Column(Text, nullable=True, comment="依赖包列表，每行一个包")

    # 执行配置
    timeout_seconds = Column(Integer, default=300, comment="执行超时时间（秒）")
    max_retries = Column(Integer, default=1, comment="最大重试次数")
    memory_limit_mb = Column(Integer, default=512, comment="内存限制（MB）")

    # 环境变量（JSON格式，敏感信息加密存储）
    env_variables = Column(JSON, nullable=True, comment="环境变量")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, comment="更新时间")
    created_by = Column(String(50), ForeignKey("users.id"),
                        nullable=True, comment="创建人ID")

    # 关系
    rule = relationship("Rule", back_populates="pipeline")
    executions = relationship(
        "PipelineExecution", back_populates="pipeline", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Pipeline(id={self.id}, name={self.name}, status={self.status})>"


class PipelineExecution(Base):
    """管道执行记录"""
    __tablename__ = "pipeline_executions"

    id = Column(String(50), primary_key=True,
                default=generate_execution_id, comment="执行ID")

    # 关联
    pipeline_id = Column(String(50), ForeignKey(
        "pipelines.id"), nullable=False, index=True, comment="管道ID")
    task_id = Column(String(50), ForeignKey("tasks.id"),
                     nullable=False, index=True, comment="任务ID")

    # 执行状态
    status = Column(String(20), default="pending", index=True, comment="执行状态")
    retry_count = Column(Integer, default=0, comment="重试次数")

    # 输入输出数据
    input_data = Column(JSON, nullable=True, comment="输入数据（提取结果）")
    output_data = Column(JSON, nullable=True, comment="输出数据（处理后结果）")

    # 执行日志
    stdout = Column(Text, nullable=True, comment="标准输出")
    stderr = Column(Text, nullable=True, comment="错误输出")
    error_message = Column(Text, nullable=True, comment="错误信息")

    # 执行统计
    duration_ms = Column(Integer, nullable=True, comment="执行耗时（毫秒）")
    memory_used_mb = Column(Integer, nullable=True, comment="内存使用（MB）")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow,
                        index=True, comment="创建时间")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    # 关系
    pipeline = relationship("Pipeline", back_populates="executions")
    task = relationship("Task", back_populates="pipeline_executions")

    def __repr__(self):
        return f"<PipelineExecution(id={self.id}, status={self.status})>"
