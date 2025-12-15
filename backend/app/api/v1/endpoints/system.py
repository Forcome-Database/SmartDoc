"""
系统配置端点
实现系统配置的查询和更新，仅Admin角色可访问
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime, timedelta
import json

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.core.cache import get_redis
from app.models.user import User
from app.models.system_config import SystemConfig
from app.models.audit_log import AuditLog
from app.schemas.system_config import (
    SystemConfigResponse,
    SystemConfigListResponse,
    SystemConfigUpdate,
    RetentionConfigResponse,
    RetentionConfigUpdate
)
from app.schemas.response import SuccessResponse

router = APIRouter(prefix="/system", tags=["系统配置"])


@router.get("/config", response_model=SystemConfigListResponse, summary="获取所有系统配置")
async def get_system_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    获取所有系统配置
    
    - 返回所有系统配置项
    - 仅Admin角色可访问
    
    Returns:
        SystemConfigListResponse: 配置列表
    """
    # 查询所有配置
    result = await db.execute(select(SystemConfig))
    configs = result.scalars().all()
    
    return SystemConfigListResponse(
        configs=[SystemConfigResponse.model_validate(config) for config in configs],
        total=len(configs)
    )


@router.put("/config/{key}", response_model=SuccessResponse, summary="更新系统配置")
async def update_system_config(
    key: str,
    config_update: SystemConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    更新指定的系统配置项
    
    - 更新配置值
    - 记录审计日志
    - 立即生效（更新Redis缓存）
    - 仅Admin角色可访问
    
    Args:
        key: 配置键
        config_update: 配置更新数据
        
    Returns:
        SuccessResponse: 成功响应
    """
    # 查询配置是否存在
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置项 {key} 不存在"
        )
    
    # 记录变更前的值
    old_value = config.value
    
    # 更新配置
    config.value = config_update.value
    if config_update.description is not None:
        config.description = config_update.description
    config.updated_by = current_user.id
    config.updated_at = datetime.utcnow()
    
    await db.commit()
    
    # 记录审计日志
    audit_log = AuditLog(
        user_id=current_user.id,
        action_type="update_system_config",
        resource_type="system_config",
        resource_id=key,
        changes={
            "old_value": old_value,
            "new_value": config.value,
            "description": config.description
        },
        ip_address=None,  # 可以从request中获取
        user_agent=None
    )
    db.add(audit_log)
    await db.commit()
    
    # 更新Redis缓存
    redis = await get_redis()
    if redis:
        try:
            cache_key = f"system:config:{key}"
            await redis.set(
                cache_key,
                json.dumps(config.value),
                ex=3600  # 缓存1小时
            )
        except Exception as e:
            # 缓存更新失败不影响主流程
            print(f"更新Redis缓存失败: {str(e)}")
    
    return SuccessResponse(
        message=f"配置项 {key} 更新成功",
        data={"key": key, "value": config.value}
    )


@router.get("/retention", response_model=RetentionConfigResponse, summary="获取数据生命周期配置")
async def get_retention_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    获取数据生命周期配置
    
    - 返回文件留存期和数据留存期配置
    - 返回下次清理时间
    - 仅Admin角色可访问
    
    Returns:
        RetentionConfigResponse: 生命周期配置
    """
    # 查询文件留存期配置
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "file_retention_days")
    )
    file_retention_config = result.scalar_one_or_none()
    file_retention_days = file_retention_config.value if file_retention_config else 30
    
    # 查询数据留存期配置
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "data_retention_days")
    )
    data_retention_config = result.scalar_one_or_none()
    data_retention_days = data_retention_config.value if data_retention_config else 0
    
    # 计算下次清理时间（每日凌晨02:00）
    now = datetime.utcnow()
    next_cleanup = datetime(now.year, now.month, now.day, 2, 0, 0)
    if now.hour >= 2:
        next_cleanup += timedelta(days=1)
    
    return RetentionConfigResponse(
        file_retention_days=file_retention_days,
        data_retention_days=data_retention_days,
        next_cleanup_time=next_cleanup.strftime("%Y-%m-%d %H:%M:%S")
    )


@router.put("/retention", response_model=SuccessResponse, summary="更新数据生命周期配置")
async def update_retention_config(
    retention_update: RetentionConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    更新数据生命周期配置
    
    - 更新文件留存期和数据留存期
    - 记录审计日志
    - 立即生效
    - 仅Admin角色可访问
    
    Args:
        retention_update: 生命周期配置更新数据
        
    Returns:
        SuccessResponse: 成功响应
    """
    # 更新文件留存期
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "file_retention_days")
    )
    file_config = result.scalar_one_or_none()
    
    if file_config:
        old_file_retention = file_config.value
        file_config.value = retention_update.file_retention_days
        file_config.updated_by = current_user.id
        file_config.updated_at = datetime.utcnow()
    else:
        # 如果不存在则创建
        old_file_retention = None
        file_config = SystemConfig(
            key="file_retention_days",
            value=retention_update.file_retention_days,
            description="文件留存期（天）",
            updated_by=current_user.id
        )
        db.add(file_config)
    
    # 更新数据留存期
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "data_retention_days")
    )
    data_config = result.scalar_one_or_none()
    
    if data_config:
        old_data_retention = data_config.value
        data_config.value = retention_update.data_retention_days
        data_config.updated_by = current_user.id
        data_config.updated_at = datetime.utcnow()
    else:
        # 如果不存在则创建
        old_data_retention = None
        data_config = SystemConfig(
            key="data_retention_days",
            value=retention_update.data_retention_days,
            description="数据留存期（天，0表示永久保留）",
            updated_by=current_user.id
        )
        db.add(data_config)
    
    await db.commit()
    
    # 记录审计日志
    audit_log = AuditLog(
        user_id=current_user.id,
        action_type="update_retention_config",
        resource_type="system_config",
        resource_id="retention",
        changes={
            "file_retention_days": {
                "old": old_file_retention,
                "new": retention_update.file_retention_days
            },
            "data_retention_days": {
                "old": old_data_retention,
                "new": retention_update.data_retention_days
            }
        },
        ip_address=None,
        user_agent=None
    )
    db.add(audit_log)
    await db.commit()
    
    # 更新Redis缓存
    redis = await get_redis()
    if redis:
        try:
            await redis.set(
                "system:config:file_retention_days",
                json.dumps(retention_update.file_retention_days),
                ex=3600
            )
            await redis.set(
                "system:config:data_retention_days",
                json.dumps(retention_update.data_retention_days),
                ex=3600
            )
        except Exception as e:
            print(f"更新Redis缓存失败: {str(e)}")
    
    return SuccessResponse(
        message="数据生命周期配置更新成功",
        data={
            "file_retention_days": retention_update.file_retention_days,
            "data_retention_days": retention_update.data_retention_days
        }
    )
