# -*- coding: utf-8 -*-
"""
Webhook配置端点
实现Webhook的CRUD、连通性测试和规则关联功能
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete
from typing import Optional
from datetime import datetime
import uuid
import json
import httpx
import time
import sys
from loguru import logger

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_admin
from app.core.security import encrypt_sensitive_data, decrypt_sensitive_data, generate_webhook_signature
from app.models.user import User, RoleEnum
from app.models.webhook import Webhook, AuthType, WebhookType, rule_webhooks
from app.models.rule import Rule
from app.models.push_log import PushLog
from app.schemas.webhook import (
    WebhookCreate, WebhookUpdate, WebhookListItem, WebhookDetail,
    WebhookListResponse, WebhookResponse, WebhookTestRequest,
    WebhookTestResponse, RuleWebhookAssociation, WebhookType as SchemaWebhookType
)

router = APIRouter(prefix="/webhooks", tags=["Webhook配置"])


def mask_secret_key(secret_key: Optional[str]) -> Optional[str]:
    """
    遮蔽Secret Key，仅显示前8位
    
    Args:
        secret_key: 完整的Secret Key
        
    Returns:
        遮蔽后的Secret Key
    """
    if not secret_key:
        return None
    
    if len(secret_key) <= 8:
        return secret_key
    
    return secret_key[:8] + "***"


def mask_auth_config(auth_config: Optional[dict], auth_type: AuthType) -> Optional[dict]:
    """
    脱敏认证配置中的敏感信息
    
    Args:
        auth_config: 认证配置
        auth_type: 认证类型
        
    Returns:
        脱敏后的认证配置
    """
    if not auth_config:
        return None
    
    masked_config = auth_config.copy()
    
    if auth_type == AuthType.BASIC:
        if 'password' in masked_config:
            masked_config['password'] = "***"
    elif auth_type == AuthType.BEARER:
        if 'token' in masked_config:
            token = masked_config['token']
            masked_config['token'] = token[:8] + "***" if len(token) > 8 else "***"
    elif auth_type == AuthType.API_KEY:
        if 'value' in masked_config:
            value = masked_config['value']
            masked_config['value'] = value[:8] + "***" if len(value) > 8 else "***"
    
    return masked_config


# ============================================================================
# 19.1 Webhook列表端点
# ============================================================================

@router.get("", response_model=WebhookListResponse, summary="获取Webhook列表")
async def get_webhooks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    获取所有Webhook配置
    
    - 仅Admin角色可访问
    - 返回Webhook基本信息和关联规则数量
    - 敏感信息已脱敏
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        WebhookListResponse: Webhook列表响应
    """
    # 查询所有Webhook
    query = select(Webhook).order_by(Webhook.created_at.desc())
    result = await db.execute(query)
    webhooks = result.scalars().all()
    
    # 构建响应数据
    items = []
    for webhook in webhooks:
        # 查询关联规则数量
        rule_count_query = select(func.count()).select_from(rule_webhooks).where(
            rule_webhooks.c.webhook_id == webhook.id
        )
        rule_count_result = await db.execute(rule_count_query)
        rule_count = rule_count_result.scalar() or 0
        
        items.append(WebhookListItem(
            id=webhook.id,
            name=webhook.name,
            webhook_type=webhook.webhook_type or WebhookType.STANDARD,
            endpoint_url=webhook.endpoint_url or "",
            auth_type=webhook.auth_type or AuthType.NONE,
            is_active=webhook.is_active,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at,
            rule_count=rule_count
        ))
    
    return WebhookListResponse(
        items=items,
        total=len(items)
    )


# ============================================================================
# 19.2 Webhook创建端点
# ============================================================================

