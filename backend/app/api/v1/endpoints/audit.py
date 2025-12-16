# -*- coding: utf-8 -*-
"""
审核工作台API端点
实现待审核任务列表、任务详情、PDF预览、草稿保存和审核提交功能
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import json
import io
import base64
import os
import tempfile

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.cache import get_redis
from app.core.storage import minio_client
from app.core.mq import publish_task
from app.core.logger import logger
from app.models.user import User
from app.models.task import Task, TaskStatus as TaskStatusEnum
from app.models.rule import Rule
from app.models.audit_log import AuditLog
from app.schemas.task import (
    TaskListItem,
    TaskListResponse,
    TaskStatus
)
from app.schemas.audit import (
    AuditTaskDetail,
    DraftSaveRequest,
    DraftSaveResponse,
    AuditSubmitRequest,
    AuditSubmitResponse
)
from app.services.dingtalk_service import dingtalk_service


router = APIRouter(prefix="/audit", tags=["audit"])


async def generate_placeholder_image(page: int, total_pages: int) -> Response:
    """
    生成占位图片（当PDF文件不存在时使用）
    
    Args:
        page: 当前页码
        total_pages: 总页数
        
    Returns:
        Response: 包含占位图片的响应
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # 创建一个灰色背景的图片
        width, height = 595, 842  # A4比例
        img = Image.new('RGB', (width, height), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)
        
        # 绘制边框
        draw.rectangle([10, 10, width-10, height-10], outline=(200, 200, 200), width=2)
        
        # 绘制文字
        text_lines = [
            "PDF 预览不可用",
            "",
            f"第 {page} 页 / 共 {total_pages} 页",
            "",
            "文件可能已被删除或移动"
        ]
        
        # 使用默认字体
        try:
            font = ImageFont.truetype("arial.ttf", 24)
            small_font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
            small_font = font
        
        y_position = height // 3
        for i, line in enumerate(text_lines):
            if line:
                # 计算文字宽度以居中
                bbox = draw.textbbox((0, 0), line, font=font if i == 0 else small_font)
                text_width = bbox[2] - bbox[0]
                x_position = (width - text_width) // 2
                draw.text(
                    (x_position, y_position),
                    line,
                    fill=(128, 128, 128),
                    font=font if i == 0 else small_font
                )
            y_position += 40
        
        # 转换为字节
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return Response(
            content=img_byte_arr.getvalue(),
            media_type="image/png",
            headers={
                "Cache-Control": "no-cache",
                "X-Placeholder": "true"
            }
        )
    except Exception as e:
        logger.error(f"生成占位图片失败: {str(e)}")
        # 返回一个简单的1x1像素透明图片
        transparent_pixel = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        return Response(
            content=transparent_pixel,
            media_type="image/png"
        )


