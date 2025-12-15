"""
文件上传API端点
实现文件上传、哈希去重、任务创建功能
支持单文件和多文件上传
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional, List, Union
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.core.logger import logger
from app.core.mq import get_rabbitmq
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.rule import Rule, RuleVersion, RuleStatus
from app.models.pipeline import PipelineExecution
from app.schemas.upload import UploadResponse, BatchUploadResponse, UploadResultItem
from app.services.hash_service import hash_service
from app.services.file_service import file_service
from app.services.pdf_service import pdf_service

router = APIRouter(prefix="/ocr", tags=["文件上传"])

# 批量上传最大文件数
MAX_BATCH_SIZE = 10


def generate_task_id() -> str:
    """
    生成任务ID
    格式: T_YYYYMMDD_序号
    """
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    # 使用UUID的后8位作为序号，确保唯一性
    unique_id = str(uuid.uuid4()).split('-')[-1].upper()
    return f"T_{date_str}_{unique_id}"


async def validate_rule(
    db: AsyncSession,
    rule_id: str,
    rule_version: Optional[str] = None
) -> tuple[Rule, RuleVersion]:
    """
    验证规则是否存在并获取规则配置
    
    Args:
        db: 数据库会话
        rule_id: 规则ID
        rule_version: 规则版本（可选，默认使用当前发布版本）
        
    Returns:
        tuple[Rule, RuleVersion]: 规则对象和规则版本对象
        
    Raises:
        HTTPException: 规则不存在或版本不存在
    """
    # 查询规则（先尝试通过id查询，再尝试通过code查询）
    # 避免使用 or_ 导致匹配多条记录
    stmt = select(Rule).where(Rule.id == rule_id)
    result = await db.execute(stmt)
    rule = result.scalar_one_or_none()
    
    if not rule:
        # 如果通过id没找到，尝试通过code查询
        stmt = select(Rule).where(Rule.code == rule_id)
        result = await db.execute(stmt)
        rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"规则不存在: {rule_id}"
        )
    
    # 确定要使用的版本
    target_version = rule_version or rule.current_version
    
    if not target_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"规则 {rule_id} 没有已发布的版本"
        )
    
    # 查询规则版本（使用rule.id而不是传入的rule_id，因为rule_id可能是code）
    stmt = select(RuleVersion).where(
        RuleVersion.rule_id == rule.id,
        RuleVersion.version == target_version
    )
    result = await db.execute(stmt)
    rule_version_obj = result.scalar_one_or_none()
    
    if not rule_version_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"规则版本不存在: {rule.id} - {target_version}"
        )
    
    # 检查版本状态
    if rule_version_obj.status != RuleStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"规则版本 {target_version} 未发布，无法使用"
        )
    
    return rule, rule_version_obj


async def calculate_estimated_wait_time(
    page_count: int,
    queue_length: int
) -> int:
    """
    计算预估等待时间
    
    Args:
        page_count: 文件页数
        queue_length: 当前队列长度
        
    Returns:
        int: 预估等待时间（秒）
    """
    # 单页处理时间约3秒，多页按2秒/页 + 1秒基础时间
    if page_count == 1:
        task_time = 3
    else:
        task_time = page_count * 2 + 1
    
    # 考虑队列长度，假设平均每个任务10秒
    queue_wait_time = queue_length * 10
    
    # 总等待时间
    total_wait_time = task_time + queue_wait_time
    
    return total_wait_time


async def process_single_file(
    file: UploadFile,
    file_content: bytes,
    rule: Rule,
    rule_version_obj: RuleVersion,
    db: AsyncSession
) -> UploadResultItem:
    """
    处理单个文件上传的核心逻辑
    
    Args:
        file: 上传的文件对象
        file_content: 文件内容
        rule: 规则对象
        rule_version_obj: 规则版本对象
        db: 数据库会话
        
    Returns:
        UploadResultItem: 上传结果
    """
    target_version = rule_version_obj.version
    actual_rule_id = rule.id
    
    # 1. 验证文件类型
    if file.content_type not in settings.ALLOWED_FILE_TYPES:
        return UploadResultItem(
            file_name=file.filename,
            status="failed",
            error=f"不支持的文件类型: {file.content_type}"
        )
    
    # 2. 验证文件大小（最大20MB）
    file_size = len(file_content)
    if file_size > settings.MAX_FILE_SIZE:
        return UploadResultItem(
            file_name=file.filename,
            status="failed",
            error=f"文件大小超过20MB限制，当前: {file_size / 1024 / 1024:.2f}MB"
        )
    
    # 3. 验证文件页数（仅PDF文件）
    page_count = 1
    if file.content_type == "application/pdf":
        try:
            page_count = pdf_service.get_page_count_from_bytes(file_content)
            if page_count > settings.MAX_PAGE_COUNT:
                return UploadResultItem(
                    file_name=file.filename,
                    status="failed",
                    error=f"文件页数超过50页限制，当前: {page_count}页"
                )
        except Exception as e:
            return UploadResultItem(
                file_name=file.filename,
                status="failed",
                error=f"无法读取PDF文件: {str(e)}"
            )
    
    # 4. 计算文件哈希
    file_hash = hash_service.calculate_file_hash(file_content)
    
    # 5. 检查去重（秒传）
    existing_task = await hash_service.check_duplicate(
        db, file_hash, actual_rule_id, target_version
    )
    
    if existing_task:
        # 命中秒传
        logger.info(f"命中秒传: {file.filename} -> 历史任务 {existing_task.id}")
        
        original_extracted_data = existing_task.extracted_data
        
        # 查询历史任务的管道执行记录
        exec_stmt = select(PipelineExecution).where(
            PipelineExecution.task_id == existing_task.id
        ).order_by(PipelineExecution.created_at.asc()).limit(1)
        exec_result = await db.execute(exec_stmt)
        first_execution = exec_result.scalar_one_or_none()
        
        if first_execution and first_execution.input_data:
            input_extracted = first_execution.input_data.get('extracted_data')
            if input_extracted:
                original_extracted_data = input_extracted
        
        # 创建秒传任务记录
        instant_task_id = generate_task_id()
        instant_task = Task(
            id=instant_task_id,
            file_name=file.filename,
            file_path=existing_task.file_path,
            file_hash=file_hash,
            page_count=page_count,
            rule_id=actual_rule_id,
            rule_version=target_version,
            status=TaskStatus.COMPLETED,
            is_instant=True,
            ocr_text=existing_task.ocr_text,
            ocr_result=existing_task.ocr_result,
            extracted_data=original_extracted_data,
            confidence_scores=existing_task.confidence_scores,
            llm_token_count=0,
            llm_cost=0,
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        
        db.add(instant_task)
        await db.flush()
        
        return UploadResultItem(
            file_name=file.filename,
            task_id=instant_task_id,
            is_instant=True,
            status=TaskStatus.COMPLETED.value,
            estimated_wait_seconds=0
        )
    
    # 6. 未命中秒传，创建新任务
    task_id = generate_task_id()
    
    # 7. 上传文件到MinIO
    try:
        file_path = await file_service.upload_to_storage(
            file_content=file_content,
            task_id=task_id,
            filename=file.filename,
            content_type=file.content_type
        )
    except Exception as e:
        return UploadResultItem(
            file_name=file.filename,
            status="failed",
            error=f"文件存储失败: {str(e)}"
        )
    
    # 8. 创建任务记录
    new_task = Task(
        id=task_id,
        file_name=file.filename,
        file_path=file_path,
        file_hash=file_hash,
        page_count=page_count,
        rule_id=actual_rule_id,
        rule_version=target_version,
        status=TaskStatus.QUEUED,
        is_instant=False,
        created_at=datetime.utcnow()
    )
    
    db.add(new_task)
    await db.flush()
    
    # 9. 计算预估等待时间（消息发布移到事务提交后）
    try:
        rabbitmq = await get_rabbitmq()
        queue_length = await rabbitmq.get_queue_size(settings.RABBITMQ_QUEUE_OCR)
        estimated_wait_seconds = await calculate_estimated_wait_time(page_count, queue_length)
        
        logger.info(f"任务创建完成: {task_id}, 预估等待: {estimated_wait_seconds}秒")
        
        # 返回待发布的任务信息，消息发布将在事务提交后执行
        return UploadResultItem(
            file_name=file.filename,
            task_id=task_id,
            is_instant=False,
            status=TaskStatus.QUEUED.value,
            estimated_wait_seconds=estimated_wait_seconds,
            # 临时存储发布所需数据
            pending_publish={
                "task_id": task_id,
                "file_path": file_path,
                "rule_id": actual_rule_id,
                "rule_version": target_version,
                "page_count": page_count
            }
        )
        
    except Exception as e:
        logger.error(f"任务创建异常 [{task_id}]: {str(e)}", exc_info=True)
        return UploadResultItem(
            file_name=file.filename,
            task_id=task_id,
            status="failed",
            error=f"任务创建失败: {str(e)}"
        )


@router.post(
    "/upload",
    response_model=Union[UploadResponse, BatchUploadResponse],
    summary="上传文件进行OCR处理（支持单文件/多文件）"
)
async def upload_file(
    files: List[UploadFile] = File(..., description="上传文件（支持单个或多个）"),
    rule_id: str = Form(..., description="规则ID"),
    rule_version: Optional[str] = Form(None, description="规则版本（可选，默认使用当前发布版本）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传文件进行OCR处理（支持单文件和多文件）
    
    统一使用 files 参数上传文件，支持单个或多个文件。
    
    功能：
    1. 支持单文件上传（返回 UploadResponse）
    2. 支持多文件上传（返回 BatchUploadResponse，最多10个文件）
    3. 验证文件大小（最大20MB/文件）
    4. 验证文件页数（最大50页/文件）
    5. 计算文件哈希并判断是否去重（秒传）
    6. 上传文件到MinIO，创建任务记录，发布到队列
    
    Requirements: 13, 29
    """
    try:
        # 过滤有效文件（排除空文件名的占位文件）
        all_files = [f for f in files if f and f.filename]
        
        # 检查是否有文件
        if not all_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请上传至少一个文件"
            )
        
        # 验证文件数量
        if len(all_files) > MAX_BATCH_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"单次最多上传{MAX_BATCH_SIZE}个文件，当前: {len(all_files)}个"
            )
        
        # 预先验证规则（只验证一次）
        rule, rule_version_obj = await validate_rule(db, rule_id, rule_version)
        
        logger.info(f"收到文件上传请求: {len(all_files)}个文件, 规则: {rule.code}, 用户: {current_user.username}")
        
        # 单文件上传：保持原有响应格式
        if len(all_files) == 1:
            single_file = all_files[0]
            file_content = await single_file.read()
            
            result = await process_single_file(
                file=single_file,
                file_content=file_content,
                rule=rule,
                rule_version_obj=rule_version_obj,
                db=db
            )
            
            # 如果处理失败，抛出异常
            if result.error:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error
                )
            
            # 先提交事务，确保任务记录已持久化
            await db.commit()
            
            # 事务提交后，发布消息到队列
            if result.pending_publish:
                try:
                    logger.info(f"准备发布任务到队列: {result.pending_publish['task_id']}")
                    rabbitmq = await get_rabbitmq()
                    success = await rabbitmq.publish_task(
                        queue_name=settings.RABBITMQ_QUEUE_OCR,
                        task_data=result.pending_publish
                    )
                    if not success:
                        logger.error(f"任务发布到队列失败: {result.pending_publish['task_id']}")
                except Exception as e:
                    logger.error(f"任务发布异常: {str(e)}", exc_info=True)
            
            return UploadResponse(
                task_id=result.task_id,
                is_instant=result.is_instant,
                status=result.status,
                estimated_wait_seconds=result.estimated_wait_seconds,
                message="文件已秒传，直接返回历史结果" if result.is_instant else "文件已上传，正在处理中"
            )
        
        # 多文件上传：返回批量响应
        results = []
        success_count = 0
        pending_publishes = []
        
        for upload_file in all_files:
            try:
                file_content = await upload_file.read()
                result = await process_single_file(
                    file=upload_file,
                    file_content=file_content,
                    rule=rule,
                    rule_version_obj=rule_version_obj,
                    db=db
                )
                results.append(result)
                if not result.error:
                    success_count += 1
                    # 收集待发布的任务
                    if result.pending_publish:
                        pending_publishes.append(result.pending_publish)
            except Exception as e:
                logger.error(f"处理文件 {upload_file.filename} 失败: {str(e)}")
                results.append(UploadResultItem(
                    file_name=upload_file.filename,
                    status="failed",
                    error=str(e)
                ))
        
        # 先提交事务，确保所有任务记录已持久化
        await db.commit()
        
        # 事务提交后，批量发布消息到队列
        if pending_publishes:
            try:
                rabbitmq = await get_rabbitmq()
                for task_data in pending_publishes:
                    logger.info(f"准备发布任务到队列: {task_data['task_id']}")
                    success = await rabbitmq.publish_task(
                        queue_name=settings.RABBITMQ_QUEUE_OCR,
                        task_data=task_data
                    )
                    if not success:
                        logger.error(f"任务发布到队列失败: {task_data['task_id']}")
            except Exception as e:
                logger.error(f"批量任务发布异常: {str(e)}", exc_info=True)
        
        return BatchUploadResponse(
            total=len(all_files),
            success_count=success_count,
            failed_count=len(all_files) - success_count,
            results=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传处理异常: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传处理失败: {str(e)}"
        )
