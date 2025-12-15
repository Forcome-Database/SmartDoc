"""
文件上传相关的Schema定义
"""
from pydantic import BaseModel, Field
from typing import Optional


class UploadResponse(BaseModel):
    """文件上传响应"""
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