@router.post("", response_model=WebhookResponse, summary="创建Webhook")
async def create_webhook(
    webhook_data: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    创建Webhook配置
    
    - 仅Admin角色可访问
    - 自动生成Webhook ID
    - 加密存储secret_key和敏感认证信息
    
    Args:
        webhook_data: Webhook创建数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        WebhookResponse: 创建结果
    """
    
    # 生成Webhook ID
    webhook_id = f"WH_{uuid.uuid4().hex[:12].upper()}"
    
    # 加密secret_key
    encrypted_secret_key = None
    if webhook_data.secret_key:
        encrypted_secret_key = encrypt_sensitive_data(webhook_data.secret_key)
    
    # 加密认证配置中的敏感信息
    encrypted_auth_config = None
    if webhook_data.auth_config:
        auth_config = webhook_data.auth_config.copy()
        
        # 根据认证类型加密敏感字段
        if webhook_data.auth_type == AuthType.BASIC and 'password' in auth_config:
            auth_config['password'] = encrypt_sensitive_data(auth_config['password'])
        elif webhook_data.auth_type == AuthType.BEARER and 'token' in auth_config:
            auth_config['token'] = encrypt_sensitive_data(auth_config['token'])
        elif webhook_data.auth_type == AuthType.API_KEY and 'value' in auth_config:
            auth_config['value'] = encrypt_sensitive_data(auth_config['value'])
        
        encrypted_auth_config = auth_config
    
    # 处理金蝶配置（如果是金蝶类型）
    kingdee_config = None
    if webhook_data.webhook_type == SchemaWebhookType.KINGDEE and webhook_data.kingdee_config:
        # 金蝶配置不需要加密，因为使用环境变量中的凭据
        kingdee_config = webhook_data.kingdee_config.model_dump() if hasattr(webhook_data.kingdee_config, 'model_dump') else dict(webhook_data.kingdee_config)
    
    # 创建Webhook记录
    new_webhook = Webhook(
        id=webhook_id,
        name=webhook_data.name,
        webhook_type=webhook_data.webhook_type,
        endpoint_url=webhook_data.endpoint_url or "",
        auth_type=webhook_data.auth_type,
        auth_config=encrypted_auth_config,
        secret_key=encrypted_secret_key,
        request_template=webhook_data.request_template or {},
        kingdee_config=kingdee_config,
        is_active=webhook_data.is_active
    )
    
    db.add(new_webhook)
    
    try:
        # 先 flush 以获取 webhook_id，但不提交事务
        await db.flush()
        
        # 处理规则关联
        rule_count = 0
        logger.info(f"创建Webhook: webhook_id={new_webhook.id}, rule_ids={webhook_data.rule_ids}")
        if webhook_data.rule_ids:
            for rule_id in webhook_data.rule_ids:
                rule_result = await db.execute(select(Rule).where(Rule.id == rule_id))
                rule = rule_result.scalar_one_or_none()
                if rule:
                    insert_stmt = rule_webhooks.insert().values(
                        rule_id=rule_id,
                        webhook_id=new_webhook.id,
                        created_at=datetime.utcnow()
                    )
                    await db.execute(insert_stmt)
                    rule_count += 1
                    logger.debug(f"已关联规则: rule_id={rule_id}")
                else:
                    logger.warning(f"规则不存在，跳过关联: rule_id={rule_id}")
            
            logger.info(f"规则关联完成: 成功关联 {rule_count} 个规则")
        
        # 一次性提交所有更改
        await db.commit()
        await db.refresh(new_webhook)
            
    except Exception as e:
        await db.rollback()
        logger.error(f"创建Webhook失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建Webhook失败: {str(e)}"
        )
    
    return WebhookResponse(
        id=new_webhook.id,
        message=f"Webhook创建成功: {webhook_data.name}"
    )


# ============================================================================
# 19.3 Webhook更新端点
# ============================================================================

@router.put("/{webhook_id}", response_model=WebhookResponse, summary="更新Webhook")
async def update_webhook(
    webhook_id: str,
    webhook_data: WebhookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    更新Webhook配置
    
    - 仅Admin角色可访问
    - 重新加密secret_key（如果修改）
    - 重新加密认证配置中的敏感信息（如果修改）
    
    Args:
        webhook_id: Webhook ID
        webhook_data: Webhook更新数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        WebhookResponse: 更新结果
        
    Raises:
        HTTPException: 404 - Webhook不存在
    """
    # 查询Webhook
    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id)
    )
    webhook = result.scalar_one_or_none()
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook不存在"
        )
    
    # 更新字段
    if webhook_data.name is not None:
        webhook.name = webhook_data.name
    
    if webhook_data.endpoint_url is not None:
        webhook.endpoint_url = webhook_data.endpoint_url
    
    if webhook_data.auth_type is not None:
        webhook.auth_type = webhook_data.auth_type
    
    if webhook_data.auth_config is not None:
        # 加密认证配置中的敏感信息
        auth_config = webhook_data.auth_config.copy()
        auth_type = webhook_data.auth_type or webhook.auth_type
        
        if auth_type == AuthType.BASIC and 'password' in auth_config:
            auth_config['password'] = encrypt_sensitive_data(auth_config['password'])
        elif auth_type == AuthType.BEARER and 'token' in auth_config:
            auth_config['token'] = encrypt_sensitive_data(auth_config['token'])
        elif auth_type == AuthType.API_KEY and 'value' in auth_config:
            auth_config['value'] = encrypt_sensitive_data(auth_config['value'])
        
        webhook.auth_config = auth_config
    
    if webhook_data.secret_key is not None:
        # 重新加密secret_key
        webhook.secret_key = encrypt_sensitive_data(webhook_data.secret_key)
    
    if webhook_data.request_template is not None:
        webhook.request_template = webhook_data.request_template
    
    if webhook_data.is_active is not None:
        webhook.is_active = webhook_data.is_active
    
    webhook.updated_at = datetime.utcnow()
    
    try:
        # 处理规则关联更新
        if webhook_data.rule_ids is not None:
            logger.info(f"更新Webhook规则关联: webhook_id={webhook_id}, rule_ids={webhook_data.rule_ids}")
            
            # 删除现有关联
            delete_stmt = delete(rule_webhooks).where(
                rule_webhooks.c.webhook_id == webhook_id
            )
            await db.execute(delete_stmt)
            
            # 添加新关联
            rule_count = 0
            for rule_id in webhook_data.rule_ids:
                rule_result = await db.execute(select(Rule).where(Rule.id == rule_id))
                if rule_result.scalar_one_or_none():
                    insert_stmt = rule_webhooks.insert().values(
                        rule_id=rule_id,
                        webhook_id=webhook_id,
                        created_at=datetime.utcnow()
                    )
                    await db.execute(insert_stmt)
                    rule_count += 1
            
            logger.info(f"规则关联更新完成: 成功关联 {rule_count} 个规则")
        
        # 一次性提交所有更改
        await db.commit()
            
    except Exception as e:
        await db.rollback()
        logger.error(f"更新Webhook失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新Webhook失败: {str(e)}"
        )
    
    return WebhookResponse(
        id=webhook_id,
        message="Webhook更新成功"
    )


