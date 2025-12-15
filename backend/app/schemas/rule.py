# -*- coding: utf-8 -*-
"""
规则相关的Pydantic Schema定义
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class RuleStatus(str, Enum):
    """规则状态枚举"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class RuleCreate(BaseModel):
    """规则创建请求"""
    name: str = Field(..., min_length=1, max_length=100, description="规则名称")
    document_type: Optional[str] = Field(default=None, max_length=50, description="文档类型")
    description: Optional[str] = Field(default=None, description="规则描述")


class RuleUpdate(BaseModel):
    """规则更新请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="规则名称")
    document_type: Optional[str] = Field(default=None, max_length=50, description="文档类型")
    description: Optional[str] = Field(default=None, description="规则描述")


class RuleListQuery(BaseModel):
    """规则列表查询参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    document_type: Optional[str] = Field(default=None, description="文档类型筛选")
    search: Optional[str] = Field(default=None, description="搜索关键词（名称或编码）")
    status: Optional[RuleStatus] = Field(default=None, description="状态筛选")


class RuleListItem(BaseModel):
    """规则列表项"""
    id: str = Field(description="规则ID")
    name: str = Field(description="规则名称")
    code: str = Field(description="规则编码")
    document_type: Optional[str] = Field(default=None, description="文档类型")
    current_version: Optional[str] = Field(default=None, description="当前发布版本")
    status: str = Field(default="draft", description="规则状态")
    created_by: Optional[str] = Field(default=None, description="创建人ID")
    creator_name: Optional[str] = Field(default=None, description="创建人姓名")
    created_at: datetime = Field(description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")
    task_count: int = Field(default=0, description="关联任务数")

    class Config:
        from_attributes = True


class RuleListResponse(BaseModel):
    """规则列表响应"""
    items: List[RuleListItem] = Field(description="规则列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    total_pages: int = Field(description="总页数")


class RuleVersionItem(BaseModel):
    """规则版本列表项"""
    id: int = Field(description="版本ID")
    version: str = Field(description="版本号")
    status: RuleStatus = Field(description="版本状态")
    config: Dict[str, Any] = Field(description="版本配置")
    published_at: Optional[datetime] = Field(default=None, description="发布时间")
    published_by: Optional[str] = Field(default=None, description="发布人ID")
    publisher_name: Optional[str] = Field(default=None, description="发布人姓名")
    created_at: datetime = Field(description="创建时间")

    class Config:
        from_attributes = True


class RuleVersionListResponse(BaseModel):
    """规则版本列表响应"""
    items: List[RuleVersionItem] = Field(description="版本列表")
    total: int = Field(description="总数")


class RuleConfigUpdate(BaseModel):
    """规则配置更新请求"""
    config: Dict[str, Any] = Field(..., description="规则配置JSON")


class RuleDetail(BaseModel):
    """规则详情"""
    id: str = Field(description="规则ID")
    name: str = Field(description="规则名称")
    code: str = Field(description="规则编码")
    document_type: Optional[str] = Field(default=None, description="文档类型")
    current_version: Optional[str] = Field(default=None, description="当前发布版本")
    created_by: Optional[str] = Field(default=None, description="创建人ID")
    creator_name: Optional[str] = Field(default=None, description="创建人姓名")
    created_at: datetime = Field(description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")
    
    # 当前发布版本的配置
    current_config: Optional[Dict[str, Any]] = Field(default=None, description="当前发布版本配置")
    
    # 统计信息
    task_count: int = Field(default=0, description="关联任务数")
    version_count: int = Field(default=0, description="版本数量")

    class Config:
        from_attributes = True


class RulePublishRequest(BaseModel):
    """规则发布请求"""
    version_id: int = Field(..., description="要发布的版本ID")
    comment: Optional[str] = Field(default=None, description="发布备注")


class RuleRollbackRequest(BaseModel):
    """规则回滚请求"""
    version_id: int = Field(..., description="要回滚到的版本ID")
    comment: Optional[str] = Field(default=None, description="回滚备注")


class SandboxTestRequest(BaseModel):
    """沙箱测试请求（用于接收文件上传后的元数据）"""
    version_id: Optional[int] = Field(default=None, description="测试的版本ID（可选，默认使用草稿版本）")


class SandboxTestResponse(BaseModel):
    """沙箱测试响应"""
    success: bool = Field(description="是否成功")
    extracted_data: Optional[Dict[str, Any]] = Field(default=None, description="提取的JSON结果")
    ocr_result: Optional[Dict[str, Any]] = Field(default=None, description="OCR标注结果")
    merged_text: Optional[str] = Field(default=None, description="合并后的OCR纯文本")
    confidence_scores: Optional[Dict[str, float]] = Field(default=None, description="字段置信度")
    consistency_results: Optional[Dict[str, Any]] = Field(default=None, description="一致性校验结果")
    needs_review: bool = Field(default=False, description="是否需要人工审核")
    processing_time: Optional[float] = Field(default=None, description="处理耗时(秒)")
    error: Optional[str] = Field(default=None, description="错误信息")


class RuleResponse(BaseModel):
    """规则操作响应"""
    id: str = Field(description="规则ID")
    message: str = Field(description="操作结果消息")


class RuleImportData(BaseModel):
    """规则导入数据"""
    name: str = Field(..., min_length=1, max_length=100, description="规则名称")
    document_type: Optional[str] = Field(default=None, description="文档类型")
    current_config: Optional[Dict[str, Any]] = Field(default=None, description="规则配置")
    
    class Config:
        extra = "ignore"  # 忽略导出文件中的其他字段（如id、code、created_at等）


class RuleImportResponse(BaseModel):
    """规则导入响应"""
    success: bool = Field(description="是否成功")
    id: Optional[str] = Field(default=None, description="导入后的规则ID")
    code: Optional[str] = Field(default=None, description="导入后的规则编码")
    message: str = Field(description="操作结果消息")
