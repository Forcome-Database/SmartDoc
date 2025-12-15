"""
文件上传API端点
实现文件上传、哈希去重、任务创建功能
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional
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
from app.schemas.upload import UploadResponse
from app.services.hash_service import hash_service
from app.services.file_service import file_service
from app.services.pdf_service import pdf_service

router = APIRouter(prefix="/ocr", tags=["文件上传"])


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


@router.post("/upload", response_model=UploadResponse, summary="上传文件进行OCR处理")
async def upload_file(
    file: UploadFile = File(..., description="要处理的PDF或图片文件"),
    rule_id: str = Form(..., description="规则ID"),
    rule_version: Optional[str] = Form(None, description="规则版本（可选，默认使用当前发布版本）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传文件进行OCR处理
    
    功能：
    1. 验证文件大小（最大20MB）
    2. 验证文件页数（最大50页）
    3. 验证rule_id参数
    4. 计算文件哈希并判断是否去重（秒传）
    5. 如果未命中，上传文件到MinIO，创建任务记录，发布到队列
    6. 返回任务ID、是否秒传、状态、预估等待时间
    
    Requirements: 13, 29
    """
    try:
        logger.info(f"收到文件上传请求: {file.filename}, 规则: {rule_id}, 用户: {current_user.username}")
        
        # 1. 验证文件类型
        if file.content_type not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file.content_type}。支持的类型: {', '.join(settings.ALLOWED_FILE_TYPES)}"
            )
        
        # 2. 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        # 3. 验证文件大小（最大20MB）
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件大小超过20MB限制。当前大小: {file_size / 1024 / 1024:.2f}MB"
            )
        
        logger.info(f"文件大小验证通过: {file_size / 1024 / 1024:.2f}MB")
        
        # 4. 验证文件页数（仅PDF文件）
        page_count = 1
        if file.content_type == "application/pdf":
            try:
                page_count = pdf_service.get_page_count_from_bytes(file_content)
                logger.info(f"PDF页数: {page_count}")
                
                if page_count > settings.MAX_PAGE_COUNT:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"文件页数超过50页限制。当前页数: {page_count}"
                    )
            except Exception as e:
                logger.error(f"获取PDF页数失败: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无法读取PDF文件: {str(e)}"
                )
        
        # 5. 验证规则
        rule, rule_version_obj = await validate_rule(db, rule_id, rule_version)
        target_version = rule_version_obj.version
        # 使用规则的真实ID（用户可能传入的是code）
        actual_rule_id = rule.id
        
        logger.info(f"规则验证通过: {rule.code} - {target_version}")
        
        # 6. 计算文件哈希
        file_hash = hash_service.calculate_file_hash(file_content)
        logger.info(f"文件哈希: {file_hash}")
        
        # 7. 检查去重（秒传）
        existing_task = await hash_service.check_duplicate(
            db, file_hash, actual_rule_id, target_version
        )
        
        if existing_task:
            # 命中秒传，直接返回历史结果
            logger.info(f"命中秒传: 任务ID {existing_task.id}")
            
            # 获取OCR原始提取结果
            # 如果历史任务有管道执行记录，从 pipeline_executions 的 input_data 中获取原始数据
            # 否则直接使用历史任务的 extracted_data
            original_extracted_data = existing_task.extracted_data
            
            # 查询历史任务的管道执行记录
            exec_stmt = select(PipelineExecution).where(
                PipelineExecution.task_id == existing_task.id
            ).order_by(PipelineExecution.created_at.asc()).limit(1)
            exec_result = await db.execute(exec_stmt)
            first_execution = exec_result.scalar_one_or_none()
            
            if first_execution and first_execution.input_data:
                # 从管道执行记录的 input_data 中获取 OCR 原始提取结果
                input_extracted = first_execution.input_data.get('extracted_data')
                if input_extracted:
                    original_extracted_data = input_extracted
                    logger.info(f"秒传任务使用管道输入的原始提取数据")
            
            # 创建新的秒传任务记录
            instant_task_id = generate_task_id()
            instant_task = Task(
                id=instant_task_id,
                file_name=file.filename,
                file_path=existing_task.file_path,  # 复用历史文件路径
                file_hash=file_hash,
                page_count=page_count,
                rule_id=actual_rule_id,  # 使用规则的真实ID
                rule_version=target_version,
                status=TaskStatus.COMPLETED,
                is_instant=True,  # 标记为秒传
                ocr_text=existing_task.ocr_text,
                ocr_result=existing_task.ocr_result,
                extracted_data=original_extracted_data,  # 使用OCR原始提取结果
                confidence_scores=existing_task.confidence_scores,
                llm_token_count=0,  # 秒传不消耗Token
                llm_cost=0,
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            
            db.add(instant_task)
            await db.commit()
            
            logger.info(f"秒传任务创建成功: {instant_task_id}")
            
            return UploadResponse(
                task_id=instant_task_id,
                is_instant=True,
                status=TaskStatus.COMPLETED.value,
                estimated_wait_seconds=0,
                message="文件已秒传，直接返回历史结果"
            )
        
        # 8. 未命中秒传，创建新任务
        task_id = generate_task_id()
        logger.info(f"创建新任务: {task_id}")
        
        # 9. 上传文件到MinIO
        try:
            file_path = await file_service.upload_to_storage(
                file_content=file_content,
                task_id=task_id,
                filename=file.filename,
                content_type=file.content_type
            )
            logger.info(f"文件上传到MinIO成功: {file_path}")
        except Exception as e:
            logger.error(f"文件上传到MinIO失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"文件上传失败: {str(e)}"
            )
        
        # 10. 创建任务记录
        new_task = Task(
            id=task_id,
            file_name=file.filename,
            file_path=file_path,
            file_hash=file_hash,
            page_count=page_count,
            rule_id=actual_rule_id,  # 使用规则的真实ID
            rule_version=target_version,
            status=TaskStatus.QUEUED,
            is_instant=False,
            created_at=datetime.utcnow()
        )
        
        db.add(new_task)
        await db.commit()
        
        logger.info(f"任务记录创建成功: {task_id}")
        
        # 11. 发布任务到消息队列
        try:
            rabbitmq = await get_rabbitmq()
            task_data = {
                "task_id": task_id,
                "file_path": file_path,
                "rule_id": actual_rule_id,  # 使用规则的真实ID
                "rule_version": target_version,
                "page_count": page_count
            }
            
            success = await rabbitmq.publish_task(
                queue_name=settings.RABBITMQ_QUEUE_OCR,
                task_data=task_data
            )
            
            if not success:
                logger.error(f"任务发布到队列失败: {task_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="任务发布失败"
                )
            
            logger.info(f"任务已发布到队列: {task_id}")
            
        except Exception as e:
            logger.error(f"发布任务到队列异常: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"任务发布失败: {str(e)}"
            )
        
        # 12. 计算预估等待时间
        queue_length = await rabbitmq.get_queue_size(settings.RABBITMQ_QUEUE_OCR)
        estimated_wait_seconds = await calculate_estimated_wait_time(page_count, queue_length)
        
        logger.info(f"任务创建完成: {task_id}, 预估等待时间: {estimated_wait_seconds}秒")
        
        return UploadResponse(
            task_id=task_id,
            is_instant=False,
            status=TaskStatus.QUEUED.value,
            estimated_wait_seconds=estimated_wait_seconds,
            message="文件已上传，正在处理中"
        )
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"文件上传处理异常: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传处理失败: {str(e)}"
        )
