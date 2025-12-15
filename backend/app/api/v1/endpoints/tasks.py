# -*- coding: utf-8 -*-
"""
任务查询API端点
实现任务列表、详情、状态更新和导出功能
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from datetime import datetime
import csv
import io
import json

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.task import Task, TaskStatus as TaskStatusEnum
from app.models.rule import Rule
from app.models.webhook import Webhook
from app.models.push_log import PushLog
from app.models.audit_log import AuditLog
from app.schemas.task import (
    TaskListQuery,
    TaskListItem,
    TaskListResponse,
    TaskDetail,
    TaskStatusUpdate,
    TaskExportQuery,
    TaskExportResponse,
    TaskStatus,
    PushLogDetail,
    PipelineExecutionDetail,
    TaskFlowStatus
)
from app.models.pipeline import PipelineExecution, Pipeline, ExecutionStatus
from app.core.mq import publish_task
from app.core.logger import logger


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[TaskStatus] = Query(None, description="任务状态筛选"),
    rule_id: Optional[str] = Query(None, description="规则ID筛选"),
    task_id: Optional[str] = Query(None, description="任务ID搜索"),
    file_name: Optional[str] = Query(None, description="文件名搜索"),
    search: Optional[str] = Query(None, description="搜索（任务ID或文件名）"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向: asc/desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取任务列表
    
    支持功能：
    - 分页查询
    - 按状态、规则ID筛选
    - 按任务ID、文件名搜索
    - 按日期范围筛选
    - 排序
    
    Requirements: 20
    """
    try:
        # 构建查询条件
        conditions = []
        
        if status:
            conditions.append(Task.status == status.value)
        
        if rule_id:
            conditions.append(Task.rule_id == rule_id)
        
        if task_id:
            conditions.append(Task.id.like(f"%{task_id}%"))
        
        if file_name:
            conditions.append(Task.file_name.like(f"%{file_name}%"))
        
        # 通用搜索（任务ID或文件名）
        if search:
            conditions.append(or_(
                Task.id.like(f"%{search}%"),
                Task.file_name.like(f"%{search}%")
            ))
        
        if start_date:
            conditions.append(Task.created_at >= start_date)
        
        if end_date:
            conditions.append(Task.created_at <= end_date)
        
        # 构建基础查询
        query = select(Task).options(selectinload(Task.rule))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 排序
        sort_column = getattr(Task, sort_by, Task.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
        # 计算总数
        count_query = select(func.count()).select_from(Task)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        result = await db.execute(count_query)
        total = result.scalar()
        
        # 分页查询
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        # 获取所有任务ID，批量查询管道执行记录
        task_ids = [t.id for t in tasks]
        pipeline_exec_map = {}
        if task_ids:
            exec_query = select(PipelineExecution).where(
                PipelineExecution.task_id.in_(task_ids)
            ).order_by(PipelineExecution.created_at.desc())
            exec_result = await db.execute(exec_query)
            for exe in exec_result.scalars().all():
                if exe.task_id not in pipeline_exec_map:
                    pipeline_exec_map[exe.task_id] = exe
        
        # 构建响应数据
        items = []
        for task in tasks:
            # 计算平均置信度
            avg_confidence = None
            if task.confidence_scores:
                scores = [v for v in task.confidence_scores.values() if isinstance(v, (int, float))]
                if scores:
                    avg_confidence = sum(scores) / len(scores)
            
            # 计算处理耗时
            duration_seconds = None
            if task.started_at and task.completed_at:
                duration_seconds = int((task.completed_at - task.started_at).total_seconds())
            
            # 构建简化的流转状态
            flow_status = _build_list_flow_status(task, pipeline_exec_map.get(task.id))
            
            item = TaskListItem(
                id=task.id,
                file_name=task.file_name,
                page_count=task.page_count,
                rule_id=task.rule_id,
                rule_name=task.rule.name if task.rule else None,
                rule_version=task.rule_version,
                status=TaskStatus(task.status.value),
                is_instant=task.is_instant,
                confidence_scores=task.confidence_scores,
                avg_confidence=avg_confidence,
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
                duration_seconds=duration_seconds,
                flow_status=flow_status
            )
            items.append(item)
        
        # 计算总页数
        total_pages = (total + page_size - 1) // page_size
        
        return TaskListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.get("/{task_id}", response_model=TaskDetail)
async def get_task_detail(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取任务详情
    
    返回完整任务信息，包括：
    - OCR结果
    - 提取结果
    - 置信度
    - 审核原因
    - 推送日志
    - 管道执行记录
    - 流转状态
    
    Requirements: 20
    """
    try:
        # 查询任务，包含关联数据
        query = select(Task).options(
            selectinload(Task.rule),
            selectinload(Task.auditor),
            selectinload(Task.push_logs).selectinload(PushLog.webhook)
        ).where(Task.id == task_id)
        
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 构建推送日志列表
        push_logs = []
        for log in task.push_logs:
            push_log = PushLogDetail(
                id=log.id,
                webhook_id=log.webhook_id,
                webhook_name=log.webhook.name if log.webhook else None,
                http_status=log.http_status,
                request_headers=log.request_headers,
                request_body=log.request_body,
                response_headers=log.response_headers,
                response_body=log.response_body,
                duration_ms=log.duration_ms,
                retry_count=log.retry_count,
                created_at=log.created_at
            )
            push_logs.append(push_log)
        
        # 查询管道执行记录
        pipeline_executions = []
        exec_query = select(PipelineExecution).options(
            selectinload(PipelineExecution.pipeline)
        ).where(PipelineExecution.task_id == task_id).order_by(PipelineExecution.created_at.desc())
        exec_result = await db.execute(exec_query)
        executions = exec_result.scalars().all()
        
        for exe in executions:
            # 处理状态值（可能是字符串或枚举）
            status_value = exe.status.value if hasattr(exe.status, 'value') else str(exe.status)
            pipeline_exec = PipelineExecutionDetail(
                id=exe.id,
                pipeline_id=exe.pipeline_id,
                pipeline_name=exe.pipeline.name if exe.pipeline else None,
                status=status_value,
                retry_count=exe.retry_count,
                input_data=exe.input_data,
                output_data=exe.output_data,
                stdout=exe.stdout,
                stderr=exe.stderr,
                error_message=exe.error_message,
                duration_ms=exe.duration_ms,
                created_at=exe.created_at,
                started_at=exe.started_at,
                completed_at=exe.completed_at
            )
            pipeline_executions.append(pipeline_exec)
        
        # 构建流转状态
        flow_status = _build_flow_status(task, executions, push_logs)
        logger.info(f"任务详情 flow_status: task_id={task_id}, ocr={flow_status.ocr_status}, pipeline={flow_status.pipeline_status}, push={flow_status.push_status}, executions_count={len(executions)}, push_logs_count={len(push_logs)}")
        
        # 构建任务详情
        detail = TaskDetail(
            id=task.id,
            file_name=task.file_name,
            file_path=task.file_path,
            file_hash=task.file_hash,
            page_count=task.page_count,
            rule_id=task.rule_id,
            rule_name=task.rule.name if task.rule else None,
            rule_version=task.rule_version,
            status=TaskStatus(task.status.value),
            is_instant=task.is_instant,
            ocr_text=task.ocr_text,
            ocr_result=task.ocr_result,
            extracted_data=task.extracted_data,
            confidence_scores=task.confidence_scores,
            audit_reasons=task.audit_reasons,
            auditor_id=task.auditor_id,
            auditor_name=task.auditor.username if task.auditor else None,
            audited_at=task.audited_at,
            llm_token_count=task.llm_token_count,
            llm_cost=float(task.llm_cost) if task.llm_cost else 0.0,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            push_logs=push_logs,
            pipeline_executions=pipeline_executions,
            flow_status=flow_status
        )
        
        return detail
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")


def _build_list_flow_status(task: Task, latest_exec) -> TaskFlowStatus:
    """构建任务列表的简化流转状态"""
    # 获取任务状态值（处理枚举和字符串两种情况）
    task_status = task.status.value if hasattr(task.status, 'value') else str(task.status)
    
    # OCR状态
    if task_status == "queued":
        ocr_status = "pending"
    elif task_status == "processing":
        ocr_status = "processing"
    elif task_status == "failed" and not task.ocr_text:
        ocr_status = "failed"
    else:
        ocr_status = "completed"
    
    # 管道状态
    pipeline_status = None
    if latest_exec:
        # 处理状态值（可能是字符串或枚举）
        pipeline_status = latest_exec.status.value if hasattr(latest_exec.status, 'value') else str(latest_exec.status)
    elif task_status in ["completed", "pushing", "push_success", "push_failed"]:
        pipeline_status = "skipped"
    
    # 推送状态
    push_status = None
    if task_status == "pushing":
        push_status = "pushing"
    elif task_status == "push_success":
        push_status = "success"
    elif task_status == "push_failed":
        push_status = "failed"
    elif task_status in ["completed", "pending_audit"]:
        push_status = "pending"
    elif task_status in ["rejected", "failed"]:
        push_status = "skipped"
    
    return TaskFlowStatus(
        ocr_status=ocr_status,
        ocr_completed_at=None,
        pipeline_status=pipeline_status,
        pipeline_completed_at=None,
        push_status=push_status,
        push_completed_at=None
    )


def _build_flow_status(task: Task, executions: list, push_logs: list) -> TaskFlowStatus:
    """构建任务流转状态"""
    # 获取任务状态值（处理枚举和字符串两种情况）
    task_status = task.status.value if hasattr(task.status, 'value') else str(task.status)
    
    # OCR状态
    if task_status == "queued":
        ocr_status = "pending"
    elif task_status == "processing":
        ocr_status = "processing"
    elif task_status == "failed" and not task.ocr_text:
        ocr_status = "failed"
    else:
        ocr_status = "completed"
    
    ocr_completed_at = task.started_at if task.ocr_text else None
    
    # 管道状态
    pipeline_status = None
    pipeline_completed_at = None
    if executions:
        latest_exec = executions[0]  # 已按时间倒序
        # 处理状态值（可能是字符串或枚举）
        pipeline_status = latest_exec.status.value if hasattr(latest_exec.status, 'value') else str(latest_exec.status)
        pipeline_completed_at = latest_exec.completed_at
    elif task_status in ["completed", "pushing", "push_success", "push_failed"]:
        # 没有管道执行记录但任务已完成，说明跳过了管道
        pipeline_status = "skipped"
    
    # 推送状态
    push_status = None
    push_completed_at = None
    if task_status == "pushing":
        push_status = "pushing"
    elif task_status == "push_success":
        push_status = "success"
        if push_logs:
            push_completed_at = max(log.created_at for log in push_logs)
    elif task_status == "push_failed":
        push_status = "failed"
        if push_logs:
            push_completed_at = max(log.created_at for log in push_logs)
    elif task_status in ["completed", "pending_audit"]:
        push_status = "pending"
    elif task_status in ["rejected", "failed"]:
        push_status = "skipped"
    
    return TaskFlowStatus(
        ocr_status=ocr_status,
        ocr_completed_at=ocr_completed_at,
        pipeline_status=pipeline_status,
        pipeline_completed_at=pipeline_completed_at,
        push_status=push_status,
        push_completed_at=push_completed_at
    )


@router.patch("/{task_id}/status")
async def update_task_status(
    task_id: str,
    update_data: TaskStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "auditor"))
):
    """
    更新任务状态
    
    支持审核员修正数据并提交：
    - 更新任务状态为Completed或Rejected
    - 保存修正后的提取数据
    - 触发推送（如果Completed）
    - 记录审核日志
    
    Requirements: 17
    """
    try:
        # 查询任务
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 检查任务状态是否允许更新
        if task.status not in [TaskStatusEnum.PENDING_AUDIT, TaskStatusEnum.PUSH_FAILED]:
            raise HTTPException(
                status_code=400,
                detail=f"任务状态为{task.status.value}，不允许更新"
            )
        
        # 更新任务状态
        old_status = task.status.value
        task.status = TaskStatusEnum(update_data.status.value)
        
        # 如果提供了修正数据，更新提取结果
        if update_data.extracted_data:
            task.extracted_data = update_data.extracted_data
            
            # 将修正后的字段置信度设置为100（人工确认）
            if task.confidence_scores:
                for field_name in update_data.extracted_data.keys():
                    if field_name in task.confidence_scores:
                        task.confidence_scores[field_name] = 100.0
        
        # 记录审核信息
        task.auditor_id = current_user.id
        task.audited_at = datetime.utcnow()
        
        if update_data.status == TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
        
        # 保存更新
        await db.commit()
        await db.refresh(task)
        
        # 记录审计日志
        audit_log = AuditLog(
            user_id=current_user.id,
            action_type="task_status_update",
            resource_type="task",
            resource_id=task_id,
            changes={
                "old_status": old_status,
                "new_status": update_data.status.value,
                "comment": update_data.audit_comment,
                "data_modified": update_data.extracted_data is not None
            },
            ip_address=None,  # 需要从request中获取
            user_agent=None
        )
        db.add(audit_log)
        await db.commit()
        
        # 如果状态变更为Completed，触发推送
        if update_data.status == TaskStatus.COMPLETED:
            try:
                await publish_task("push_tasks", {
                    "task_id": task_id,
                    "retry_count": 0
                })
                logger.info(f"任务 {task_id} 已加入推送队列")
            except Exception as e:
                logger.error(f"发布推送任务失败: {str(e)}")
        
        return {
            "code": 200,
            "message": "任务状态更新成功",
            "data": {
                "task_id": task_id,
                "status": update_data.status.value
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新任务状态失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新任务状态失败: {str(e)}")


@router.get("/export")
async def export_tasks(
    status: Optional[TaskStatus] = Query(None, description="任务状态筛选"),
    rule_id: Optional[str] = Query(None, description="规则ID筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    format: str = Query("csv", description="导出格式: csv/excel"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出任务数据
    
    支持功能：
    - 导出为CSV或Excel格式
    - 支持筛选条件
    - 数据量>10000时异步导出
    
    Requirements: 26
    """
    try:
        # 构建查询条件
        conditions = []
        
        if status:
            conditions.append(Task.status == status.value)
        
        if rule_id:
            conditions.append(Task.rule_id == rule_id)
        
        if start_date:
            conditions.append(Task.created_at >= start_date)
        
        if end_date:
            conditions.append(Task.created_at <= end_date)
        
        # 计算总数
        count_query = select(func.count()).select_from(Task)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        result = await db.execute(count_query)
        total = result.scalar()
        
        # 如果数据量超过10000，返回异步导出提示
        if total > 10000:
            # TODO: 实现异步导出逻辑
            return TaskExportResponse(
                task_id=None,
                download_url=None,
                message=f"数据量较大({total}条)，异步导出功能开发中，请缩小筛选范围"
            )
        
        # 同步导出
        query = select(Task).options(selectinload(Task.rule))
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(Task.created_at))
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        if format.lower() == "csv":
            # 生成CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            writer.writerow([
                "任务ID", "文件名", "页数", "规则ID", "规则名称", "规则版本",
                "状态", "是否秒传", "平均置信度", "创建时间", "完成时间", "耗时(秒)"
            ])
            
            # 写入数据
            for task in tasks:
                # 计算平均置信度
                avg_confidence = None
                if task.confidence_scores:
                    scores = [v for v in task.confidence_scores.values() if isinstance(v, (int, float))]
                    if scores:
                        avg_confidence = f"{sum(scores) / len(scores):.2f}"
                
                # 计算耗时
                duration = ""
                if task.started_at and task.completed_at:
                    duration = str(int((task.completed_at - task.started_at).total_seconds()))
                
                writer.writerow([
                    task.id,
                    task.file_name,
                    task.page_count,
                    task.rule_id,
                    task.rule.name if task.rule else "",
                    task.rule_version,
                    task.status.value,
                    "是" if task.is_instant else "否",
                    avg_confidence or "",
                    task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    task.completed_at.strftime("%Y-%m-%d %H:%M:%S") if task.completed_at else "",
                    duration
                ])
            
            # 返回CSV文件
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )
        
        else:
            # Excel格式暂不支持
            raise HTTPException(status_code=400, detail="Excel格式导出功能开发中")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出任务失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出任务失败: {str(e)}")


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    重试任务
    
    将失败或已驳回的任务重新加入处理队列
    
    可重试状态: failed, rejected
    """
    try:
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 检查状态是否允许重试
        if task.status not in [TaskStatusEnum.FAILED, TaskStatusEnum.REJECTED]:
            raise HTTPException(
                status_code=400,
                detail=f"任务状态为{task.status.value}，不允许重试"
            )
        
        # 重置任务状态
        task.status = TaskStatusEnum.QUEUED
        task.started_at = None
        task.completed_at = None
        task.error_message = None
        task.extracted_data = None
        task.confidence_scores = None
        task.audit_reasons = None
        task.auditor_id = None
        task.audited_at = None
        
        await db.commit()
        
        # 发布到OCR队列
        await publish_task("ocr_tasks", {"task_id": task_id})
        
        logger.info(f"任务 {task_id} 已重新加入队列")
        
        return {"code": 200, "message": "任务已重新加入队列", "task_id": task_id}
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"重试任务失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"重试任务失败: {str(e)}")


@router.post("/{task_id}/repush")
async def repush_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    重新推送任务
    
    将推送失败的任务重新加入推送队列
    
    可重推状态: push_failed
    """
    try:
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 检查状态是否允许重推
        if task.status != TaskStatusEnum.PUSH_FAILED:
            raise HTTPException(
                status_code=400,
                detail=f"任务状态为{task.status.value}，不允许重新推送"
            )
        
        # 更新状态为推送中
        task.status = TaskStatusEnum.PUSHING
        await db.commit()
        
        # 发布到推送队列
        await publish_task("push_tasks", {"task_id": task_id, "retry_count": 0})
        
        logger.info(f"任务 {task_id} 已重新加入推送队列")
        
        return {"code": 200, "message": "任务已重新加入推送队列", "task_id": task_id}
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"重新推送任务失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"重新推送任务失败: {str(e)}")


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    取消任务
    
    取消排队中的任务
    
    可取消状态: queued
    """
    try:
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 检查状态是否允许取消
        if task.status != TaskStatusEnum.QUEUED:
            raise HTTPException(
                status_code=400,
                detail=f"任务状态为{task.status.value}，不允许取消"
            )
        
        # 更新状态为已取消（使用REJECTED状态表示取消）
        task.status = TaskStatusEnum.REJECTED
        task.error_message = "用户取消"
        task.completed_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"任务 {task_id} 已取消")
        
        return {"code": 200, "message": "任务已取消", "task_id": task_id}
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"取消任务失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除任务
    
    删除已完成或失败的任务
    
    可删除状态: failed, rejected, completed, push_success, push_failed
    """
    try:
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 检查状态是否允许删除
        deletable_statuses = [
            TaskStatusEnum.FAILED,
            TaskStatusEnum.REJECTED,
            TaskStatusEnum.COMPLETED,
            TaskStatusEnum.PUSH_SUCCESS,
            TaskStatusEnum.PUSH_FAILED
        ]
        
        if task.status not in deletable_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"任务状态为{task.status.value}，不允许删除"
            )
        
        # 删除任务
        await db.delete(task)
        await db.commit()
        
        logger.info(f"任务 {task_id} 已删除")
        
        return {"code": 200, "message": "任务已删除", "task_id": task_id}
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除任务失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")
