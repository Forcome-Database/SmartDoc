"""
审计日志端点
实现审计日志查询和导出功能，仅Admin角色可访问
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional, List
from datetime import datetime
import csv
import io

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import (
    AuditLogResponse,
    PaginatedAuditLogResponse,
    AuditLogExportResponse
)
from app.schemas.response import SuccessResponse

router = APIRouter(prefix="/audit-logs", tags=["审计日志"])


@router.get("", response_model=PaginatedAuditLogResponse, summary="获取审计日志列表")
async def get_audit_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: Optional[str] = Query(None, description="用户ID筛选"),
    action_type: Optional[str] = Query(None, description="操作类型筛选"),
    resource_type: Optional[str] = Query(None, description="资源类型筛选"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    获取审计日志列表
    
    - 支持分页
    - 支持按时间范围、用户、操作类型、资源类型筛选
    - 仅Admin角色可访问
    
    Args:
        page: 页码
        page_size: 每页数量
        user_id: 用户ID筛选
        action_type: 操作类型筛选
        resource_type: 资源类型筛选
        start_date: 开始时间
        end_date: 结束时间
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        分页的审计日志列表
    """
    # 构建查询条件
    conditions = []
    
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    
    if action_type:
        conditions.append(AuditLog.action_type == action_type)
    
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    
    if start_date:
        conditions.append(AuditLog.created_at >= start_date)
    
    if end_date:
        conditions.append(AuditLog.created_at <= end_date)
    
    # 查询总数
    count_query = select(func.count(AuditLog.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    result = await db.execute(count_query)
    total = result.scalar()
    
    # 查询日志列表（关联用户表获取用户名）
    query = (
        select(AuditLog, User.username)
        .outerjoin(User, AuditLog.user_id == User.id)
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    rows = result.all()
    
    # 构建响应数据
    items = []
    for audit_log, username in rows:
        log_dict = {
            "id": audit_log.id,
            "user_id": audit_log.user_id,
            "username": username,
            "action_type": audit_log.action_type,
            "resource_type": audit_log.resource_type,
            "resource_id": audit_log.resource_id,
            "changes": audit_log.changes,
            "ip_address": audit_log.ip_address,
            "user_agent": audit_log.user_agent,
            "created_at": audit_log.created_at
        }
        items.append(log_dict)
    
    # 计算总页数
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    }


@router.get("/export", summary="导出审计日志")
async def export_audit_logs(
    user_id: Optional[str] = Query(None, description="用户ID筛选"),
    action_type: Optional[str] = Query(None, description="操作类型筛选"),
    resource_type: Optional[str] = Query(None, description="资源类型筛选"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    导出审计日志为CSV格式
    
    - 支持按时间范围、用户、操作类型、资源类型筛选
    - 仅Admin角色可访问
    
    Args:
        user_id: 用户ID筛选
        action_type: 操作类型筛选
        resource_type: 资源类型筛选
        start_date: 开始时间
        end_date: 结束时间
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        CSV文件流
    """
    # 构建查询条件
    conditions = []
    
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    
    if action_type:
        conditions.append(AuditLog.action_type == action_type)
    
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    
    if start_date:
        conditions.append(AuditLog.created_at >= start_date)
    
    if end_date:
        conditions.append(AuditLog.created_at <= end_date)
    
    # 查询所有符合条件的日志（关联用户表）
    query = (
        select(AuditLog, User.username)
        .outerjoin(User, AuditLog.user_id == User.id)
        .order_by(AuditLog.created_at.desc())
    )
    
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    rows = result.all()
    
    # 创建CSV内容
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow([
        "日志ID",
        "用户ID",
        "用户名",
        "操作类型",
        "资源类型",
        "资源ID",
        "变更内容",
        "IP地址",
        "User Agent",
        "创建时间"
    ])
    
    # 写入数据行
    for audit_log, username in rows:
        writer.writerow([
            audit_log.id,
            audit_log.user_id or "",
            username or "",
            audit_log.action_type,
            audit_log.resource_type,
            audit_log.resource_id or "",
            str(audit_log.changes) if audit_log.changes else "",
            audit_log.ip_address or "",
            audit_log.user_agent or "",
            audit_log.created_at.strftime("%Y-%m-%d %H:%M:%S") if audit_log.created_at else ""
        ])
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"audit_logs_{timestamp}.csv"
    
    # 返回CSV文件流
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
