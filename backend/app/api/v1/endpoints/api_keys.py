"""
API Key管理端点
提供API Key的生成、查询和撤销功能
"""
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    generate_api_key,
    hash_api_key_secret,
    mask_api_key_secret
)
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.api_key import APIKey
from app.schemas.api_key import (
    APIKeyResponse,
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    APIKeyListResponse,
    APIKeyRevokeResponse
)
import secrets


router = APIRouter(prefix="/api-keys", tags=["API Key管理"], redirect_slashes=False)


# ============================================================================
# 23.1 API Key列表端点
# ============================================================================

@router.get(
    "/",
    response_model=APIKeyListResponse,
    summary="获取当前用户的API Key列表",
    description="返回当前用户的所有API Key，Secret仅显示前8位+***"
)
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的API Key列表
    
    - 仅返回当前用户创建的API Key
    - Secret字段遮蔽显示（前8位+***）
    - 按创建时间倒序排列
    """
    # 查询当前用户的所有API Key
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == current_user.id)
        .order_by(APIKey.created_at.desc())
    )
    api_keys = result.scalars().all()
    
    # 构建响应数据
    items = []
    for api_key in api_keys:
        # 遮蔽secret（从key_id中提取前8位，因为secret_hash已经是哈希值）
        masked_secret = mask_api_key_secret(api_key.key_id, visible_chars=8)
        
        items.append(APIKeyResponse(
            id=api_key.id,
            key_id=api_key.key_id,
            masked_secret=masked_secret,
            expires_at=api_key.expires_at,
            is_active=api_key.is_active,
            last_used_at=api_key.last_used_at,
            created_at=api_key.created_at
        ))
    
    return APIKeyListResponse(
        items=items,
        total=len(items)
    )


# ============================================================================
# 23.2 API Key生成端点
# ============================================================================

@router.post(
    "/",
    response_model=APIKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="生成新的API Key",
    description="为当前用户生成新的API Key，完整Secret仅此一次显示"
)
async def create_api_key(
    request: APIKeyCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    生成新的API Key
    
    - 生成唯一的key_id和secret
    - secret使用bcrypt哈希存储
    - 支持配置有效期（天数）
    - 完整secret仅在创建时返回一次
    
    Args:
        request: 创建请求，包含有效期配置
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        包含完整secret的API Key信息
    """
    # 生成API Key
    key_id, secret = generate_api_key()
    
    # 哈希存储secret
    secret_hash = hash_api_key_secret(secret)
    
    # 计算过期时间
    expires_at = None
    if request.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=request.expires_days)
    
    # 生成唯一ID
    api_key_id = f"ak_{secrets.token_urlsafe(16)}"
    
    # 创建API Key记录
    api_key = APIKey(
        id=api_key_id,
        user_id=current_user.id,
        key_id=key_id,
        secret_hash=secret_hash,
        expires_at=expires_at,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    # 返回响应（包含完整secret，仅此一次）
    return APIKeyCreateResponse(
        id=api_key.id,
        key_id=api_key.key_id,
        secret=secret,  # 完整secret，仅此一次显示
        expires_at=api_key.expires_at,
        created_at=api_key.created_at
    )


# ============================================================================
# 23.3 API Key撤销端点
# ============================================================================

@router.delete(
    "/{api_key_id}",
    response_model=APIKeyRevokeResponse,
    summary="撤销API Key",
    description="将指定的API Key设置为不可用状态"
)
async def revoke_api_key(
    api_key_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    撤销（禁用）API Key
    
    - 将is_active设置为False
    - 仅允许撤销当前用户自己的API Key
    - 撤销后的API Key无法再用于认证
    
    Args:
        api_key_id: 要撤销的API Key的ID
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        撤销操作结果
        
    Raises:
        HTTPException: 如果API Key不存在或不属于当前用户
    """
    # 查询API Key（支持通过id或key_id查询）
    result = await db.execute(
        select(APIKey).where(
            ((APIKey.id == api_key_id) | (APIKey.key_id == api_key_id)),
            APIKey.user_id == current_user.id
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API Key不存在或无权访问: {api_key_id}"
        )
    
    # 检查是否已经被撤销
    if not api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"API Key已经被撤销: {api_key_id}"
        )
    
    # 撤销API Key（设置为不可用）
    api_key.is_active = False
    await db.commit()
    
    return APIKeyRevokeResponse(
        message="API Key已成功撤销",
        key_id=api_key.key_id
    )