# ============================================================================
# 19.4 Webhook删除端点
# ============================================================================

@router.delete("/{webhook_id}", response_model=WebhookResponse, summary="删除Webhook")
async def delete_webhook(
    webhook_id: str,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    删除Webhook配置
    
    - 仅Admin角色可访问
    - 检查是否有规则关联，如有则提示警告
    - 使用 force=true 可强制删除（同时解除所有规则关联）
    
    Args:
        webhook_id: Webhook ID
        force: 是否强制删除（解除所有规则关联后删除）
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        WebhookResponse: 删除结果
        
    Raises:
        HTTPException: 404 - Webhook不存在
        HTTPException: 400 - 有规则关联，无法删除（非强制模式）
    """
    # 查询Webhook
    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id)
    )
    webhook = result.scalar_one_or_none()
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook不存在"
        )
    
    # 检查是否有规则关联
    rule_count_query = select(func.count()).select_from(rule_webhooks).where(
        rule_webhooks.c.webhook_id == webhook_id
    )
    rule_count_result = await db.execute(rule_count_query)
    rule_count = rule_count_result.scalar() or 0
    
    if rule_count > 0:
        if not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"该Webhook关联了{rule_count}个规则，请先解除关联后再删除，或使用强制删除"
            )
        
        # 强制删除：先解除所有规则关联
        delete_associations = delete(rule_webhooks).where(
            rule_webhooks.c.webhook_id == webhook_id
        )
        await db.execute(delete_associations)
        logger.info(f"强制删除Webhook: 已解除{rule_count}个规则关联, webhook_id={webhook_id}")
    
    # 删除关联的推送日志
    from app.models.push_log import PushLog
    delete_logs = delete(PushLog).where(PushLog.webhook_id == webhook_id)
    await db.execute(delete_logs)
    logger.info(f"已删除Webhook关联的推送日志: webhook_id={webhook_id}")
    
    # 删除Webhook
    await db.delete(webhook)
    
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除Webhook失败: {str(e)}"
        )
    
    message = "Webhook删除成功"
    if rule_count > 0 and force:
        message = f"Webhook删除成功（已自动解除{rule_count}个规则关联）"
    
    return WebhookResponse(
        id=webhook_id,
        message=message
    )


# ============================================================================
# Webhook详情端点（额外功能）
# ============================================================================

@router.get("/{webhook_id}", response_model=WebhookDetail, summary="获取Webhook详情")
async def get_webhook_detail(
    webhook_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    获取Webhook详情
    
    - 仅Admin角色可访问
    - 返回完整配置信息（敏感信息已脱敏）
    - 返回关联规则数和推送次数
    
    Args:
        webhook_id: Webhook ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        WebhookDetail: Webhook详情
        
    Raises:
        HTTPException: 404 - Webhook不存在
    """
    # 查询Webhook
    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id)
    )
    webhook = result.scalar_one_or_none()
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook不存在"
        )
    
    # 查询关联规则数量
    rule_count_query = select(func.count()).select_from(rule_webhooks).where(
        rule_webhooks.c.webhook_id == webhook_id
    )
    rule_count_result = await db.execute(rule_count_query)
    rule_count = rule_count_result.scalar() or 0
    
    # 查询推送次数
    push_count_query = select(func.count(PushLog.id)).where(
        PushLog.webhook_id == webhook_id
    )
    push_count_result = await db.execute(push_count_query)
    push_count = push_count_result.scalar() or 0
    
    # 查询关联的规则ID列表
    rule_ids_query = select(rule_webhooks.c.rule_id).where(
        rule_webhooks.c.webhook_id == webhook_id
    )
    rule_ids_result = await db.execute(rule_ids_query)
    rule_ids = [row[0] for row in rule_ids_result.fetchall()]
    
    logger.info(f"获取Webhook详情: webhook_id={webhook_id}, rule_ids={rule_ids}, rule_count={rule_count}")
    
    # 脱敏处理
    secret_key_masked = None
    if webhook.secret_key:
        decrypted_secret = decrypt_sensitive_data(webhook.secret_key)
        secret_key_masked = mask_secret_key(decrypted_secret)
    
    auth_config_masked = mask_auth_config(webhook.auth_config, webhook.auth_type)
    
    # 金蝶配置脱敏（金蝶使用环境变量，这里只显示form_id等非敏感信息）
    kingdee_config_masked = None
    if webhook.kingdee_config:
        kingdee_config_masked = {
            "form_id": webhook.kingdee_config.get("form_id", ""),
            "save_mode": webhook.kingdee_config.get("save_mode", "smart"),
            "note": "金蝶连接使用环境变量配置"
        }
    
    return WebhookDetail(
        id=webhook.id,
        name=webhook.name,
        webhook_type=webhook.webhook_type or WebhookType.STANDARD,
        endpoint_url=webhook.endpoint_url or "",
        auth_type=webhook.auth_type or AuthType.NONE,
        auth_config=auth_config_masked,
        secret_key_masked=secret_key_masked,
        request_template=webhook.request_template,
        kingdee_config=kingdee_config_masked,
        is_active=webhook.is_active,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
        rule_count=rule_count,
        push_count=push_count,
        rule_ids=rule_ids
    )



