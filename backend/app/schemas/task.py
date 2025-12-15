# -*- coding: utf-8 -*-
"""
任务相关的Pydantic Schema定义
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态枚举"""
    QUEUED = "queued"
    PROCESSING = "processing"
    PENDING_AUDIT = "pending_audit"
    COMPLETED = "completed"
    REJECTED = "rejected"
    PUSHING = "pushing"
    PUSH_SUCCESS = "push_success"
    PUSH_FAILED = "push_failed"
    FAILED = "failed"


class TaskListQuery(BaseModel):
    """任务列表查询参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    status: Optional[TaskStatus] = Field(default=None, description="任务状态筛选")
    rule_id: Optional[str] = Field(default=None, description="规则ID筛选")
    task_id: Optional[str] = Field(default=None, description="任务ID搜索")
    file_name: Optional[str] = Field(default=None, description="文件名搜索")
    start_date: Optional[datetime] = Field(default=None, description="开始日期")
    end_date: Optional[datetime] = Field(default=None, description="结束日期")
    sort_by: Optional[str] = Field(default="created_at", description="排序字段")
    sort_order: Optional[str] = Field(default="desc", description="排序方向: asc/desc")


class TaskFlowStatus(BaseModel):
    """任务流转状态"""
    ocr_status: str = Field(description="OCR状态: pending/processing/completed/failed")
    ocr_completed_at: Optional[datetime] = Field(default=None, description="OCR完成时间")
    pipeline_status: Optional[str] = Field(default=None, description="管道状态: pending/running/success/failed/skipped")
    pipeline_completed_at: Optional[datetime] = Field(default=None, description="管道完成时间")
    push_status: Optional[str] = Field(default=None, description="推送状态: pending/pushing/success/failed/skipped")
    push_completed_at: Optional[datetime] = Field(default=None, description="推送完成时间")


class TaskListItem(BaseModel):
    """任务列表项"""
    id: str = Field(description="任务ID")
    file_name: str = Field(description="文件名")
    page_count: int = Field(description="页数")
    rule_id: str = Field(description="规则ID")
    rule_name: Optional[str] = Field(default=None, description="规则名称")
    rule_version: str = Field(description="规则版本")
    status: TaskStatus = Field(description="任务状态")
    is_instant: bool = Field(description="是否秒传")
    confidence_scores: Optional[Dict[str, float]] = Field(default=None, description="置信度分数")
    avg_confidence: Optional[float] = Field(default=None, description="平均置信度")
    audit_reasons: Optional[List[Dict[str, Any]]] = Field(default=None, description="审核原因列表")
    created_at: datetime = Field(description="创建时间")
    started_at: Optional[datetime] = Field(default=None, description="开始处理时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    duration_seconds: Optional[int] = Field(default=None, description="处理耗时(秒)")
    # 流转状态
    flow_status: Optional[TaskFlowStatus] = Field(default=None, description="流转状态")

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """任务列表响应"""
    items: List[TaskListItem] = Field(description="任务列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    total_pages: int = Field(description="总页数")


class PushLogDetail(BaseModel):
    """推送日志详情"""
    id: int = Field(description="日志ID")
    webhook_id: str = Field(description="Webhook ID")
    webhook_name: Optional[str] = Field(default=None, description="Webhook名称")
    http_status: Optional[int] = Field(default=None, description="HTTP状态码")
    request_headers: Optional[Dict[str, Any]] = Field(default=None, description="请求头")
    request_body: Optional[str] = Field(default=None, description="请求体")
    response_headers: Optional[Dict[str, Any]] = Field(default=None, description="响应头")
    response_body: Optional[str] = Field(default=None, description="响应体")
    duration_ms: Optional[int] = Field(default=None, description="耗时(毫秒)")
    retry_count: int = Field(default=0, description="重试次数")
    created_at: datetime = Field(description="创建时间")

    class Config:
        from_attributes = True


class PipelineExecutionDetail(BaseModel):
    """管道执行详情"""
    id: str = Field(description="执行ID")
    pipeline_id: str = Field(description="管道ID")
    pipeline_name: Optional[str] = Field(default=None, description="管道名称")
    status: str = Field(description="执行状态: pending/running/success/failed")
    retry_count: int = Field(default=0, description="重试次数")
    input_data: Optional[Dict[str, Any]] = Field(default=None, description="输入数据")
    output_data: Optional[Dict[str, Any]] = Field(default=None, description="输出数据")
    stdout: Optional[str] = Field(default=None, description="标准输出")
    stderr: Optional[str] = Field(default=None, description="标准错误")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    duration_ms: Optional[int] = Field(default=None, description="耗时(毫秒)")
    created_at: datetime = Field(description="创建时间")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")

    class Config:
        from_attributes = True


class TaskDetail(BaseModel):
    """任务详情"""
    id: str = Field(description="任务ID")
    file_name: str = Field(description="文件名")
    file_path: str = Field(description="文件路径")
    file_hash: str = Field(description="文件哈希")
    page_count: int = Field(description="页数")
    rule_id: str = Field(description="规则ID")
    rule_name: Optional[str] = Field(default=None, description="规则名称")
    rule_version: str = Field(description="规则版本")
    status: TaskStatus = Field(description="任务状态")
    is_instant: bool = Field(description="是否秒传")
    
    # OCR结果
    ocr_text: Optional[str] = Field(default=None, description="OCR合并文本")
    ocr_result: Optional[Dict[str, Any]] = Field(default=None, description="OCR完整结果")
    
    # 提取结果
    extracted_data: Optional[Dict[str, Any]] = Field(default=None, description="提取数据")
    confidence_scores: Optional[Dict[str, float]] = Field(default=None, description="置信度分数")
    
    # 审核信息
    audit_reasons: Optional[List[Dict[str, Any]]] = Field(default=None, description="审核原因")
    auditor_id: Optional[str] = Field(default=None, description="审核员ID")
    auditor_name: Optional[str] = Field(default=None, description="审核员姓名")
    audited_at: Optional[datetime] = Field(default=None, description="审核时间")
    
    # LLM信息
    llm_token_count: int = Field(default=0, description="LLM Token消耗")
    llm_cost: float = Field(default=0.0, description="LLM成本")
    
    # 时间戳
    created_at: datetime = Field(description="创建时间")
    started_at: Optional[datetime] = Field(default=None, description="开始处理时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    
    # 推送日志
    push_logs: List[PushLogDetail] = Field(default_factory=list, description="推送日志")
    
    # 管道执行记录
    pipeline_executions: List[PipelineExecutionDetail] = Field(default_factory=list, description="管道执行记录")
    
    # 流转状态
    flow_status: Optional[TaskFlowStatus] = Field(default=None, description="流转状态")

    class Config:
        from_attributes = True


class TaskStatusUpdate(BaseModel):
    """任务状态更新请求"""
    status: TaskStatus = Field(description="新状态")
    extracted_data: Optional[Dict[str, Any]] = Field(default=None, description="修正后的提取数据")
    audit_comment: Optional[str] = Field(default=None, description="审核备注")


class TaskExportQuery(BaseModel):
    """任务导出查询参数"""
    status: Optional[TaskStatus] = Field(default=None, description="任务状态筛选")
    rule_id: Optional[str] = Field(default=None, description="规则ID筛选")
    start_date: Optional[datetime] = Field(default=None, description="开始日期")
    end_date: Optional[datetime] = Field(default=None, description="结束日期")
    format: str = Field(default="csv", description="导出格式: csv/excel")


class TaskExportResponse(BaseModel):
    """任务导出响应"""
    task_id: Optional[str] = Field(default=None, description="异步导出任务ID")
    download_url: Optional[str] = Field(default=None, description="下载链接(同步导出)")
    message: str = Field(description="提示信息")
