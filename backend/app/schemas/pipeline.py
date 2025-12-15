"""
数据处理管道相关的Pydantic模型
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.pipeline import PipelineStatus, ExecutionStatus


# ========== Pipeline Schemas ==========

class PipelineCreate(BaseModel):
    """创建管道请求"""
    name: str = Field(..., min_length=1, max_length=100, description="管道名称")
    description: Optional[str] = Field(None, description="管道描述")
    rule_id: str = Field(..., description="关联的规则ID")
    script_content: str = Field(..., min_length=1, description="Python脚本内容")
    requirements: Optional[str] = Field(None, description="依赖包列表")
    timeout_seconds: Optional[int] = Field(300, ge=10, le=3600, description="超时时间")
    max_retries: Optional[int] = Field(1, ge=0, le=5, description="最大重试次数")
    memory_limit_mb: Optional[int] = Field(512, ge=128, le=4096, description="内存限制")
    env_variables: Optional[Dict[str, str]] = Field(None, description="环境变量")


class PipelineUpdate(BaseModel):
    """更新管道请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    script_content: Optional[str] = Field(None, min_length=1)
    requirements: Optional[str] = None
    timeout_seconds: Optional[int] = Field(None, ge=10, le=3600)
    max_retries: Optional[int] = Field(None, ge=0, le=5)
    memory_limit_mb: Optional[int] = Field(None, ge=128, le=4096)
    env_variables: Optional[Dict[str, str]] = None


class PipelineResponse(BaseModel):
    """管道响应"""
    id: str
    name: str
    description: Optional[str]
    rule_id: str
    status: PipelineStatus
    script_content: str
    requirements: Optional[str]
    timeout_seconds: int
    max_retries: int
    memory_limit_mb: int
    env_variables: Optional[Dict[str, str]]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


class PipelineListResponse(BaseModel):
    """管道列表响应"""
    items: List[PipelineResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ========== Test Schemas ==========

class PipelineTestRequest(BaseModel):
    """测试管道请求"""
    test_data: Optional[Dict[str, Any]] = Field(
        default={},
        description="测试用的提取数据"
    )
    ocr_text: Optional[str] = Field(
        default="",
        description="测试用的OCR文本"
    )


class PipelineTestResponse(BaseModel):
    """测试管道响应"""
    success: bool
    output_data: Optional[Dict[str, Any]]
    stdout: str
    stderr: str
    error_message: Optional[str]


# ========== Execution Schemas ==========

class ExecutionDetail(BaseModel):
    """执行记录详情"""
    id: str
    pipeline_id: str
    task_id: str
    status: ExecutionStatus
    retry_count: int
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    stdout: Optional[str]
    stderr: Optional[str]
    error_message: Optional[str]
    duration_ms: Optional[int]
    memory_used_mb: Optional[int]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ExecutionListResponse(BaseModel):
    """执行记录列表响应"""
    items: List[ExecutionDetail]
    total: int
    page: int
    page_size: int
    total_pages: int