@router.get("/tasks", response_model=TaskListResponse)
async def list_audit_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（任务ID或文件名）"),
    rule_id: Optional[str] = Query(None, description="规则ID筛选"),
    confidence_range: Optional[str] = Query(None, description="置信度范围: high/medium/low"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向: asc/desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "auditor"))
):
    """
    获取待审核任务列表
    
    仅返回状态为Pending Audit的任务
    支持分页、搜索和筛选
    仅Auditor和Admin角色可访问
    
    Requirements: 16
    """
    try:
        # 构建查询条件 - 固定筛选待审核状态
        conditions = [Task.status == TaskStatusEnum.PENDING_AUDIT]
        
        # 关键词搜索
        if keyword:
            from sqlalchemy import or_
            conditions.append(
                or_(
                    Task.id.like(f"%{keyword}%"),
                    Task.file_name.like(f"%{keyword}%")
                )
            )
        
        if rule_id:
            conditions.append(Task.rule_id == rule_id)
        
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                conditions.append(Task.created_at >= start_dt)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                # 包含结束日期的全天
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                conditions.append(Task.created_at <= end_dt)
            except ValueError:
                pass
        
        # 构建基础查询
        query = select(Task).options(selectinload(Task.rule))
        query = query.where(and_(*conditions))
        
        # 排序
        sort_column = getattr(Task, sort_by, Task.created_at)
        if sort_order.lower() == "asc":
            from sqlalchemy import asc
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
        # 计算总数
        count_query = select(func.count()).select_from(Task).where(and_(*conditions))
        result = await db.execute(count_query)
        total = result.scalar()
        
        # 分页查询
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        # 构建响应数据
        items = []
        for task in tasks:
            # 计算平均置信度
            avg_confidence = None
            if task.confidence_scores:
                scores = [v for v in task.confidence_scores.values() if isinstance(v, (int, float))]
                if scores:
                    avg_confidence = sum(scores) / len(scores)
            
            # 置信度范围筛选
            if confidence_range:
                if confidence_range == "high" and (avg_confidence is None or avg_confidence < 90):
                    continue
                elif confidence_range == "medium" and (avg_confidence is None or avg_confidence < 70 or avg_confidence >= 90):
                    continue
                elif confidence_range == "low" and (avg_confidence is None or avg_confidence >= 70):
                    continue
            
            # 计算处理耗时
            duration_seconds = None
            if task.started_at and task.completed_at:
                duration_seconds = int((task.completed_at - task.started_at).total_seconds())
            
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
                audit_reasons=task.audit_reasons,
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
                duration_seconds=duration_seconds
            )
            items.append(item)
        
        # 计算总页数
        total_pages = (total + page_size - 1) // page_size
        
        logger.info(f"用户 {current_user.username} 查询待审核任务列表，共 {total} 条")
        
        return TaskListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    except Exception as e:
        logger.error(f"获取待审核任务列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取待审核任务列表失败: {str(e)}")




@router.get("/tasks/{task_id}", response_model=AuditTaskDetail)
async def get_audit_task_detail(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "auditor"))
):
    """
    获取审核任务详情
    
    返回任务完整信息：
    - PDF文件预签名URL（1小时有效期）
    - OCR结果（含坐标信息）
    - 提取结果和置信度
    - 审核原因
    
    Requirements: 16, 33, 41
    """
    try:
        # 查询任务
        query = select(Task).options(
            selectinload(Task.rule)
        ).where(Task.id == task_id)
        
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 生成PDF文件预签名URL（1小时有效期）
        file_url = None
        if task.file_path:
            try:
                from datetime import timedelta
                # 从 file_path 中提取对象名称（去掉 bucket 前缀）
                object_name = task.file_path
                if "/" in object_name and object_name.startswith(minio_client._bucket):
                    object_name = object_name[len(minio_client._bucket) + 1:]
                
                file_url = minio_client.generate_presigned_url(
                    object_name,
                    expires=timedelta(hours=1)
                )
            except Exception as e:
                logger.warning(f"生成预签名URL失败: {str(e)}")
        
        # 构建审核任务详情
        detail = AuditTaskDetail(
            id=task.id,
            file_name=task.file_name,
            file_url=file_url,
            page_count=task.page_count,
            rule_id=task.rule_id,
            rule_name=task.rule.name if task.rule else None,
            rule_version=task.rule_version,
            status=task.status.value,
            ocr_result=task.ocr_result,
            extracted_data=task.extracted_data,
            confidence_scores=task.confidence_scores,
            audit_reasons=task.audit_reasons,
            created_at=task.created_at,
            started_at=task.started_at
        )
        
        logger.info(f"用户 {current_user.username} 查看审核任务详情: {task_id}")
        
        return detail
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取审核任务详情失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取审核任务详情失败: {str(e)}")




