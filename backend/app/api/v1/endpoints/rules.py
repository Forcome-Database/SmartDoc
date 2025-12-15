# -*- coding: utf-8 -*-
"""
规则管理端点
实现规则的CRUD、版本管理、发布、回滚和沙箱测试功能
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime
import uuid
import json
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_architect
from app.core.config import settings
from app.models.user import User, RoleEnum
from app.models.rule import Rule, RuleVersion, RuleStatus
from app.models.task import Task
from app.schemas.rule import (
    RuleCreate, RuleUpdate, RuleListQuery, RuleListResponse, RuleListItem,
    RuleDetail, RuleVersionListResponse, RuleVersionItem, RuleConfigUpdate,
    RulePublishRequest, RuleRollbackRequest, SandboxTestRequest,
    SandboxTestResponse, RuleResponse, RuleImportData, RuleImportResponse
)

router = APIRouter(prefix="/rules", tags=["规则管理"])
logger = logging.getLogger(__name__)


def _set_nested_value(data: dict, path: str, value) -> None:
    """
    将扁平路径的值设置到嵌套字典中，支持深度合并
    
    例如：
    - path="jianyi2.yinyue", value="xxx" 
    - 结果: data["jianyi2"]["yinyue"] = "xxx"
    
    - path="jianyi2", value={"fengge": "yyy"}
    - 如果 data["jianyi2"] 已存在，会合并而不是覆盖
    
    Args:
        data: 目标字典
        path: 点号分隔的路径
        value: 要设置的值
    """
    parts = path.split('.')
    
    if len(parts) == 1:
        # 顶层字段
        key = parts[0]
        if key in data:
            existing = data[key]
            if isinstance(existing, dict) and isinstance(value, dict):
                # 两者都是字典，深度合并
                _deep_merge(existing, value)
            elif isinstance(existing, dict) and not isinstance(value, dict):
                # 已存在的是字典，新值不是字典，保留已存在的（可能是子字段已设置）
                pass
            elif not isinstance(existing, dict) and isinstance(value, dict):
                # 已存在的不是字典，新值是字典，用字典替换
                data[key] = value
            else:
                # 两者都不是字典，直接覆盖
                data[key] = value
        else:
            data[key] = value
    else:
        # 嵌套字段
        current = data
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                # 如果已存在但不是字典，转换为字典
                current[part] = {}
            current = current[part]
        
        # 设置最终值
        final_key = parts[-1]
        if final_key in current and isinstance(current[final_key], dict) and isinstance(value, dict):
            _deep_merge(current[final_key], value)
        else:
            current[final_key] = value


def _deep_merge(base: dict, update: dict) -> None:
    """
    深度合并两个字典，update 中的值会合并到 base 中
    
    Args:
        base: 基础字典（会被修改）
        update: 要合并的字典
    """
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def _get_nested_value(data: dict, path: str):
    """
    从嵌套字典中获取值
    
    Args:
        data: 数据字典
        path: 点号分隔的路径，如 "jianyi.fengge"
        
    Returns:
        字段值，如果不存在返回None
    """
    if not data or not path:
        return None
    
    parts = path.split('.')
    current = data
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    
    return current


def _get_nested_schema(schema: dict, path: str) -> dict:
    """
    从Schema中获取嵌套字段的定义
    
    Args:
        schema: Schema定义
        path: 点号分隔的路径，如 "jianyi.fengge"
        
    Returns:
        字段的schema定义，如果不存在返回None
    """
    if not schema or not path:
        return None
    
    parts = path.split('.')
    current = schema
    
    for i, part in enumerate(parts):
        if part not in current:
            return None
        
        node = current[part]
        
        # 如果是最后一个部分，返回该节点
        if i == len(parts) - 1:
            return node
        
        # 继续向下查找
        node_type = node.get('nodeType', 'field')
        if node_type == 'object' and 'properties' in node:
            current = node['properties']
        elif node_type == 'array' and 'items' in node:
            current = node['items']
        elif node_type == 'table' and 'columns' in node:
            current = node['columns']
        else:
            return None
    
    return None


def generate_rule_code(name: str) -> str:
    """
    生成规则编码

    Args:
        name: 规则名称

    Returns:
        str: 规则编码（格式：RULE_YYYYMMDD_XXXX）
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_suffix = str(uuid.uuid4())[:4].upper()
    return f"RULE_{timestamp}_{random_suffix}"


