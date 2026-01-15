/**
 * 权限检查工具函数
 * 用于检查用户对文档的访问权限
 *
 * Requirements: 13.12
 */
import { eq, and, or } from 'drizzle-orm'
import { documentPermissions, documents } from '@shared/schema'
import type { PermissionLevel, CheckPermissionResult, SessionUser } from '@shared/types'
import { Errors } from './api-response'

// 权限级别优先级（数字越大权限越高）
const PERMISSION_PRIORITY: Record<PermissionLevel, number> = {
  view: 1,
  edit: 2,
  admin: 3,
}

/**
 * 检查用户对文档的权限
 */
export async function checkDocumentPermission(
  documentId: string,
  userId: string,
  userRole: string,
  userDepartmentId?: string | null,
  requiredLevel: PermissionLevel = 'view'
): Promise<CheckPermissionResult> {
  const db = useDb()

  // 系统管理员拥有所有权限
  if (userRole === 'admin') {
    return {
      hasPermission: true,
      level: 'admin',
      isAuthor: false,
      isAdmin: true,
    }
  }

  // 获取文档信息
  const [document] = await db
    .select({
      id: documents.id,
      authorId: documents.authorId,
    })
    .from(documents)
    .where(eq(documents.id, documentId))
    .limit(1)

  if (!document) {
    return {
      hasPermission: false,
      level: null,
      isAuthor: false,
      isAdmin: false,
    }
  }

  // 文档作者拥有管理权限
  if (document.authorId === userId) {
    return {
      hasPermission: true,
      level: 'admin',
      isAuthor: true,
      isAdmin: false,
    }
  }

  // 用户权限或部门权限
  const targetConditions = [
    and(
      eq(documentPermissions.targetType, 'user'),
      eq(documentPermissions.targetId, userId)
    ),
  ]

  if (userDepartmentId) {
    targetConditions.push(
      and(
        eq(documentPermissions.targetType, 'department'),
        eq(documentPermissions.targetId, userDepartmentId)
      )
    )
  }

  // 获取用户的所有权限
  const permissions = await db
    .select({
      level: documentPermissions.level,
    })
    .from(documentPermissions)
    .where(
      and(
        eq(documentPermissions.documentId, documentId),
        or(...targetConditions)
      )
    )

  if (permissions.length === 0) {
    // 没有明确的权限设置，默认允许查看（可根据需求调整）
    return {
      hasPermission: requiredLevel === 'view',
      level: 'view',
      isAuthor: false,
      isAdmin: false,
    }
  }

  // 获取最高权限级别
  let highestLevel: PermissionLevel = 'view'
  for (const p of permissions) {
    if (PERMISSION_PRIORITY[p.level as PermissionLevel] > PERMISSION_PRIORITY[highestLevel]) {
      highestLevel = p.level as PermissionLevel
    }
  }

  // 检查是否满足所需权限
  const hasPermission = PERMISSION_PRIORITY[highestLevel] >= PERMISSION_PRIORITY[requiredLevel]

  return {
    hasPermission,
    level: highestLevel,
    isAuthor: false,
    isAdmin: false,
  }
}

/**
 * 检查用户是否可以查看文档
 */
export async function canViewDocument(
  documentId: string,
  userId: string,
  userRole: string,
  userDepartmentId?: string | null
): Promise<boolean> {
  const result = await checkDocumentPermission(documentId, userId, userRole, userDepartmentId, 'view')
  return result.hasPermission
}

/**
 * 检查用户是否可以编辑文档
 */
export async function canEditDocument(
  documentId: string,
  userId: string,
  userRole: string,
  userDepartmentId?: string | null
): Promise<boolean> {
  const result = await checkDocumentPermission(documentId, userId, userRole, userDepartmentId, 'edit')
  return result.hasPermission
}

/**
 * 检查用户是否可以管理文档权限
 */
export async function canManageDocument(
  documentId: string,
  userId: string,
  userRole: string,
  userDepartmentId?: string | null
): Promise<boolean> {
  const result = await checkDocumentPermission(documentId, userId, userRole, userDepartmentId, 'admin')
  return result.hasPermission
}

// ============ 基于 Event 的权限检查辅助函数 ============

/**
 * 从 event.context 获取当前用户
 * @throws ApiError 如果用户未登录
 */
export function getCurrentUser(event: { context: { user?: SessionUser } }): SessionUser {
  const user = event.context.user
  if (!user) {
    throw Errors.unauthorized()
  }
  return user
}

/**
 * 验证文档权限
 * @throws ApiError 如果没有权限
 */
export async function requireDocumentPermission(
  event: { context: { user?: SessionUser; permission?: CheckPermissionResult } },
  documentId: string,
  level: PermissionLevel = 'view'
): Promise<CheckPermissionResult> {
  const user = getCurrentUser(event)

  const result = await checkDocumentPermission(
    documentId,
    user.id,
    user.role,
    user.departmentId,
    level
  )

  if (!result.hasPermission) {
    throw Errors.forbidden('没有权限访问此文档')
  }

  // 将权限结果附加到 context
  event.context.permission = result
  return result
}

/**
 * 验证管理员权限
 * @throws ApiError 如果不是管理员
 */
export function requireAdminRole(event: { context: { user?: SessionUser } }): SessionUser {
  const user = getCurrentUser(event)
  if (user.role !== 'admin') {
    throw Errors.forbidden('需要管理员权限')
  }
  return user
}

/**
 * 验证编辑者或管理员权限
 * @throws ApiError 如果不是编辑者或管理员
 */
export function requireEditorRole(event: { context: { user?: SessionUser } }): SessionUser {
  const user = getCurrentUser(event)
  if (!['admin', 'editor'].includes(user.role)) {
    throw Errors.forbidden('需要编辑者权限')
  }
  return user
}