@router.get("/tasks/{task_id}/preview/{page}")
async def get_page_preview(
    task_id: str,
    page: int = Path(..., ge=1, description="页码（从1开始）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "auditor"))
):
    """
    获取PDF页面预览图
    
    按需生成单页预览图
    使用Redis缓存（1小时）
    支持懒加载
    
    Requirements: 16
    """
    try:
        # 查询任务
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 检查页码是否有效
        if page > task.page_count:
            raise HTTPException(
                status_code=400,
                detail=f"页码超出范围，文档共{task.page_count}页"
            )
        
        # 检查Redis缓存
        redis = await get_redis()
        cache_key = f"preview:{task_id}:{page}"
        
        cached_image_b64 = await redis.get(cache_key)
        if cached_image_b64:
            logger.debug(f"从缓存获取预览图: {task_id}, 页码: {page}")
            cached_image = base64.b64decode(cached_image_b64)
            return Response(
                content=cached_image,
                media_type="image/png",
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "X-Cache": "HIT"
                }
            )
        
        # 生成预览图
        from app.services.pdf_service import pdf_service
        from app.services.file_service import file_service
        
        # 检查文件是否存在
        if not task.file_path:
            raise HTTPException(status_code=404, detail="任务没有关联的文件")
        
        # 检查文件是否在存储中存在
        if not file_service.file_exists(task.file_path):
            logger.warning(f"文件不存在于存储中: {task.file_path}")
            # 返回占位图片
            return await generate_placeholder_image(page, task.page_count)
        
        # 下载PDF文件
        try:
            pdf_content = await file_service.download_from_storage(task.file_path)
        except Exception as e:
            logger.error(f"下载PDF文件失败: {task.file_path}, 错误: {str(e)}")
            return await generate_placeholder_image(page, task.page_count)
        
        # 保存到临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(pdf_content)
            temp_pdf_path = temp_file.name
        
        try:
            # 转换单页为图片
            image_path = await pdf_service.convert_single_page_to_image(
                temp_pdf_path,
                page_number=page,
                dpi=150,  # 使用较低DPI以减少文件大小
                fmt="PNG"
            )
            
            # 读取图片内容
            with open(image_path, 'rb') as img_file:
                image_content = img_file.read()
            
            # 缓存到Redis（1小时）- 使用base64编码存储二进制数据
            image_b64 = base64.b64encode(image_content).decode('utf-8')
            await redis.set(cache_key, image_b64, expire=3600)
            
            # 清理临时文件
            os.remove(image_path)
            os.remove(temp_pdf_path)
            
            logger.info(f"生成预览图: {task_id}, 页码: {page}")
            
            return Response(
                content=image_content,
                media_type="image/png",
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "X-Cache": "MISS"
                }
            )
        
        finally:
            # 确保清理临时文件
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成页面预览失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成页面预览失败: {str(e)}")




@router.post("/tasks/{task_id}/draft", response_model=DraftSaveResponse)
async def save_draft(
    task_id: str,
    draft_data: DraftSaveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "auditor"))
):
    """
    保存审核草稿
    
    保存用户修改的草稿数据
    使用Redis存储（TTL 24小时）
    
    Requirements: 30
    """
    try:
        # 验证任务是否存在
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 检查任务状态
        if task.status != TaskStatusEnum.PENDING_AUDIT:
            raise HTTPException(
                status_code=400,
                detail=f"任务状态为{task.status.value}，不允许保存草稿"
            )
        
        # 保存草稿到Redis
        redis = await get_redis()
        draft_key = f"draft:{task_id}:{current_user.id}"
        
        draft_content = {
            "extracted_data": draft_data.extracted_data,
            "saved_at": datetime.utcnow().isoformat(),
            "saved_by": current_user.id
        }
        
        # 设置24小时过期
        await redis.set(
            draft_key,
            json.dumps(draft_content),
            expire=86400  # 24小时
        )
        
        logger.info(f"用户 {current_user.username} 保存审核草稿: {task_id}")
        
        return DraftSaveResponse(
            message="草稿保存成功",
            saved_at=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存草稿失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"保存草稿失败: {str(e)}")