@router.get("", response_model=RuleListResponse, summary="获取规则列表")
async def get_rules(
    page: int = 1,
    page_size: int = 20,
    document_type: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取规则列表

    - 支持分页
    - 支持按document_type筛选
    - 支持按名称或编码搜索
    - 返回规则基本信息和关联任务数

    Args:
        page: 页码
        page_size: 每页数量
        document_type: 文档类型筛选
        search: 搜索关键词
        db: 数据库会话
        current_user: 当前用户

    Returns:
        RuleListResponse: 规则列表响应
    """
    # 构建查询条件
    conditions = []

    if document_type:
        conditions.append(Rule.document_type == document_type)

    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                Rule.name.like(search_pattern),
                Rule.code.like(search_pattern)
            )
        )

    # 查询总数
    count_query = select(func.count(Rule.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 查询规则列表（预加载creator关系）
    query = select(Rule).options(selectinload(Rule.creator)).order_by(desc(Rule.created_at))

    if conditions:
        query = query.where(and_(*conditions))

    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    rules = result.scalars().all()

    # 批量查询所有规则的任务数（优化性能，避免N+1查询）
    rule_ids = [rule.id for rule in rules]
    task_count_dict = {}
    
    if rule_ids:
        # 一次性查询所有规则的任务数
        task_count_query = select(
            Task.rule_id,
            func.count(Task.id).label('count')
        ).where(
            Task.rule_id.in_(rule_ids)
        ).group_by(Task.rule_id)
        
        task_count_result = await db.execute(task_count_query)
        task_count_dict = {row.rule_id: row.count for row in task_count_result}

    # 构建响应数据
    items = []
    for rule in rules:
        # 从字典中获取任务数
        task_count = task_count_dict.get(rule.id, 0)

        # 获取创建人姓名
        creator_name = None
        if rule.creator:
            creator_name = rule.creator.username

        # 确定规则状态（基于当前版本）
        status = "draft"  # 默认为草稿
        if rule.current_version:
            # 有发布版本，状态为已发布
            status = "published"
        
        items.append(RuleListItem(
            id=rule.id,
            name=rule.name,
            code=rule.code,
            document_type=rule.document_type,
            current_version=rule.current_version,
            status=status,
            created_by=rule.created_by,
            creator_name=creator_name,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
            task_count=task_count
        ))

    # 计算总页数
    total_pages = (total + page_size - 1) // page_size

    return RuleListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("", response_model=RuleResponse, summary="创建规则")
async def create_rule(
    rule_data: RuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_architect)
):
    """
    创建新规则

    - 仅Admin和Architect角色可访问
    - 自动生成唯一规则编码
    - 创建初始草稿版本（V0.0）

    Args:
        rule_data: 规则创建数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        RuleResponse: 创建结果

    Raises:
        HTTPException: 400 - 规则编码已存在
    """
    # 生成规则ID和编码
    rule_id = str(uuid.uuid4())
    rule_code = generate_rule_code(rule_data.name)

    # 检查编码是否已存在（理论上不会重复，但保险起见）
    existing_rule = await db.execute(
        select(Rule).where(Rule.code == rule_code)
    )
    if existing_rule.scalar_one_or_none():
        # 如果重复，重新生成
        rule_code = generate_rule_code(
            rule_data.name) + "_" + str(uuid.uuid4())[:4]

    # 创建规则记录
    new_rule = Rule(
        id=rule_id,
        name=rule_data.name,
        code=rule_code,
        document_type=rule_data.document_type,
        current_version=None,  # 初始没有发布版本
        created_by=current_user.id
    )

    db.add(new_rule)

    # 创建初始草稿版本
    initial_version = RuleVersion(
        rule_id=rule_id,
        version="V0.0",
        status=RuleStatus.DRAFT,
        config={
            "extraction_rules": [],
            "validation_rules": [],
            "llm_config": {}
        }
    )

    db.add(initial_version)

    try:
        await db.commit()
        await db.refresh(new_rule)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建规则失败: {str(e)}"
        )

    return RuleResponse(
        id=new_rule.id,
        message=f"规则创建成功，编码: {rule_code}"
    )


@router.post("/import", response_model=RuleImportResponse, summary="导入规则")
async def import_rule(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_architect)
):
    """
    从JSON文件导入规则

    - 仅Admin和Architect角色可访问
    - 支持导入由导出功能生成的JSON文件
    - 自动生成新的规则ID和编码
    - 导入的规则配置将作为草稿版本

    Args:
        file: 上传的JSON文件
        db: 数据库会话
        current_user: 当前用户

    Returns:
        RuleImportResponse: 导入结果

    Raises:
        HTTPException: 400 - 文件格式错误或内容无效
    """
    # 验证文件类型
    if not file.filename.endswith('.json'):
        return RuleImportResponse(
            success=False,
            message="仅支持JSON文件格式"
        )
    
    try:
        # 读取并解析JSON内容
        content = await file.read()
        try:
            import_data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            return RuleImportResponse(
                success=False,
                message=f"JSON解析失败: {str(e)}"
            )
        
        # 验证必要字段
        if not isinstance(import_data, dict):
            return RuleImportResponse(
                success=False,
                message="无效的规则数据格式"
            )
        
        rule_name = import_data.get('name')
        if not rule_name:
            return RuleImportResponse(
                success=False,
                message="规则名称不能为空"
            )
        
        # 生成新的规则ID和编码
        rule_id = str(uuid.uuid4())
        rule_code = generate_rule_code(rule_name)
        
        # 检查编码是否已存在
        existing_rule = await db.execute(
            select(Rule).where(Rule.code == rule_code)
        )
        if existing_rule.scalar_one_or_none():
            rule_code = generate_rule_code(rule_name) + "_" + str(uuid.uuid4())[:4]
        
        # 提取规则配置
        # 支持两种格式：current_config（导出格式）或直接的config字段
        rule_config = import_data.get('current_config') or import_data.get('config') or {
            "extraction_rules": [],
            "validation_rules": [],
            "llm_config": {}
        }
        
        # 创建规则记录
        new_rule = Rule(
            id=rule_id,
            name=rule_name,
            code=rule_code,
            document_type=import_data.get('document_type'),
            current_version=None,
            created_by=current_user.id
        )
        db.add(new_rule)
        
        # 创建草稿版本，包含导入的配置
        initial_version = RuleVersion(
            rule_id=rule_id,
            version="V0.0",
            status=RuleStatus.DRAFT,
            config=rule_config
        )
        db.add(initial_version)
        
        await db.commit()
        await db.refresh(new_rule)
        
        logger.info(f"规则导入成功: {rule_name} ({rule_code}), 操作人: {current_user.username}")
        
        return RuleImportResponse(
            success=True,
            id=new_rule.id,
            code=new_rule.code,
            message=f"规则导入成功，编码: {rule_code}"
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"规则导入失败: {str(e)}")
        return RuleImportResponse(
            success=False,
            message=f"导入失败: {str(e)}"
        )


@router.get("/{rule_id}", response_model=RuleDetail, summary="获取规则详情")
async def get_rule_detail(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取规则详情

    - 返回规则基本信息
    - 返回当前发布版本的配置
    - 返回统计信息（任务数、版本数）

    Args:
        rule_id: 规则ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        RuleDetail: 规则详情

    Raises:
        HTTPException: 404 - 规则不存在
    """
    # 查询规则（预加载creator关系）
    result = await db.execute(
        select(Rule).options(selectinload(Rule.creator)).where(Rule.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="规则不存在"
        )

    # 获取当前发布版本的配置
    current_config = None
    if rule.current_version:
        version_result = await db.execute(
            select(RuleVersion).where(
                and_(
                    RuleVersion.rule_id == rule_id,
                    RuleVersion.version == rule.current_version,
                    RuleVersion.status == RuleStatus.PUBLISHED
                )
            )
        )
        current_version = version_result.scalar_one_or_none()
        if current_version:
            current_config = current_version.config

    # 查询关联任务数
    task_count_query = select(func.count(Task.id)).where(
        Task.rule_id == rule_id)
    task_count_result = await db.execute(task_count_query)
    task_count = task_count_result.scalar() or 0

    # 查询版本数量
    version_count_query = select(func.count(RuleVersion.id)).where(
        RuleVersion.rule_id == rule_id)
    version_count_result = await db.execute(version_count_query)
    version_count = version_count_result.scalar() or 0

    # 获取创建人姓名
    creator_name = None
    if rule.creator:
        creator_name = rule.creator.username

    return RuleDetail(
        id=rule.id,
        name=rule.name,
        code=rule.code,
        document_type=rule.document_type,
        current_version=rule.current_version,
        created_by=rule.created_by,
        creator_name=creator_name,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        current_config=current_config,
        task_count=task_count,
        version_count=version_count
    )


@router.get("/{rule_id}/versions", response_model=RuleVersionListResponse, summary="获取规则版本列表")
async def get_rule_versions(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取规则的所有版本历史

    - 返回所有版本（草稿、已发布、归档）
    - 按版本号降序排列
    - 包含发布人信息

    Args:
        rule_id: 规则ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        RuleVersionListResponse: 版本列表响应

    Raises:
        HTTPException: 404 - 规则不存在
    """
    # 检查规则是否存在
    rule_result = await db.execute(
        select(Rule).where(Rule.id == rule_id)
    )
    rule = rule_result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="规则不存在"
        )

    # 查询所有版本（预加载publisher关系）
    query = select(RuleVersion).options(selectinload(RuleVersion.publisher)).where(
        RuleVersion.rule_id == rule_id
    ).order_by(desc(RuleVersion.version))

    result = await db.execute(query)
    versions = result.scalars().all()

    # 构建响应数据
    items = []
    for version in versions:
        # 获取发布人姓名
        publisher_name = None
        if version.publisher:
            publisher_name = version.publisher.username

        items.append(RuleVersionItem(
            id=version.id,
            version=version.version,
            status=version.status,
            config=version.config,
            published_at=version.published_at,
            published_by=version.published_by,
            publisher_name=publisher_name,
            created_at=version.created_at
        ))

    return RuleVersionListResponse(
        items=items,
        total=len(items)
    )


@router.put("/{rule_id}/versions/{version_id}", response_model=RuleResponse, summary="更新规则配置")
async def update_rule_config(
    rule_id: str,
    version_id: int,
    config_data: RuleConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_architect)
):
    """
    更新草稿版本的配置内容

    - 仅Admin和Architect角色可访问
    - 只能更新草稿状态的版本
    - 验证配置JSON格式

    Args:
        rule_id: 规则ID
        version_id: 版本ID
        config_data: 配置更新数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        RuleResponse: 更新结果

    Raises:
        HTTPException: 404 - 规则或版本不存在
        HTTPException: 400 - 版本不是草稿状态
    """
    # 查询规则
    rule_result = await db.execute(
        select(Rule).where(Rule.id == rule_id)
    )
    rule = rule_result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="规则不存在"
        )

    # 查询版本
    version_result = await db.execute(
        select(RuleVersion).where(
            and_(
                RuleVersion.id == version_id,
                RuleVersion.rule_id == rule_id
            )
        )
    )
    version = version_result.scalar_one_or_none()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="版本不存在"
        )

    # 检查版本状态
    if version.status != RuleStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能更新草稿状态的版本"
        )

    # 验证配置格式（基本验证）
    try:
        config = config_data.config
        # 确保必要的字段存在
        if not isinstance(config, dict):
            raise ValueError("配置必须是JSON对象")

        # 可以添加更多的配置验证逻辑
        # 例如：验证extraction_rules、validation_rules等字段的格式

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"配置格式无效: {str(e)}"
        )

    # 更新配置
    version.config = config
    rule.updated_at = datetime.utcnow()

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新配置失败: {str(e)}"
        )

    return RuleResponse(
        id=rule_id,
        message="配置更新成功"
    )


@router.post("/{rule_id}/publish", response_model=RuleResponse, summary="发布规则")
async def publish_rule(
    rule_id: str,
    publish_data: RulePublishRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_architect)
):
    """
    发布规则版本

    - 仅Admin和Architect角色可访问
    - 将草稿版本发布为新版本（V1.0、V1.1等）
    - 将当前发布版本归档
    - 更新规则的current_version
    - 清除Redis缓存

    Args:
        rule_id: 规则ID
        publish_data: 发布请求数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        RuleResponse: 发布结果

    Raises:
        HTTPException: 404 - 规则或版本不存在
        HTTPException: 400 - 版本不是草稿状态
    """
    # 查询规则
    rule_result = await db.execute(
        select(Rule).where(Rule.id == rule_id)
    )
    rule = rule_result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="规则不存在"
        )

    # 查询要发布的版本
    version_result = await db.execute(
        select(RuleVersion).where(
            and_(
                RuleVersion.id == publish_data.version_id,
                RuleVersion.rule_id == rule_id
            )
        )
    )
    version = version_result.scalar_one_or_none()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="版本不存在"
        )

    # 检查版本状态
    if version.status != RuleStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能发布草稿状态的版本"
        )

    # 将当前发布版本归档
    if rule.current_version:
        current_version_result = await db.execute(
            select(RuleVersion).where(
                and_(
                    RuleVersion.rule_id == rule_id,
                    RuleVersion.version == rule.current_version,
                    RuleVersion.status == RuleStatus.PUBLISHED
                )
            )
        )
        current_version = current_version_result.scalar_one_or_none()
        if current_version:
            current_version.status = RuleStatus.ARCHIVED

    # 生成新版本号
    # 查询最大版本号
    max_version_result = await db.execute(
        select(RuleVersion.version).where(
            and_(
                RuleVersion.rule_id == rule_id,
                RuleVersion.status.in_(
                    [RuleStatus.PUBLISHED, RuleStatus.ARCHIVED])
            )
        ).order_by(desc(RuleVersion.version)).limit(1)
    )
    max_version = max_version_result.scalar_one_or_none()

    if max_version:
        # 解析版本号并递增
        try:
            version_parts = max_version.replace("V", "").split(".")
            major = int(version_parts[0])
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0
            new_version = f"V{major}.{minor + 1}"
        except:
            new_version = "V1.0"
    else:
        new_version = "V1.0"

    # 更新版本信息
    version.version = new_version
    version.status = RuleStatus.PUBLISHED
    version.published_at = datetime.utcnow()
    version.published_by = current_user.id

    # 更新规则的当前版本
    rule.current_version = new_version
    rule.updated_at = datetime.utcnow()

    # 创建新的草稿版本
    new_draft = RuleVersion(
        rule_id=rule_id,
        version="V0.0",
        status=RuleStatus.DRAFT,
        config=version.config.copy()  # 复制当前配置作为新草稿的起点
    )
    db.add(new_draft)

    try:
        await db.commit()

        # TODO: 清除Redis缓存
        # await redis.delete(f"rule_config:{rule_id}")

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发布规则失败: {str(e)}"
        )

    return RuleResponse(
        id=rule_id,
        message=f"规则发布成功，版本: {new_version}"
    )


@router.post("/{rule_id}/rollback", response_model=RuleResponse, summary="回滚规则")
async def rollback_rule(
    rule_id: str,
    rollback_data: RuleRollbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_architect)
):
    """
    回滚规则到指定历史版本

    - 仅Admin和Architect角色可访问
    - 将指定历史版本恢复为已发布状态
    - 将当前版本归档
    - 清除Redis缓存

    Args:
        rule_id: 规则ID
        rollback_data: 回滚请求数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        RuleResponse: 回滚结果

    Raises:
        HTTPException: 404 - 规则或版本不存在
        HTTPException: 400 - 版本不是归档状态
    """
    # 查询规则
    rule_result = await db.execute(
        select(Rule).where(Rule.id == rule_id)
    )
    rule = rule_result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="规则不存在"
        )

    # 查询要回滚的版本
    target_version_result = await db.execute(
        select(RuleVersion).where(
            and_(
                RuleVersion.id == rollback_data.version_id,
                RuleVersion.rule_id == rule_id
            )
        )
    )
    target_version = target_version_result.scalar_one_or_none()

    if not target_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标版本不存在"
        )

    # 检查版本状态（只能回滚归档版本）
    if target_version.status != RuleStatus.ARCHIVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能回滚归档状态的版本"
        )

    # 将当前发布版本归档
    if rule.current_version:
        current_version_result = await db.execute(
            select(RuleVersion).where(
                and_(
                    RuleVersion.rule_id == rule_id,
                    RuleVersion.version == rule.current_version,
                    RuleVersion.status == RuleStatus.PUBLISHED
                )
            )
        )
        current_version = current_version_result.scalar_one_or_none()
        if current_version:
            current_version.status = RuleStatus.ARCHIVED

    # 恢复目标版本为已发布状态
    target_version.status = RuleStatus.PUBLISHED
    target_version.published_at = datetime.utcnow()
    target_version.published_by = current_user.id

    # 更新规则的当前版本
    rule.current_version = target_version.version
    rule.updated_at = datetime.utcnow()

    try:
        await db.commit()

        # TODO: 清除Redis缓存
        # await redis.delete(f"rule_config:{rule_id}")

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"回滚规则失败: {str(e)}"
        )

    return RuleResponse(
        id=rule_id,
        message=f"规则回滚成功，当前版本: {target_version.version}"
    )


@router.delete("/{rule_id}", response_model=RuleResponse, summary="删除规则")
async def delete_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_architect)
):
    """
    删除规则

    - 仅Admin和Architect角色可访问
    - 检查规则是否有关联任务
    - 如果有关联任务，禁止删除
    - 删除规则及其所有版本

    Args:
        rule_id: 规则ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        RuleResponse: 删除结果

    Raises:
        HTTPException: 404 - 规则不存在
        HTTPException: 400 - 规则有关联任务，无法删除
    """
    # 查询规则
    rule_result = await db.execute(
        select(Rule).where(Rule.id == rule_id)
    )
    rule = rule_result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="规则不存在"
        )

    # 检查是否有关联任务
    task_count_query = select(func.count(Task.id)).where(Task.rule_id == rule_id)
    task_count_result = await db.execute(task_count_query)
    task_count = task_count_result.scalar() or 0

    if task_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"规则有 {task_count} 个关联任务，无法删除"
        )

    try:
        # 删除所有版本
        await db.execute(
            select(RuleVersion).where(RuleVersion.rule_id == rule_id)
        )
        versions_result = await db.execute(
            select(RuleVersion).where(RuleVersion.rule_id == rule_id)
        )
        versions = versions_result.scalars().all()
        
        for version in versions:
            await db.delete(version)

        # 删除规则
        await db.delete(rule)
        
        await db.commit()

        # TODO: 清除Redis缓存
        # await redis.delete(f"rule_config:{rule_id}")

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除规则失败: {str(e)}"
        )

    return RuleResponse(
        id=rule_id,
        message="规则删除成功"
    )


@router.post("/{rule_id}/sandbox", response_model=SandboxTestResponse, summary="沙箱测试")
async def sandbox_test(
    rule_id: str,
    file: UploadFile = File(...),
    version_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_architect)
):
    """
    沙箱测试规则

    - 仅Admin和Architect角色可访问
    - 接收上传的测试文件
    - 使用指定版本（默认草稿版本）执行完整处理流程
    - 返回提取结果、OCR标注、合并文本预览
    - 不影响生产数据（不创建任务记录）

    Args:
        rule_id: 规则ID
        file: 上传的测试文件
        version_id: 测试的版本ID（可选）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        SandboxTestResponse: 测试结果

    Raises:
        HTTPException: 404 - 规则或版本不存在
        HTTPException: 400 - 文件格式不支持
    """
    import time

    start_time = time.time()

    # 查询规则
    rule_result = await db.execute(
        select(Rule).where(Rule.id == rule_id)
    )
    rule = rule_result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="规则不存在"
        )

    # 确定要测试的版本
    if version_id:
        # 使用指定版本
        version_result = await db.execute(
            select(RuleVersion).where(
                and_(
                    RuleVersion.id == version_id,
                    RuleVersion.rule_id == rule_id
                )
            )
        )
        test_version = version_result.scalar_one_or_none()

        if not test_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定版本不存在"
            )
    else:
        # 使用草稿版本
        version_result = await db.execute(
            select(RuleVersion).where(
                and_(
                    RuleVersion.rule_id == rule_id,
                    RuleVersion.status == RuleStatus.DRAFT
                )
            )
        )
        test_version = version_result.scalar_one_or_none()

        if not test_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到草稿版本"
            )

    # 验证文件类型
    allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file.content_type}"
        )

    try:
        # 保存上传的文件到临时目录
        import tempfile
        import os
        from app.services.ocr_service import OCRService
        from app.services.extraction_service import ExtractionService
        from app.services.validation_service import ValidationService
        
        # 创建临时文件
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            file_content = await file.read()
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # 1. 执行OCR识别
            logger.info(f"开始OCR识别: {file.filename}")
            # 使用快速模式以提高沙箱测试速度
            ocr_config = {
                'umiocr_endpoint': settings.UMIOCR_ENDPOINT,
                'umiocr_timeout': settings.UMIOCR_TIMEOUT,
            }
            ocr_service = OCRService(config=ocr_config, fast_mode=True)
            
            # 获取规则配置
            config = test_version.config or {}
            
            # 从basic配置中读取OCR相关配置
            basic_config = config.get('basic', {})
            ocr_engine = basic_config.get('ocrEngine', 'paddleocr')
            language = basic_config.get('language', 'zh')
            page_strategy_mode = basic_config.get('pageStrategy', 'multi_page')
            
            # 构建页面策略配置
            page_strategy = {'mode': page_strategy_mode}
            if page_strategy_mode == 'specified_pages':
                page_strategy['page_range'] = basic_config.get('pageRange', '1')
            
            # 其他OCR配置 - 沙箱测试严格使用配置的引擎，不启用fallback
            enable_fallback = False  # 禁用fallback，严格使用用户配置的引擎
            fallback_engine = None
            
            logger.info(f"沙箱测试配置: engine={ocr_engine}, language={language}, page_strategy={page_strategy}, fallback=disabled")
            
            # 语言映射：前端使用 zh/en/zh_en，不同OCR引擎需要不同的语言代码
            if ocr_engine == 'tesseract':
                # Tesseract语言代码
                language_map = {
                    'zh': 'chi_sim',  # 简体中文
                    'en': 'eng',      # 英文
                    'zh_en': 'chi_sim+eng'  # 中英混排
                }
                ocr_language = language_map.get(language, 'eng')
            elif ocr_engine == 'umiocr':
                # UmiOCR语言代码（与PaddleOCR类似）
                language_map = {
                    'zh': 'ch',       # 中文
                    'en': 'en',       # 英文
                    'zh_en': 'ch'     # 中英混排
                }
                ocr_language = language_map.get(language, 'ch')
            else:
                # PaddleOCR语言代码
                language_map = {
                    'zh': 'ch',       # 中文
                    'en': 'en',       # 英文
                    'zh_en': 'ch'     # 中英混排
                }
                ocr_language = language_map.get(language, 'en')
            
            ocr_result = await ocr_service.process_document(
                file_path=temp_file_path,
                engine=ocr_engine,
                page_strategy=page_strategy,
                language=ocr_language,
                enable_fallback=enable_fallback,
                fallback_engine=fallback_engine
            )
            
            logger.info(f"OCR识别完成: {ocr_result.page_count}页, 引擎: {ocr_result.engine_used}")
            
            # 2. 应用提取规则
            extraction_service = ExtractionService()
            schema = config.get('schema', {})
            extraction_config = config.get('extraction', {})
            
            extracted_data = {}
            confidence_scores = {}
            
            # 将前端的extraction配置转换为extraction_rules数组
            extraction_rules = []
            if extraction_config and isinstance(extraction_config, dict):
                for field_name, rule_config in extraction_config.items():
                    if rule_config and isinstance(rule_config, dict):
                        rule = {'field': field_name, **rule_config}
                        extraction_rules.append(rule)
            
            if extraction_rules:
                logger.info(f"开始数据提取: {len(extraction_rules)}个规则")
                try:
                    extraction_results, llm_stats = await extraction_service.extract_fields(
                        ocr_result=ocr_result,
                        schema=schema,
                        extraction_rules=extraction_rules,
                        extraction_config=extraction_config
                    )
                    
                    # 转换提取结果，将扁平路径合并为嵌套结构
                    for field_name, result in extraction_results.items():
                        _set_nested_value(extracted_data, field_name, result.value)
                        confidence_scores[field_name] = result.confidence
                    
                    # 记录LLM消耗（沙盒测试时仅记录日志，不保存到数据库）
                    if llm_stats.get('token_count', 0) > 0:
                        logger.info(f"沙盒测试LLM消耗: Token={llm_stats['token_count']}, 费用=¥{llm_stats.get('cost', 0):.4f}")
                except Exception as e:
                    logger.error(f"数据提取失败: {str(e)}")
            else:
                logger.info("未配置提取规则，跳过数据提取")
            
            # 3. 应用清洗和验证规则
            validation_config = config.get('validation', {})
            validation_errors = []
            
            if validation_config:
                validation_service = ValidationService()
                
                # 3.1 先执行数据清洗
                cleaning_rules = []
                validation_rules_list = []
                
                for field_path, field_config in validation_config.items():
                    # 收集清洗规则
                    field_cleaning = field_config.get('cleaning', [])
                    if field_cleaning:
                        cleaning_rules.append({
                            'field': field_path,
                            'operations': field_cleaning
                        })
                    
                    # 收集验证规则
                    field_validation = field_config.get('validation', [])
                    for rule in field_validation:
                        validation_rules_list.append({
                            'field': field_path,
                            **rule
                        })
                
                # 执行清洗
                if cleaning_rules:
                    logger.info(f"开始数据清洗: {len(cleaning_rules)}个字段")
                    extracted_data = validation_service.clean_data(extracted_data, cleaning_rules)
                    logger.info(f"清洗后数据: {extracted_data}")
                
                # 3.2 执行验证
                if validation_rules_list:
                    logger.info(f"开始数据验证: {len(validation_rules_list)}个规则")
                    validation_result = validation_service.validate(extracted_data, validation_rules_list)
                    
                    if validation_result.has_errors:
                        validation_errors = [
                            {'field': error.field, 'error': error.message}
                            for error in validation_result.errors
                        ]
            
            # 兼容旧格式的验证规则
            old_validation_rules = config.get('validation_rules', [])
            script_rules = config.get('script_rules', [])
            
            if old_validation_rules or script_rules:
                if not validation_config:
                    validation_service = ValidationService()
                
                if old_validation_rules:
                    logger.info(f"开始旧格式数据验证: {len(old_validation_rules)}个规则")
                    validation_result = validation_service.validate(extracted_data, old_validation_rules)
                    
                    if validation_result.has_errors:
                        validation_errors.extend([
                            {'field': error.field, 'error': error.message}
                            for error in validation_result.errors
                        ])
                
                # 执行自定义脚本验证
                if script_rules:
                    script_result = validation_service.validate_custom_scripts(extracted_data, script_rules)
                    if script_result.errors:
                        validation_errors.extend([
                            {'field': error.field, 'error': error.message}
                            for error in script_result.errors
                        ])
            
            # 4. 应用增强风控（LLM补全低置信度字段）
            enhancement_config = config.get('enhancement', {})
            auto_enhancement = enhancement_config.get('autoEnhancement', {})
            
            if auto_enhancement.get('enabled') and auto_enhancement.get('llmCompletion'):
                llm_threshold = auto_enhancement.get('llmThreshold', 60)
                
                # 找出低于阈值的字段
                low_confidence_fields = []
                for field_name, confidence in confidence_scores.items():
                    if confidence < llm_threshold:
                        low_confidence_fields.append({
                            'field': field_name,
                            'confidence': confidence,
                            'current_value': _get_nested_value(extracted_data, field_name)
                        })
                
                if low_confidence_fields:
                    logger.info(f"发现 {len(low_confidence_fields)} 个低置信度字段（阈值: {llm_threshold}%），尝试LLM补全")
                    
                    try:
                        from app.services.llm_service import llm_service, AGENTLY_AVAILABLE
                        
                        if AGENTLY_AVAILABLE and llm_service.agent_config:
                            # 构建OCR结果字典
                            ocr_result_dict = {
                                'merged_text': ocr_result.merged_text,
                                'page_results': [
                                    {
                                        'text': page.text,
                                        'page_num': page.page_num,
                                        'confidence': page.confidence,
                                        'blocks': page.boxes
                                    }
                                    for page in ocr_result.page_results
                                ]
                            }
                            
                            # 为低置信度字段构建LLM提取配置
                            # 关键：复用原始的提取配置，保留用户定义的promptTemplate
                            llm_fields_schema = {}
                            llm_extraction_config = {}
                            
                            for item in low_confidence_fields:
                                field_name = item['field']
                                # 获取字段的schema定义
                                field_schema = _get_nested_schema(schema, field_name)
                                if field_schema:
                                    llm_fields_schema[field_name] = field_schema
                                    
                                    # 优先使用原始提取配置（包含用户定义的promptTemplate）
                                    original_config = extraction_config.get(field_name, {})
                                    if original_config and original_config.get('type') == 'llm':
                                        # 复用原始LLM配置
                                        llm_extraction_config[field_name] = original_config
                                        logger.info(f"LLM补全字段 {field_name}: 复用原始提取配置")
                                    else:
                                        # 非LLM提取的字段，生成默认LLM配置
                                        llm_extraction_config[field_name] = {
                                            'type': 'llm',
                                            'promptTemplate': f'请从文档中提取"{field_schema.get("label", field_name)}"的内容',
                                            'contextScope': 'all_pages'
                                        }
                                        logger.info(f"LLM补全字段 {field_name}: 使用默认提取配置")
                            
                            if llm_fields_schema:
                                # 调用LLM补全
                                llm_result = await llm_service.extract_by_schema(
                                    ocr_result_dict,
                                    llm_fields_schema,
                                    llm_extraction_config,
                                    'all_pages',
                                    3
                                )
                                
                                if llm_result and llm_result.get('data'):
                                    llm_data = llm_result['data']
                                    enhanced_count = 0
                                    
                                    for field_name, new_value in llm_data.items():
                                        if new_value is not None and new_value != '':
                                            old_value = _get_nested_value(extracted_data, field_name)
                                            _set_nested_value(extracted_data, field_name, new_value)
                                            # 更新置信度（LLM补全后提升到75%）
                                            confidence_scores[field_name] = 75.0
                                            enhanced_count += 1
                                            logger.info(f"LLM补全字段 {field_name}: {old_value} -> {new_value}")
                                    
                                    logger.info(f"LLM补全完成: {enhanced_count}/{len(low_confidence_fields)} 个字段")
                        else:
                            logger.warning("LLM服务不可用，跳过LLM补全")
                    except Exception as e:
                        logger.error(f"LLM补全失败: {str(e)}")
                        import traceback
                        traceback.print_exc()
            
            # 5. 一致性校验（LLM视觉提取对比）
            consistency_check = enhancement_config.get('consistencyCheck', {})
            consistency_results = None
            
            if consistency_check.get('enabled'):
                threshold = consistency_check.get('threshold', 80) / 100.0  # 转换为0-1
                strategy = consistency_check.get('strategy', 'manual_review')
                
                logger.info(f"开始一致性校验: 阈值={threshold*100}%, 策略={strategy}")
                
                try:
                    from app.services.llm_service import llm_service, AGENTLY_AVAILABLE
                    
                    if AGENTLY_AVAILABLE and llm_service.agent_config:
                        # 使用LLM视觉能力直接从文件提取
                        vision_result = await llm_service.extract_by_vision(
                            temp_file_path,
                            schema,
                            extraction_config
                        )
                        
                        if vision_result and vision_result.get('data'):
                            vision_data = vision_result['data']
                            
                            # 对比两组结果
                            consistency_results = llm_service.batch_compare_results(
                                extracted_data,
                                vision_data,
                                threshold
                            )
                            
                            # 统计不一致字段
                            inconsistent_fields = [
                                field for field, result in consistency_results.items()
                                if not result['is_consistent']
                            ]
                            
                            if inconsistent_fields:
                                logger.warning(f"一致性校验发现 {len(inconsistent_fields)} 个不一致字段: {inconsistent_fields}")
                                
                                # 根据策略处理
                                if strategy == 'prefer_llm':
                                    # 优先使用LLM视觉结果
                                    for field in inconsistent_fields:
                                        vision_value = vision_data.get(field)
                                        if vision_value is not None:
                                            _set_nested_value(extracted_data, field, vision_value)
                                            confidence_scores[field] = 85.0  # 视觉提取置信度
                                            logger.info(f"一致性校验: 字段 {field} 使用视觉提取结果")
                                elif strategy == 'prefer_ocr':
                                    # 优先使用OCR结果，不做修改
                                    logger.info("一致性校验: 保持OCR提取结果")
                                elif strategy == 'manual_review':
                                    # 标记需要人工审核（在返回结果中体现）
                                    logger.info("一致性校验: 标记需要人工审核")
                            else:
                                logger.info("一致性校验通过: 所有字段一致")
                        else:
                            logger.warning("视觉提取返回空结果，跳过一致性校验")
                    else:
                        logger.warning("LLM服务不可用，跳过一致性校验")
                except Exception as e:
                    logger.error(f"一致性校验失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            # 6. 构建OCR结果响应
            ocr_result_data = {
                'pages': [
                    {
                        'page_num': page.page_num,
                        'text': page.text,
                        'confidence': page.confidence,
                        'blocks': [
                            {
                                'text': box['text'],
                                'confidence': box.get('confidence', 0.0),
                                'box': box['box']
                            }
                            for box in page.boxes
                        ]
                    }
                    for page in ocr_result.page_results
                ],
                'engine_used': ocr_result.engine_used,
                'fallback_used': ocr_result.fallback_used
            }
            
            # 7. 计算处理时间
            processing_time = time.time() - start_time
            
            # 判断是否需要人工审核
            needs_review = False
            if consistency_results:
                inconsistent_fields = [
                    field for field, result in consistency_results.items()
                    if not result['is_consistent']
                ]
                if inconsistent_fields and consistency_check.get('strategy') == 'manual_review':
                    needs_review = True
            
            logger.info(f"沙箱测试完成: 耗时{processing_time:.2f}秒, 需要审核={needs_review}")
            
            return SandboxTestResponse(
                success=True,
                extracted_data=extracted_data,
                ocr_result=ocr_result_data,
                merged_text=ocr_result.merged_text,
                confidence_scores=confidence_scores,
                consistency_results=consistency_results,
                needs_review=needs_review,
                processing_time=processing_time,
                error=None if not validation_errors else f"验证失败: {validation_errors}"
            )
        
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {str(e)}")

    except Exception as e:
        processing_time = time.time() - start_time
        return SandboxTestResponse(
            success=False,
            extracted_data=None,
            ocr_result=None,
            merged_text=None,
            confidence_scores=None,
            processing_time=processing_time,
            error=str(e)
        )