# ============================================================================
# 19.5 连通性测试端点
# ============================================================================

@router.post("/{webhook_id}/test", response_model=WebhookTestResponse, summary="测试Webhook连通性")
async def test_webhook(
    webhook_id: str,
    test_data: WebhookTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    测试Webhook连通性
    
    - 仅Admin角色可访问
    - 使用Mock数据发送测试请求
    - 返回响应状态码、响应头、响应体
    - 5秒超时
    
    Args:
        webhook_id: Webhook ID
        test_data: 测试请求数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        WebhookTestResponse: 测试结果
        
    Raises:
        HTTPException: 404 - Webhook不存在
    """
    start_time = time.time()
    
    # 查询Webhook
    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id)
    )
    webhook = result.scalar_one_or_none()
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook不存在"
        )
    
    # 准备Mock数据
    mock_data = test_data.mock_data or {
        "task_id": "T_TEST_001",
        "result": {"test_field": "test_value"},
        "file_url": "https://example.com/test.pdf",
        "meta_info": {
            "rule_name": "测试规则",
            "processing_time": 3.5,
            "page_count": 1
        }
    }
    
    # 渲染请求体模版
    request_body = webhook.request_template.copy()
    
    def replace_variables(obj, data):
        """递归替换模版变量"""
        if isinstance(obj, dict):
            return {k: replace_variables(v, data) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_variables(item, data) for item in obj]
        elif isinstance(obj, str):
            # 替换变量
            result = obj
            result = result.replace("{{task_id}}", str(data.get("task_id", "")))
            result = result.replace("{{result_json}}", json.dumps(data.get("result", {}), ensure_ascii=False))
            result = result.replace("{{file_url}}", str(data.get("file_url", "")))
            result = result.replace("{{meta_info}}", json.dumps(data.get("meta_info", {}), ensure_ascii=False))
            return result
        else:
            return obj
    
    rendered_body = replace_variables(request_body, mock_data)
    request_body_str = json.dumps(rendered_body, ensure_ascii=False)
    
    # 准备请求头
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "IDP-Platform-Test/1.0"
    }
    
    # 添加认证信息
    if webhook.auth_type == AuthType.BASIC and webhook.auth_config:
        username = webhook.auth_config.get('username', '')
        password_encrypted = webhook.auth_config.get('password', '')
        password = decrypt_sensitive_data(password_encrypted) if password_encrypted else ''
        
        import base64
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers["Authorization"] = f"Basic {encoded_credentials}"
    
    elif webhook.auth_type == AuthType.BEARER and webhook.auth_config:
        token_encrypted = webhook.auth_config.get('token', '')
        token = decrypt_sensitive_data(token_encrypted) if token_encrypted else ''
        headers["Authorization"] = f"Bearer {token}"
    
    elif webhook.auth_type == AuthType.API_KEY and webhook.auth_config:
        key = webhook.auth_config.get('key', '')
        value_encrypted = webhook.auth_config.get('value', '')
        value = decrypt_sensitive_data(value_encrypted) if value_encrypted else ''
        headers[key] = value
    
    # 添加HMAC签名
    if webhook.secret_key:
        decrypted_secret = decrypt_sensitive_data(webhook.secret_key)
        signature = generate_webhook_signature(request_body_str, decrypted_secret)
        headers["X-IDP-Signature"] = signature
    
    # 发送测试请求
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                webhook.endpoint_url,
                content=request_body_str,
                headers=headers
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return WebhookTestResponse(
                success=True,
                status_code=response.status_code,
                response_headers=dict(response.headers),
                response_body=response.text[:1000],  # 限制响应体长度
                error=None,
                duration_ms=duration_ms
            )
    
    except httpx.TimeoutException:
        duration_ms = int((time.time() - start_time) * 1000)
        return WebhookTestResponse(
            success=False,
            status_code=None,
            response_headers=None,
            response_body=None,
            error="请求超时（5秒）",
            duration_ms=duration_ms
        )
    
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return WebhookTestResponse(
            success=False,
            status_code=None,
            response_headers=None,
            response_body=None,
            error=str(e),
            duration_ms=duration_ms
        )


# ============================================================================
# 19.6 规则关联Webhook端点
# ============================================================================

@router.post("/rules/{rule_id}/webhooks", response_model=WebhookResponse, summary="关联规则和Webhook")
async def associate_rule_webhooks(
    rule_id: str,
    association_data: RuleWebhookAssociation,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    关联规则和Webhook（多对多）
    
    - 仅Admin角色可访问
    - 批量关联多个Webhook到规则
    - 自动去重，避免重复关联
    
    Args:
        rule_id: 规则ID
        association_data: 关联数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        WebhookResponse: 关联结果
        
    Raises:
        HTTPException: 404 - 规则不存在
        HTTPException: 404 - Webhook不存在
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
    
    # 检查所有Webhook是否存在
    for webhook_id in association_data.webhook_ids:
        webhook_result = await db.execute(
            select(Webhook).where(Webhook.id == webhook_id)
        )
        webhook = webhook_result.scalar_one_or_none()
        
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Webhook不存在: {webhook_id}"
            )
    
    # 查询已存在的关联
    existing_query = select(rule_webhooks.c.webhook_id).where(
        rule_webhooks.c.rule_id == rule_id
    )
    existing_result = await db.execute(existing_query)
    existing_webhook_ids = set(row[0] for row in existing_result.fetchall())
    
    # 添加新关联
    new_associations = 0
    for webhook_id in association_data.webhook_ids:
        if webhook_id not in existing_webhook_ids:
            insert_stmt = rule_webhooks.insert().values(
                rule_id=rule_id,
                webhook_id=webhook_id,
                created_at=datetime.utcnow()
            )
            await db.execute(insert_stmt)
            new_associations += 1
    
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"关联Webhook失败: {str(e)}"
        )
    
    return WebhookResponse(
        id=rule_id,
        message=f"成功关联{new_associations}个Webhook（跳过{len(association_data.webhook_ids) - new_associations}个已存在的关联）"
    )


@router.delete("/rules/{rule_id}/webhooks/{webhook_id}", response_model=WebhookResponse, summary="解除规则和Webhook关联")
async def disassociate_rule_webhook(
    rule_id: str,
    webhook_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    解除规则和Webhook的关联
    
    - 仅Admin角色可访问
    - 删除规则和Webhook的关联关系
    
    Args:
        rule_id: 规则ID
        webhook_id: Webhook ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        WebhookResponse: 解除关联结果
        
    Raises:
        HTTPException: 404 - 关联不存在
    """
    # 检查关联是否存在
    check_query = select(rule_webhooks).where(
        and_(
            rule_webhooks.c.rule_id == rule_id,
            rule_webhooks.c.webhook_id == webhook_id
        )
    )
    check_result = await db.execute(check_query)
    association = check_result.fetchone()
    
    if not association:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="关联不存在"
        )
    
    # 删除关联
    delete_stmt = delete(rule_webhooks).where(
        and_(
            rule_webhooks.c.rule_id == rule_id,
            rule_webhooks.c.webhook_id == webhook_id
        )
    )
    await db.execute(delete_stmt)
    
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解除关联失败: {str(e)}"
        )
    
    return WebhookResponse(
        id=rule_id,
        message="成功解除Webhook关联"
    )