@router.get("/tasks/{task_id}/draft")
async def get_draft(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "auditor"))
):
    """
    获取审核草稿
    
    从Redis加载之前保存的草稿数据
    """
    try:
        # 验证任务是否存在
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 从Redis获取草稿
        redis = await get_redis()
        draft_key = f"draft:{task_id}:{current_user.id}"
        
        draft_content = await redis.get(draft_key)
        
        if not draft_content:
            return {
                "code": 200,
                "message": "无草稿数据",
                "data": None
            }
        
        draft_data = json.loads(draft_content)
        
        logger.info(f"用户 {current_user.username} 获取审核草稿: {task_id}")
        
        return {
            "code": 200,
            "message": "获取草稿成功",
            "data": draft_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取草稿失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取草稿失败: {str(e)}")




@router.post("/tasks/{task_id}/submit", response_model=AuditSubmitResponse)
async def submit_audit(
    task_id: str,
    submit_data: AuditSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "auditor"))
):
    """
    提交审核结果
    
    接收修正后的数据和审核决策（通过/驳回）
    更新任务状态和extracted_data
    记录审核人和审核时间
    触发推送（如果通过）
    清除草稿
    
    Requirements: 17
    """
    try:
        # 查询任务
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 检查任务状态
        if task.status != TaskStatusEnum.PENDING_AUDIT:
            raise HTTPException(
                status_code=400,
                detail=f"任务状态为{task.status.value}，不允许提交审核"
            )
        
        # 验证审核决策（兼容新旧格式）
        decision = submit_data.decision if hasattr(submit_data, 'decision') else None
        action = submit_data.action if hasattr(submit_data, 'action') else None
        
        # 统一处理决策
        if decision:
            final_decision = decision
        elif action:
            final_decision = "approved" if action == "approve" else "rejected"
        else:
            raise HTTPException(
                status_code=400,
                detail="必须提供decision或action字段"
            )
        
        if final_decision not in ["approved", "rejected"]:
            raise HTTPException(
                status_code=400,
                detail="审核决策必须为approved或rejected"
            )
        
        # 记录旧状态
        old_status = task.status.value
        
        # 根据审核决策更新任务状态
        if final_decision == "approved":
            task.status = TaskStatusEnum.COMPLETED
            task.completed_at = datetime.utcnow()
            new_status = "completed"
            
            # 获取提取数据（兼容新旧格式）
            extracted_data = None
            if hasattr(submit_data, 'extracted_data') and submit_data.extracted_data:
                extracted_data = submit_data.extracted_data
            elif hasattr(submit_data, 'data') and submit_data.data:
                extracted_data = submit_data.data
            
            # 如果提供了修正数据，更新提取结果
            if extracted_data:
                task.extracted_data = extracted_data
                
                # 将修正后的字段置信度设置为100（人工确认）
                if task.confidence_scores:
                    for field_name in extracted_data.keys():
                        if field_name in task.confidence_scores:
                            task.confidence_scores[field_name] = 100.0
        
        else:  # rejected
            task.status = TaskStatusEnum.REJECTED
            new_status = "rejected"
        
        # 记录审核信息
        task.auditor_id = current_user.id
        task.audited_at = datetime.utcnow()
        
        # 保存更新
        await db.commit()
        await db.refresh(task)
        
        # 记录审计日志
        audit_log = AuditLog(
            user_id=current_user.id,
            action_type="audit_submit",
            resource_type="task",
            resource_id=task_id,
            changes={
                "old_status": old_status,
                "new_status": new_status,
                "decision": final_decision,
                "comment": submit_data.comment or submit_data.reason,
                "data_modified": (submit_data.extracted_data is not None) or (submit_data.data is not None)
            },
            ip_address=None,
            user_agent=None
        )
        db.add(audit_log)
        await db.commit()
        
        # 清除草稿
        redis = await get_redis()
        draft_key = f"draft:{task_id}:{current_user.id}"
        await redis.delete(draft_key)
        
        # 如果审核通过，触发Pipeline处理（Pipeline会判断是否有管道，然后触发推送）
        if final_decision == "approved":
            try:
                await publish_task("pipeline_tasks", {
                    "task_id": task_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                logger.info(f"任务 {task_id} 审核通过，已加入Pipeline队列")
            except Exception as e:
                logger.error(f"发布Pipeline任务失败: {str(e)}")
        
        # 发送审核完成钉钉通知
        try:
            # 获取规则名称
            rule_name = task.rule.name if task.rule else '未知规则'
            await dingtalk_service.notify_audit_completed(
                task_id=task_id,
                file_name=task.file_name,
                rule_id=str(task.rule_id),
                rule_name=rule_name,
                status=new_status,
                auditor=current_user.username
            )
        except Exception as e:
            logger.warning(f"发送审核完成通知失败: {str(e)}")
        
        logger.info(
            f"用户 {current_user.username} 提交审核: {task_id}, "
            f"决策: {final_decision}"
        )
        
        return AuditSubmitResponse(
            message=f"审核{'通过' if final_decision == 'approved' else '驳回'}成功",
            task_id=task_id,
            new_status=new_status
        )
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"提交审核失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"提交审核失败: {str(e)}")

