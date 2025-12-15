"""
仪表盘API端点
提供核心指标、任务吞吐趋势、规则效能和异常分布等数据
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case, and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.cache import get_redis, RedisClient
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.rule import Rule
from app.schemas.response import ResponseModel
import json


router = APIRouter(prefix="/dashboard", tags=["仪表盘"])


def get_date_range(range_type: str) -> tuple[datetime, datetime]:
    """
    根据时间范围类型获取开始和结束时间
    
    Args:
        range_type: 时间范围类型（today, 7days, 30days）
        
    Returns:
        (start_date, end_date) 元组
    """
    now = datetime.utcnow()
    end_date = now
    
    if range_type == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_type == "7days":
        start_date = now - timedelta(days=7)
    elif range_type == "30days":
        start_date = now - timedelta(days=30)
    else:
        # 默认7天
        start_date = now - timedelta(days=7)
    
    return start_date, end_date


@router.get("/metrics", summary="获取核心指标")
async def get_dashboard_metrics(
    time_range: str = Query("7days", description="时间范围：today, 7days, 30days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis)
):
    """
    获取仪表盘核心指标
    
    返回8个核心指标：
    1. 总接单量
    2. 累计页数
    3. 处理中任务数
    4. 待审核任务数
    5. 推送异常数
    6. 直通率
    7. 算力节省
    8. LLM消耗
    
    使用Redis缓存5分钟
    """
    # 检查缓存
    cache_key = f"metrics:dashboard:{time_range}"
    cached_data = await redis.get(cache_key)
    if cached_data:
        return ResponseModel(data=json.loads(cached_data))
    
    # 获取时间范围
    start_date, end_date = get_date_range(time_range)
    
    # 1. 总接单量
    total_tasks_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.created_at >= start_date,
            Task.created_at <= end_date
        )
    )
    total_tasks = total_tasks_result.scalar() or 0
    
    # 2. 累计页数（所有任务实际消耗的OCR页数总和）
    total_pages_result = await db.execute(
        select(func.sum(Task.page_count)).where(
            Task.created_at >= start_date,
            Task.created_at <= end_date
        )
    )
    total_pages = total_pages_result.scalar() or 0
    
    # 3. 处理中任务数
    processing_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.created_at >= start_date,
            Task.created_at <= end_date,
            Task.status.in_([TaskStatus.QUEUED, TaskStatus.PROCESSING, TaskStatus.PUSHING])
        )
    )
    processing_count = processing_result.scalar() or 0
    
    # 4. 待审核任务数
    pending_audit_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.created_at >= start_date,
            Task.created_at <= end_date,
            Task.status == TaskStatus.PENDING_AUDIT
        )
    )
    pending_audit_count = pending_audit_result.scalar() or 0
    
    # 5. 推送异常数
    push_failed_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.created_at >= start_date,
            Task.created_at <= end_date,
            Task.status == TaskStatus.PUSH_FAILED
        )
    )
    push_failed_count = push_failed_result.scalar() or 0
    
    # 6. 直通率（无需人工干预且成功推送的任务数 / 总任务数）
    # 直通任务：completed或push_success状态，且未经过人工审核（auditor_id为空）
    straight_through_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.created_at >= start_date,
            Task.created_at <= end_date,
            Task.status.in_([TaskStatus.COMPLETED, TaskStatus.PUSH_SUCCESS]),
            Task.auditor_id.is_(None)
        )
    )
    straight_through_count = straight_through_result.scalar() or 0
    
    straight_through_rate = (straight_through_count / total_tasks * 100) if total_tasks > 0 else 0
    
    # 7. 算力节省（秒传任务节省的处理时间）
    instant_tasks_result = await db.execute(
        select(Task).where(
            Task.created_at >= start_date,
            Task.created_at <= end_date,
            Task.is_instant == True
        )
    )
    instant_tasks = instant_tasks_result.scalars().all()
    instant_count = len(instant_tasks)
    instant_pages = sum(task.page_count for task in instant_tasks)
    # 假设单页处理耗时3秒
    saved_seconds = instant_pages * 3
    saved_hours = saved_seconds / 3600
    
    # 8. LLM消耗（总Token数和预估费用）
    llm_stats_result = await db.execute(
        select(
            func.sum(Task.llm_token_count).label('total_tokens'),
            func.sum(Task.llm_cost).label('total_cost')
        ).where(
            Task.created_at >= start_date,
            Task.created_at <= end_date
        )
    )
    llm_stats = llm_stats_result.first()
    
    total_llm_tokens = int(llm_stats.total_tokens or 0)
    total_llm_cost = float(llm_stats.total_cost or 0)
    
    # 组装结果
    metrics = {
        "total_tasks": int(total_tasks),
        "total_pages": int(total_pages),
        "processing_count": int(processing_count),
        "pending_audit_count": int(pending_audit_count),
        "push_failed_count": int(push_failed_count),
        "straight_through_rate": round(straight_through_rate, 2),
        "cost_savings": {
            "instant_count": instant_count,
            "instant_pages": instant_pages,
            "saved_hours": round(saved_hours, 2)
        },
        "llm_consumption": {
            "total_tokens": total_llm_tokens,
            "total_cost": round(total_llm_cost, 2)
        },
        "time_range": time_range,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }
    
    # 缓存5分钟
    await redis.set(cache_key, json.dumps(metrics), expire=300)
    
    return ResponseModel(data=metrics)




@router.get("/throughput", summary="获取任务吞吐趋势")
async def get_task_throughput(
    time_range: str = Query("7days", description="时间范围：today, 7days, 30days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取任务吞吐趋势
    
    返回每日任务数量统计，包含：
    - 成功（completed, push_success）
    - 待审核（pending_audit）
    - 失败（failed, push_failed）
    - 驳回（rejected）
    
    按日期分组聚合
    """
    # 获取时间范围
    start_date, end_date = get_date_range(time_range)
    
    # 按日期分组统计各状态任务数
    # 使用DATE函数提取日期部分
    results = await db.execute(
        select(
            func.date(Task.created_at).label('date'),
            func.sum(
                case(
                    (Task.status.in_([TaskStatus.COMPLETED, TaskStatus.PUSH_SUCCESS]), 1),
                    else_=0
                )
            ).label('success_count'),
            func.sum(
                case(
                    (Task.status == TaskStatus.PENDING_AUDIT, 1),
                    else_=0
                )
            ).label('pending_audit_count'),
            func.sum(
                case(
                    (Task.status.in_([TaskStatus.FAILED, TaskStatus.PUSH_FAILED]), 1),
                    else_=0
                )
            ).label('failed_count'),
            func.sum(
                case(
                    (Task.status == TaskStatus.REJECTED, 1),
                    else_=0
                )
            ).label('rejected_count')
        ).where(
            Task.created_at >= start_date,
            Task.created_at <= end_date
        ).group_by(
            func.date(Task.created_at)
        ).order_by(
            func.date(Task.created_at)
        )
    )
    
    # 格式化结果
    throughput_data = []
    for row in results:
        throughput_data.append({
            "date": row.date.isoformat() if row.date else None,
            "success": int(row.success_count or 0),
            "pending_audit": int(row.pending_audit_count or 0),
            "failed": int(row.failed_count or 0),
            "rejected": int(row.rejected_count or 0),
            "total": int(
                (row.success_count or 0) + 
                (row.pending_audit_count or 0) + 
                (row.failed_count or 0) + 
                (row.rejected_count or 0)
            )
        })
    
    return ResponseModel(data={
        "time_range": time_range,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "throughput": throughput_data
    })