@router.get("/rules/{rule_id}/webhooks", response_model=WebhookListResponse, summary="获取规则关联的Webhook列表")
async def get_rule_webhooks(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取规则关联的所有Webhook
    
    - 返回规则关联的Webhook列表
    
    Args:
        rule_id: 规则ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        WebhookListResponse: Webhook列表响应
        
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
    
    # 查询关联的Webhook
    query = select(Webhook).join(
        rule_webhooks,
        Webhook.id == rule_webhooks.c.webhook_id
    ).where(
        rule_webhooks.c.rule_id == rule_id
    ).order_by(Webhook.created_at.desc())
    
    result = await db.execute(query)
    webhooks = result.scalars().all()
    
    # 构建响应数据
    items = []
    for webhook in webhooks:
        # 查询关联规则数量
        rule_count_query = select(func.count()).select_from(rule_webhooks).where(
            rule_webhooks.c.webhook_id == webhook.id
        )
        rule_count_result = await db.execute(rule_count_query)
        rule_count = rule_count_result.scalar() or 0
        
        items.append(WebhookListItem(
            id=webhook.id,
            name=webhook.name,
            endpoint_url=webhook.endpoint_url,
            auth_type=webhook.auth_type,
            is_active=webhook.is_active,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at,
            rule_count=rule_count
        ))
    
    return WebhookListResponse(
        items=items,
        total=len(items)
    )
