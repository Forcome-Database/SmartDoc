"""
用户管理端点
实现用户的CRUD操作，仅Admin角色可访问
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.core.security import hash_password, verify_password
from app.models.user import User, RoleEnum
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserStatusUpdate,
    UserListResponse,
    UserDetailResponse,
    PaginatedUserResponse
)
from app.schemas.response import SuccessResponse

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("", response_model=PaginatedUserResponse, summary="获取用户列表")
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    username: Optional[str] = Query(None, description="用户名筛选（模糊匹配）"),
    email: Optional[str] = Query(None, description="邮箱筛选（模糊匹配）"),
    role: Optional[RoleEnum] = Query(None, description="角色筛选"),
    is_active: Optional[bool] = Query(None, description="状态筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    获取用户列表
    
    - 支持分页
    - 支持按用户名、邮箱、角色、状态筛选
    - 仅Admin角色可访问
    
    Args:
        page: 页码
        page_size: 每页数量
        username: 用户名筛选（模糊匹配）
        email: 邮箱筛选（模糊匹配）
        role: 角色筛选
        is_active: 状态筛选
        db: 数据库会话
        current_user: 当前用户（Admin）
        
    Returns:
        PaginatedUserResponse: 分页用户列表
    """
    # 构建查询条件
    query = select(User)
    
    # 应用筛选条件
    if username:
        query = query.where(User.username.like(f"%{username}%"))
    
    if email:
        query = query.where(User.email.like(f"%{email}%"))
    
    if role:
        query = query.where(User.role == role)
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    # 查询总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    # 计算总页数
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedUserResponse(
        items=[UserListResponse.from_orm(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("", response_model=UserDetailResponse, status_code=status.HTTP_201_CREATED, summary="创建用户")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    创建新用户
    
    - 验证用户名和邮箱唯一性
    - 使用bcrypt哈希存储密码
    - 仅Admin角色可访问
    
    Args:
        user_data: 用户创建数据
        db: 数据库会话
        current_user: 当前用户（Admin）
        
    Returns:
        UserDetailResponse: 创建的用户信息
        
    Raises:
        HTTPException: 400 - 用户名或邮箱已存在
    """
    # 检查用户名是否已存在
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )
    
    # 创建新用户
    new_user = User(
        id=f"U_{uuid.uuid4().hex[:12].upper()}",
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return UserDetailResponse.from_orm(new_user)


@router.get("/{user_id}", response_model=UserDetailResponse, summary="获取用户详情")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    获取用户详情
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        current_user: 当前用户（Admin）
        
    Returns:
        UserDetailResponse: 用户详情
        
    Raises:
        HTTPException: 404 - 用户不存在
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserDetailResponse.from_orm(user)


@router.put("/{user_id}", response_model=UserDetailResponse, summary="更新用户信息")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    更新用户信息
    
    - 可更新用户名、邮箱、角色
    - 支持修改密码（需验证旧密码）
    - 仅Admin角色可访问
    
    Args:
        user_id: 用户ID
        user_data: 用户更新数据
        db: 数据库会话
        current_user: 当前用户（Admin）
        
    Returns:
        UserDetailResponse: 更新后的用户信息
        
    Raises:
        HTTPException: 404 - 用户不存在
        HTTPException: 400 - 用户名或邮箱已存在
        HTTPException: 400 - 旧密码错误
    """
    # 查询用户
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新用户名
    if user_data.username and user_data.username != user.username:
        # 检查用户名是否已被其他用户使用
        result = await db.execute(
            select(User).where(
                User.username == user_data.username,
                User.id != user_id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        user.username = user_data.username
    
    # 更新邮箱
    if user_data.email and user_data.email != user.email:
        # 检查邮箱是否已被其他用户使用
        result = await db.execute(
            select(User).where(
                User.email == user_data.email,
                User.id != user_id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
        user.email = user_data.email
    
    # 更新角色
    if user_data.role:
        user.role = user_data.role
    
    # 更新密码
    if user_data.new_password:
        # 验证旧密码
        if not user_data.old_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="修改密码时必须提供旧密码"
            )
        
        if not verify_password(user_data.old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码错误"
            )
        
        # 更新密码
        user.password_hash = hash_password(user_data.new_password)
    
    await db.commit()
    await db.refresh(user)
    
    return UserDetailResponse.from_orm(user)


@router.patch("/{user_id}/status", response_model=UserDetailResponse, summary="更新用户状态")
async def update_user_status(
    user_id: str,
    status_data: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    更新用户状态（启用/禁用）
    
    - 切换用户is_active状态
    - 仅Admin角色可访问
    
    Args:
        user_id: 用户ID
        status_data: 状态更新数据
        db: 数据库会话
        current_user: 当前用户（Admin）
        
    Returns:
        UserDetailResponse: 更新后的用户信息
        
    Raises:
        HTTPException: 404 - 用户不存在
        HTTPException: 400 - 不能禁用自己
    """
    # 查询用户
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 不允许禁用自己
    if user_id == current_user.id and not status_data.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己的账号"
        )
    
    # 更新状态
    user.is_active = status_data.is_active
    
    await db.commit()
    await db.refresh(user)
    
    return UserDetailResponse.from_orm(user)


@router.delete("/{user_id}", response_model=SuccessResponse, summary="删除用户")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    删除用户（软删除）
    
    - 设置is_active=False实现软删除
    - 不允许删除最后一个Admin用户
    - 不允许删除自己
    - 仅Admin角色可访问
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        current_user: 当前用户（Admin）
        
    Returns:
        SuccessResponse: 成功消息
        
    Raises:
        HTTPException: 404 - 用户不存在
        HTTPException: 400 - 不能删除自己
        HTTPException: 400 - 不能删除最后一个Admin用户
    """
    # 查询用户
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 不允许删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账号"
        )
    
    # 如果要删除的是Admin用户，检查是否是最后一个Admin
    if user.role == RoleEnum.ADMIN:
        result = await db.execute(
            select(func.count()).select_from(User).where(
                User.role == RoleEnum.ADMIN,
                User.is_active == True,
                User.id != user_id
            )
        )
        active_admin_count = result.scalar()
        
        if active_admin_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除最后一个Admin用户"
            )
    
    # 软删除：设置is_active=False
    user.is_active = False
    
    await db.commit()
    
    return SuccessResponse(
        message=f"用户 {user.username} 已被删除"
    )
