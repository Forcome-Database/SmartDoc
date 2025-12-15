# -*- coding: utf-8 -*-
"""
审核工作台相关的Pydantic Schema定义
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field


class AuditReason(BaseModel):
    """审核原因详情"""
    type: str = Field(description="原因类型: confidence_low, missing_field, validation_failed")
    field: Optional[str] = Field(default=None, description="相关字段名")
    threshold: Optional[float] = Field(default=None, description="阈值")
    confidence: Optional[float] = Field(default=None, description="实际置信度")
    message: Optional[str] = Field(default=None, description="原因描述")

    class Config:
        from_attributes = True


class AuditTaskDetail(BaseModel):
    """审核任务详情"""
    id: str = Field(description="任务ID")
    file_name: str = Field(description="文件名")
    file_url: Optional[str] = Field(default=None, description="PDF文件预签名URL")
    page_count: int = Field(description="页数")
    rule_id: str = Field(description="规则ID")
    rule_name: Optional[str] = Field(default=None, description="规则名称")
    rule_version: str = Field(description="规则版本")
    status: str = Field(description="任务状态")
    
    # OCR结果（含坐标信息）
    ocr_result: Optional[Dict[str, Any]] = Field(default=None, description="OCR完整结果（含坐标）")
    
    # 提取结果和置信度
    extracted_data: Optional[Dict[str, Any]] = Field(default=None, description="提取数据")
    confidence_scores: Optional[Dict[str, float]] = Field(default=None, description="字段置信度")
    
    # 审核原因 - 支持字符串列表或字典列表
    audit_reasons: Optional[List[Union[str, Dict[str, Any], AuditReason]]] = Field(default=None, description="审核原因列表")
    
    # 时间信息
    created_at: datetime = Field(description="创建时间")
    started_at: Optional[datetime] = Field(default=None, description="开始处理时间")

    class Config:
        from_attributes = True


class DraftSaveRequest(BaseModel):
    """草稿保存请求"""
    extracted_data: Dict[str, Any] = Field(description="修改后的提取数据")


class DraftSaveResponse(BaseModel):
    """草稿保存响应"""
    message: str = Field(description="提示信息")
    saved_at: datetime = Field(description="保存时间")


class AuditSubmitRequest(BaseModel):
    """审核提交请求"""
    # 支持两种格式：decision 或 action
    decision: Optional[str] = Field(default=None, description="审核决策: approved/rejected")
    action: Optional[str] = Field(default=None, description="审核动作: approve/reject")
    # 支持两种格式：extracted_data 或 data
    extracted_data: Optional[Dict[str, Any]] = Field(default=None, description="修正后的数据")
    data: Optional[Dict[str, Any]] = Field(default=None, description="修正后的数据（别名）")
    comment: Optional[str] = Field(default=None, description="审核备注")
    reason: Optional[str] = Field(default=None, description="驳回原因")


class AuditSubmitResponse(BaseModel):
    """审核提交响应"""
    message: str = Field(description="提示信息")
    task_id: str = Field(description="任务ID")
    new_status: str = Field(description="新状态")

