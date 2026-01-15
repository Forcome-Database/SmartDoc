/**
 * 添加文档权限 API
 * POST /api/documents/:id/permissions
 * 
 * Requirements: 13.12
 * 为文档添加权限设置
 */
import { z } from 'zod'
import { eq, and } from 'drizzle-orm'
import { documentPermissions, documents, users } from '@shared/schema'

const createPermissionSchema = z.object({
  targetType: z.enum(['user', 'department']),
  targetId: z.string().min(1, '目标 ID 不能为空'),
  level: z.enum(['view', 'edit', 'admin']),
})

export default defineEventHandler(async (event) => {
  const db = useDb()
  const documentId = getRouterParam(event, 'id')

  if (!documentId) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少文档 ID',
    })
  }

  // 获取当前用户
  const session = await getUserSession(event)
  if (!session?.user?.id) {
    throw createError({
      statusCode: 401,
      statusMessage: 'Unauthorized',
      message: '请先登录',
    })
  }

  const currentUserId = session.user.id

  // 验证请求体
  const body = await readBody(event)
  const parsed = createPermissionSchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: parsed.error.errors.map(e => e.message).join(', '),
    })
  }

  const { targetType, targetId, level } = parsed.data

  // 检查文档是否存在
  const [document] = await db
    .select({
      id: documents.id,
      authorId: documents.authorId,
    })
    .from(documents)
    .where(eq(documents.id, documentId))
    .limit(1)

  if (!document) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '文档不存在',
    })
  }

  // 检查当前用户是否有管理权限
  const isAuthor = document.authorId === currentUserId
  const isAdmin = session.user.role === 'admin'

  if (!isAuthor && !isAdmin) {
    // 检查是否有 admin 级别的权限
    const [adminPermission] = await db
      .select({ id: documentPermissions.id })
      .from(documentPermissions)
      .where(
        and(
          eq(documentPermissions.documentId, documentId),
          eq(documentPermissions.targetType, 'user'),
          eq(documentPermissions.targetId, currentUserId),
          eq(documentPermissions.level, 'admin')
        )
      )
      .limit(1)

    if (!adminPermission) {
      throw createError({
        statusCode: 403,
        statusMessage: 'Forbidden',
        message: '没有权限管理此文档的权限设置',
      })
    }
  }

  // 如果是用户权限，验证用户存在
  if (targetType === 'user') {
    const [targetUser] = await db
      .select({ id: users.id })
      .from(users)
      .where(eq(users.id, targetId))
      .limit(1)

    if (!targetUser) {
      throw createError({
        statusCode: 400,
        statusMessage: 'Bad Request',
        message: '目标用户不存在',
      })
    }
  }

  // 检查是否已存在相同的权限设置
  const [existing] = await db
    .select({ id: documentPermissions.id })
    .from(documentPermissions)
    .where(
      and(
        eq(documentPermissions.documentId, documentId),
        eq(documentPermissions.targetType, targetType),
        eq(documentPermissions.targetId, targetId)
      )
    )
    .limit(1)

  if (existing) {
    // 更新现有权限
    const [updated] = await db
      .update(documentPermissions)
      .set({
        level,
        updatedAt: new Date(),
      })
      .where(eq(documentPermissions.id, existing.id))
      .returning()

    return {
      permission: updated,
      updated: true,
    }
  }

  // 创建新权限
  const [newPermission] = await db
    .insert(documentPermissions)
    .values({
      documentId,
      targetType,
      targetId,
      level,
      createdBy: currentUserId,
    })
    .returning()

  // 获取用户信息（如果是用户权限）
  let user = null
  if (targetType === 'user') {
    const [u] = await db
      .select({
        id: users.id,
        name: users.name,
        avatar: users.avatar,
      })
      .from(users)
      .where(eq(users.id, targetId))
      .limit(1)
    user = u
  }

  return {
    permission: {
      ...newPermission,
      user,
    },
    updated: false,
  }
})
