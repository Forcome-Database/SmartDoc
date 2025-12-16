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


@router.get("/dingtalk", response_model=SuccessResponse, summary="获取钉钉配置")
async def get_dingtalk_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    获取钉钉群机器人配置（单条JSON配置方案）
    
    Returns:
        SuccessResponse: 钉钉配置
    """
    from app.services.dingtalk_service import DEFAULT_CONFIG
    
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "dingtalk_config")
    )
    config_record = result.scalar_one_or_none()
    
    if config_record and config_record.value:
        config = {**DEFAULT_CONFIG, **config_record.value}
        # 不返回密钥明文，只返回是否已配置
        config["has_secret"] = bool(config.get("secret"))
        config["secret"] = ""
        config["updated_at"] = config_record.updated_at.isoformat() if config_record.updated_at else None
    else:
        config = {**DEFAULT_CONFIG, "has_secret": False, "updated_at": None}
    
    return SuccessResponse(message="获取钉钉配置成功", data=config)


@router.put("/dingtalk", response_model=SuccessResponse, summary="更新钉钉配置")
async def update_dingtalk_config(
    config_update: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    更新钉钉群机器人配置（单条JSON配置方案）
    
    支持的配置项:
    - enabled: 总开关
    - webhook_url: Webhook地址
    - secret: 加签密钥
    - at_all: 是否@所有人
    - at_mobiles: @指定人员手机号列表
    - notify_events: 通知事件配置
    - notify_rules: 启用通知的规则ID列表
    
    Args:
        config_update: 配置更新数据
        
    Returns:
        SuccessResponse: 成功响应
    """
    from app.services.dingtalk_service import DEFAULT_CONFIG, dingtalk_service
    
    # 获取现有配置
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "dingtalk_config")
    )
    config_record = result.scalar_one_or_none()
    
    # 合并配置
    if config_record and config_record.value:
        current_config = {**DEFAULT_CONFIG, **config_record.value}
    else:
        current_config = DEFAULT_CONFIG.copy()
    
    old_config = current_config.copy()
    
    # 更新配置项
    if 'enabled' in config_update:
        current_config['enabled'] = config_update['enabled']
    if 'webhook_url' in config_update:
        current_config['webhook_url'] = config_update['webhook_url']
    if 'secret' in config_update and config_update['secret']:
        # 只有传入非空密钥才更新
        current_config['secret'] = config_update['secret']
    if 'at_all' in config_update:
        current_config['at_all'] = config_update['at_all']
    if 'at_mobiles' in config_update:
        current_config['at_mobiles'] = config_update['at_mobiles']
    if 'notify_events' in config_update:
        current_config['notify_events'] = {
            **current_config.get('notify_events', {}),
            **config_update['notify_events']
        }
    if 'notify_rules' in config_update:
        current_config['notify_rules'] = config_update['notify_rules']
    
    # 保存配置
    if config_record:
        config_record.value = current_config
        config_record.updated_by = current_user.id
        config_record.updated_at = datetime.utcnow()
    else:
        config_record = SystemConfig(
            key="dingtalk_config",
            value=current_config,
            description="钉钉群机器人通知配置",
            updated_by=current_user.id
        )
        db.add(config_record)
    
    await db.commit()
    
    # 清除服务缓存
    dingtalk_service.clear_cache()
    
    # 记录审计日志
    audit_log = AuditLog(
        user_id=current_user.id,
        action_type="update_dingtalk_config",
        resource_type="system_config",
        resource_id="dingtalk_config",
        changes={
            "enabled": {"old": old_config.get('enabled'), "new": current_config.get('enabled')},
            "webhook_url_changed": old_config.get('webhook_url') != current_config.get('webhook_url'),
            "secret_updated": 'secret' in config_update and bool(config_update['secret']),
            "notify_events": current_config.get('notify_events'),
            "notify_rules": current_config.get('notify_rules')
        },
        ip_address=None,
        user_agent=None
    )
    db.add(audit_log)
    await db.commit()
    
    # 返回配置（隐藏密钥）
    response_config = current_config.copy()
    response_config['has_secret'] = bool(response_config.get('secret'))
    response_config['secret'] = ''
    
    return SuccessResponse(
        message="钉钉配置更新成功",
        data=response_config
    )


@router.post("/dingtalk/test", response_model=SuccessResponse, summary="测试钉钉Webhook")
async def test_dingtalk_webhook(
    test_request: dict,
    current_user: User = Depends(require_admin)
):
    """
    测试钉钉群机器人Webhook
    
    - 发送测试消息到指定的Webhook URL
    - 支持加签验证
    - 支持@指定人员
    - 仅Admin角色可访问
    
    Args:
        test_request: 测试请求 {webhook_url, secret, at_all, at_mobiles}
        
    Returns:
        SuccessResponse: 测试结果
    """
    import httpx
    from app.services.dingtalk_service import DingTalkService
    
    webhook_url = test_request.get('webhook_url', '')
    secret = test_request.get('secret', '')
    at_all = test_request.get('at_all', True)
    at_mobiles = test_request.get('at_mobiles', [])
    
    if not webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook URL不能为空"
        )
    
    if not webhook_url.startswith('https://oapi.dingtalk.com/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的钉钉Webhook URL"
        )
    
    try:
        # 如果有加签密钥，生成带签名的URL
        final_url = webhook_url
        if secret:
            final_url = DingTalkService.generate_sign_for_test(secret, webhook_url)
        
        # 构建测试消息
        test_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        at_info = ""
        if at_mobiles:
            at_info = f"\n@人员: {', '.join(at_mobiles)}"
        elif at_all:
            at_info = "\n@所有人"
        
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": "🔔 钉钉通知测试",
                "text": f"### 🔔 智能文档处理中台 - 钉钉通知测试\n\n**测试时间**: {test_time}\n\n**测试人**: {current_user.username}{at_info}\n\n---\n如果您收到此消息，说明钉钉通知配置正确！"
            },
            "at": {
                "isAtAll": at_all and not at_mobiles,
                "atMobiles": at_mobiles
            }
        }
        
        # 发送测试请求
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                final_url,
                json=message,
                headers={"Content-Type": "application/json"}
            )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("errcode") == 0:
                return SuccessResponse(
                    message="测试消息发送成功",
                    data={"success": True}
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"钉钉返回错误: {result.get('errmsg', '未知错误')}"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"请求失败: HTTP {response.status_code}"
            )
            
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="请求超时，请检查网络连接"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试失败: {str(e)}"
        )


@router.get("/rules/simple", response_model=SuccessResponse, summary="获取规则简单列表")
async def get_rules_simple_list(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    获取规则简单列表（用于钉钉通知规则选择）
    
    Returns:
        SuccessResponse: 规则列表 [{id, name}]
    """
    from app.models.rule import Rule
    
    # 查询已发布的规则（current_version不为空表示已发布）
    result = await db.execute(
        select(Rule.id, Rule.name).where(Rule.current_version.isnot(None))
    )
    rules = result.all()
    
    return SuccessResponse(
        message="获取规则列表成功",
        data=[{"id": str(r.id), "name": r.name} for r in rules]
    )
