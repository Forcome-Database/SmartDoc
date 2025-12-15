"""
数据处理管道API端点
实现管道的CRUD、测试执行和执行记录查询
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.logger import logger
from app.models.user import User
from app.models.pipeline import (
    Pipeline, PipelineExecution, 
    PipelineStatus, ExecutionStatus,
    generate_pipeline_id
)
from app.models.rule import Rule
from app.schemas.pipeline import (
    PipelineCreate, PipelineUpdate, PipelineResponse,
    PipelineListResponse, PipelineTestRequest, PipelineTestResponse,
    ExecutionListResponse, ExecutionDetail
)
from app.services.pipeline_service import PipelineService, PipelineExecutor


router = APIRouter(prefix="/pipelines", tags=["数据处理管道"])


@router.post("", response_model=PipelineResponse, summary="创建管道")
async def create_pipeline(
    data: PipelineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "architect"))
):
    """
    创建数据处理管道
    
    - 每个规则只能关联一个管道
    - 支持配置Python脚本和依赖包
    """
    try:
        # 检查规则是否存在
        stmt = select(Rule).where(Rule.id == data.rule_id)
        result = await db.execute(stmt)
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(status_code=404, detail=f"规则不存在: {data.rule_id}")
        
        # 检查规则是否已有管道
        stmt = select(Pipeline).where(Pipeline.rule_id == data.rule_id)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"规则 {data.rule_id} 已关联管道 {existing.id}"
            )
        
        # 创建管道
        pipeline = Pipeline(
            id=generate_pipeline_id(),
            name=data.name,
            description=data.description,
            rule_id=data.rule_id,
            script_content=data.script_content,
            requirements=data.requirements,
            timeout_seconds=data.timeout_seconds or 300,
            max_retries=data.max_retries or 1,
            memory_limit_mb=data.memory_limit_mb or 512,
            env_variables=data.env_variables,
            status="draft",
            created_by=current_user.id
        )
        
        db.add(pipeline)
        await db.commit()
        await db.refresh(pipeline)
        
        logger.info(f"用户 {current_user.username} 创建管道: {pipeline.id}")
        
        return PipelineResponse.model_validate(pipeline)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"创建管道失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建管道失败: {str(e)}")


@router.get("", response_model=PipelineListResponse, summary="获取管道列表")
async def list_pipelines(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    rule_id: Optional[str] = Query(None, description="规则ID筛选"),
    status: Optional[PipelineStatus] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取管道列表"""
    try:
        conditions = []
        
        if rule_id:
            conditions.append(Pipeline.rule_id == rule_id)
        if status:
            conditions.append(Pipeline.status == status)
        if keyword:
            conditions.append(Pipeline.name.like(f"%{keyword}%"))
        
        # 查询总数
        count_query = select(func.count()).select_from(Pipeline)
        if conditions:
            from sqlalchemy import and_
            count_query = count_query.where(and_(*conditions))
        
        result = await db.execute(count_query)
        total = result.scalar()
        
        # 分页查询
        query = select(Pipeline).order_by(desc(Pipeline.created_at))
        if conditions:
            from sqlalchemy import and_
            query = query.where(and_(*conditions))
        
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        pipelines = result.scalars().all()
        
        return PipelineListResponse(
            items=[PipelineResponse.model_validate(p) for p in pipelines],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
        
    except Exception as e:
        logger.error(f"获取管道列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取管道列表失败: {str(e)}")


@router.get("/{pipeline_id}", response_model=PipelineResponse, summary="获取管道详情")
async def get_pipeline(
    pipeline_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取管道详情"""
    stmt = select(Pipeline).where(Pipeline.id == pipeline_id)
    result = await db.execute(stmt)
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="管道不存在")
    
    return PipelineResponse.model_validate(pipeline)


@router.put("/{pipeline_id}", response_model=PipelineResponse, summary="更新管道")
async def update_pipeline(
    pipeline_id: str,
    data: PipelineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "architect"))
):
    """更新管道配置"""
    try:
        stmt = select(Pipeline).where(Pipeline.id == pipeline_id)
        result = await db.execute(stmt)
        pipeline = result.scalar_one_or_none()
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="管道不存在")
        
        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(pipeline, key, value)
        
        pipeline.updated_at = datetime.utcnow()
        
        # 如果更新了依赖，需要重建环境
        if 'requirements' in update_data:
            executor = PipelineExecutor()
            executor.cleanup_venv(pipeline_id)
        
        await db.commit()
        await db.refresh(pipeline)
        
        logger.info(f"用户 {current_user.username} 更新管道: {pipeline_id}")
        
        return PipelineResponse.model_validate(pipeline)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新管道失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新管道失败: {str(e)}")


@router.delete("/{pipeline_id}", summary="删除管道")
async def delete_pipeline(
    pipeline_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """删除管道"""
    try:
        stmt = select(Pipeline).where(Pipeline.id == pipeline_id)
        result = await db.execute(stmt)
        pipeline = result.scalar_one_or_none()
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="管道不存在")
        
        # 清理虚拟环境
        executor = PipelineExecutor()
        executor.cleanup_venv(pipeline_id)
        
        await db.delete(pipeline)
        await db.commit()
        
        logger.info(f"用户 {current_user.username} 删除管道: {pipeline_id}")
        
        return {"code": 200, "message": "删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除管道失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除管道失败: {str(e)}")


@router.post("/{pipeline_id}/activate", summary="激活管道")
async def activate_pipeline(
    pipeline_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "architect"))
):
    """激活管道，使其在任务处理时生效"""
    try:
        stmt = select(Pipeline).where(Pipeline.id == pipeline_id)
        result = await db.execute(stmt)
        pipeline = result.scalar_one_or_none()
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="管道不存在")
        
        pipeline.status = "active"
        pipeline.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"用户 {current_user.username} 激活管道: {pipeline_id}")
        
        return {"code": 200, "message": "管道已激活"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"激活管道失败: {str(e)}")


@router.post("/{pipeline_id}/deactivate", summary="停用管道")
async def deactivate_pipeline(
    pipeline_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "architect"))
):
    """停用管道"""
    try:
        stmt = select(Pipeline).where(Pipeline.id == pipeline_id)
        result = await db.execute(stmt)
        pipeline = result.scalar_one_or_none()
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="管道不存在")
        
        pipeline.status = "inactive"
        pipeline.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"用户 {current_user.username} 停用管道: {pipeline_id}")
        
        return {"code": 200, "message": "管道已停用"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"停用管道失败: {str(e)}")


@router.post("/{pipeline_id}/test", response_model=PipelineTestResponse, summary="测试管道")
async def test_pipeline(
    pipeline_id: str,
    data: PipelineTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "architect"))
):
    """
    测试管道脚本
    
    使用提供的测试数据执行管道脚本，返回执行结果
    """
    try:
        stmt = select(Pipeline).where(Pipeline.id == pipeline_id)
        result = await db.execute(stmt)
        pipeline = result.scalar_one_or_none()
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="管道不存在")
        
        # 准备测试输入数据
        input_data = {
            'task_id': 'TEST_TASK',
            'extracted_data': data.test_data or {},
            'ocr_text': data.ocr_text or '',
            'meta_info': {
                'file_name': 'test.pdf',
                'page_count': 1,
                'rule_id': pipeline.rule_id,
                'rule_version': 'test',
                'confidence_scores': {},
                'created_at': datetime.utcnow().isoformat(),
            }
        }
        
        # 执行测试
        executor = PipelineExecutor()
        success, output_data, stdout, stderr, error_msg = await executor.execute(
            pipeline=pipeline,
            input_data=input_data,
            timeout=60  # 测试超时60秒
        )
        
        logger.info(f"用户 {current_user.username} 测试管道: {pipeline_id}, 结果: {success}")
        
        return PipelineTestResponse(
            success=success,
            output_data=output_data,
            stdout=stdout,
            stderr=stderr,
            error_message=error_msg
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试管道失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"测试管道失败: {str(e)}")


@router.get("/{pipeline_id}/executions", response_model=ExecutionListResponse, summary="获取执行记录")
async def list_executions(
    pipeline_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[ExecutionStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取管道的执行记录列表"""
    try:
        conditions = [PipelineExecution.pipeline_id == pipeline_id]
        
        if status:
            conditions.append(PipelineExecution.status == status)
        
        from sqlalchemy import and_
        
        # 查询总数
        count_query = select(func.count()).select_from(PipelineExecution).where(and_(*conditions))
        result = await db.execute(count_query)
        total = result.scalar()
        
        # 分页查询
        query = (
            select(PipelineExecution)
            .where(and_(*conditions))
            .order_by(desc(PipelineExecution.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(query)
        executions = result.scalars().all()
        
        return ExecutionListResponse(
            items=[ExecutionDetail.model_validate(e) for e in executions],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
        
    except Exception as e:
        logger.error(f"获取执行记录失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取执行记录失败: {str(e)}")


@router.get("/executions/{execution_id}", response_model=ExecutionDetail, summary="获取执行详情")
async def get_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取执行记录详情"""
    stmt = select(PipelineExecution).where(PipelineExecution.id == execution_id)
    result = await db.execute(stmt)
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    
    return ExecutionDetail.model_validate(execution)


@router.get("/by-rule/{rule_id}", response_model=PipelineResponse, summary="根据规则获取管道")
async def get_pipeline_by_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据规则ID获取关联的管道"""
    stmt = select(Pipeline).where(Pipeline.rule_id == rule_id)
    result = await db.execute(stmt)
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="该规则没有关联的管道")
    
    return PipelineResponse.model_validate(pipeline)
