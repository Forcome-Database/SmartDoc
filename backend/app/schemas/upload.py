"""
文件上传相关的Schema定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class UploadResponse(BaseModel):
    """单文件上传响应"""
    task_id: str = Field(..., description="任务ID")
    is_instant: bool = Field(..., description="是否秒传")
    status: str = Field(..., description="任务状态")
    estimated_wait_seconds: int = Field(..., description="预估等待时间（秒）")
    message: Optional[str] = Field(None, description="提示信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "T_20251214_0001",
                "is_instant": False,
                "status": "queued",
                "estimated_wait_seconds": 15,
                "message": "文件已上传，正在处理中"
            }
        }


class TaskDetailResponse(BaseModel):
    """任务详情响应"""
    task_id: str
    file_name: str
    page_count: int
    rule_id: str
    rule_version: str
    status: str
    is_instant: bool
    created_at: str
    completed_at: Optional[str] = None
    extracted_data: Optional[dict] = None
    confidence_scores: Optional[dict] = None
    audit_reasons: Optional[list] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "T_20251214_0001",
                "file_name": "invoice.pdf",
                "page_count": 3,
                "rule_id": "RULE001",
                "rule_version": "V1.0",
                "status": "completed",
                "is_instant": False,
                "created_at": "2025-12-14T10:30:00",
                "completed_at": "2025-12-14T10:30:15",
                "extracted_data": {"invoice_no": "INV-001", "amount": 1000.50},
                "confidence_scores": {"invoice_no": 95, "amount": 88}
            }
        }


class UploadResultItem(BaseModel):
    """单个文件上传结果"""
    file_name: str = Field(..., description="文件名")
    task_id: Optional[str] = Field(None, description="任务ID，失败时为空")
    is_instant: bool = Field(False, description="是否秒传")
    status: str = Field(..., description="状态: queued/completed/failed")
    estimated_wait_seconds: int = Field(0, description="预估等待时间（秒）")
    error: Optional[str] = Field(None, description="错误信息，成功时为空")
    # 内部使用：待发布到队列的任务数据，序列化时排除
    pending_publish: Optional[dict] = Field(None, exclude=True)


class BatchUploadResponse(BaseModel):
    """批量上传响应"""
    total: int = Field(..., description="总文件数")
    success_count: int = Field(..., description="成功数")
    failed_count: int = Field(..., description="失败数")
    results: List[UploadResultItem] = Field(..., description="每个文件的上传结果")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 3,
                "success_count": 2,
                "failed_count": 1,
                "results": [
                    {"file_name": "doc1.pdf", "task_id": "T_20251215_001", "is_instant": False, "status": "queued", "estimated_wait_seconds": 10},
                    {"file_name": "doc2.pdf", "task_id": "T_20251215_002", "is_instant": True, "status": "completed", "estimated_wait_seconds": 0},
                    {"file_name": "doc3.pdf", "task_id": None, "is_instant": False, "status": "failed", "error": "文件大小超过限制"}
                ]
            }
        }