@router.get("/rule-performance", summary="获取规则效能Top10")
async def get_rule_performance(
    time_range: str = Query("7days", description="时间范围：today, 7days, 30days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取规则效能Top10
    
    返回任务量Top10的规则，包含：
    - 规则名称
    - 任务量
    - 平均耗时（秒）
    - 人工干预率（%）
    
    按任务量降序排列
    """
    try:
        # 获取时间范围
        start_date, end_date = get_date_range(time_range)
        
        # 第一步：查询规则和任务数量（不包含复杂的时间计算）
        basic_results = await db.execute(
            select(
                Rule.id,
                Rule.name,
                Rule.code,
                Rule.document_type,
                func.count(Task.id).label('task_count'),
                func.sum(
                    case(
                        (Task.status == TaskStatus.PENDING_AUDIT, 1),
                        else_=0
                    )
                ).label('audit_count')
            ).join(
                Task, Task.rule_id == Rule.id
            ).where(
                Task.created_at >= start_date,
                Task.created_at <= end_date
            ).group_by(
                Rule.id, Rule.name, Rule.code, Rule.document_type
            ).order_by(
                func.count(Task.id).desc()
            ).limit(10)
        )
        
        # 格式化结果
        performance_data = []
        for row in basic_results:
            task_count = int(row.task_count or 0)
            audit_count = int(row.audit_count or 0)
            
            # 计算人工干预率
            intervention_rate = (audit_count / task_count * 100) if task_count > 0 else 0
            
            # 确定干预率等级（用于前端颜色标识）
            if intervention_rate < 10:
                intervention_level = "low"  # 低（绿色）
            elif intervention_rate < 30:
                intervention_level = "medium"  # 中（黄色）
            else:
                intervention_level = "high"  # 高（红色）
            
            # 第二步：查询该规则的已完成任务，计算平均耗时
            avg_duration = 0.0
            try:
                # 查询有开始和完成时间的任务
                tasks_result = await db.execute(
                    select(Task).where(
                        Task.rule_id == row.id,
                        Task.created_at >= start_date,
                        Task.created_at <= end_date,
                        Task.started_at.isnot(None),
                        Task.completed_at.isnot(None)
                    )
                )
                tasks = tasks_result.scalars().all()
                
                if tasks:
                    # 计算每个任务的耗时（秒）
                    durations = []
                    for task in tasks:
                        duration = (task.completed_at - task.started_at).total_seconds()
                        if duration > 0:  # 只统计有效的耗时
                            durations.append(duration)
                    
                    if durations:
                        avg_duration = sum(durations) / len(durations)
            except Exception as dur_error:
                # 如果计算平均耗时失败，使用0
                print(f"计算规则 {row.id} 平均耗时失败: {str(dur_error)}")
                avg_duration = 0.0
            
            performance_data.append({
                "rule_id": row.id,
                "rule_name": row.name,
                "rule_code": row.code,
                "document_type": row.document_type,
                "task_count": task_count,
                "avg_duration": round(avg_duration, 2),
                "intervention_rate": round(intervention_rate, 2),
                "intervention_level": intervention_level
            })
        
        return ResponseModel(data={
            "time_range": time_range,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "rules": performance_data
        })
    except Exception as e:
        # 记录错误并返回空数据而不是500错误
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_rule_performance: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 返回空数据
        start_date, end_date = get_date_range(time_range)
        return ResponseModel(data={
            "time_range": time_range,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "rules": []
        })




@router.get("/exceptions", summary="获取异常分布")
async def get_exception_distribution(
    time_range: str = Query("7days", description="时间范围：today, 7days, 30days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取异常分布
    
    统计各类异常的数量和占比，包括：
    - OCR识别空
    - 必填校验失败
    - 格式校验失败
    - LLM不一致
    - 下游接口错误
    - 处理超时
    
    返回饼图数据
    """
    # 获取时间范围
    start_date, end_date = get_date_range(time_range)
    
    # 查询所有有审核原因或失败的任务
    tasks_with_issues_result = await db.execute(
        select(Task).where(
            Task.created_at >= start_date,
            Task.created_at <= end_date,
            or_(
                Task.audit_reasons.isnot(None),
                Task.status.in_([TaskStatus.FAILED, TaskStatus.PUSH_FAILED])
            )
        )
    )
    tasks_with_issues = tasks_with_issues_result.scalars().all()
    
    # 统计各类异常
    exception_stats = {
        "ocr_empty": 0,  # OCR识别空
        "required_field_missing": 0,  # 必填校验失败
        "format_validation_failed": 0,  # 格式校验失败
        "llm_inconsistent": 0,  # LLM不一致
        "downstream_error": 0,  # 下游接口错误
        "processing_timeout": 0,  # 处理超时
        "other": 0  # 其他异常
    }
    
    for task in tasks_with_issues:
        # 分析审核原因
        if task.audit_reasons:
            reasons = task.audit_reasons if isinstance(task.audit_reasons, list) else []
            for reason in reasons:
                reason_text = reason.get('reason', '') if isinstance(reason, dict) else str(reason)
                reason_lower = reason_text.lower()
                
                if 'ocr' in reason_lower and ('空' in reason_lower or 'empty' in reason_lower):
                    exception_stats["ocr_empty"] += 1
                elif '必填' in reason_lower or 'required' in reason_lower:
                    exception_stats["required_field_missing"] += 1
                elif '格式' in reason_lower or 'format' in reason_lower or '校验' in reason_lower:
                    exception_stats["format_validation_failed"] += 1
                elif 'llm' in reason_lower and ('不一致' in reason_lower or 'inconsistent' in reason_lower):
                    exception_stats["llm_inconsistent"] += 1
                else:
                    exception_stats["other"] += 1
        
        # 分析任务状态和错误信息
        if task.status == TaskStatus.PUSH_FAILED:
            exception_stats["downstream_error"] += 1
        elif task.status == TaskStatus.FAILED:
            if task.error_message:
                error_lower = task.error_message.lower()
                if 'timeout' in error_lower or '超时' in error_lower:
                    exception_stats["processing_timeout"] += 1
                else:
                    exception_stats["other"] += 1
    
    # 计算总数和占比
    total_exceptions = sum(exception_stats.values())
    
    # 格式化结果为饼图数据
    exception_data = []
    exception_labels = {
        "ocr_empty": "OCR识别空",
        "required_field_missing": "必填校验失败",
        "format_validation_failed": "格式校验失败",
        "llm_inconsistent": "LLM不一致",
        "downstream_error": "下游接口错误",
        "processing_timeout": "处理超时",
        "other": "其他异常"
    }
    
    for key, count in exception_stats.items():
        if count > 0:  # 只返回有数据的异常类型
            percentage = (count / total_exceptions * 100) if total_exceptions > 0 else 0
            exception_data.append({
                "type": key,
                "label": exception_labels[key],
                "count": count,
                "percentage": round(percentage, 2)
            })
    
    # 按数量降序排列
    exception_data.sort(key=lambda x: x['count'], reverse=True)
    
    return ResponseModel(data={
        "time_range": time_range,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_exceptions": total_exceptions,
        "exceptions": exception_data
    })
