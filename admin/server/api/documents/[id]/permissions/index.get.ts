/**
 * 获取文档权限列表 API
 * GET /api/documents/:id/permissions
 * 
 * Requirements: 13.12
 * 返回文档的权限设置列表
 */
import { eq } from 'drizzle-orm'
import { documentPermissions, users, documents } from '@shared/schema'

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

  // 获取权限列表
  const permissions = await db
    .select({
      id: documentPermissions.id,
      documentId: documentPermissions.documentId,
      targetType: documentPermissions.targetType,
      targetId: documentPermissions.targetId,
      level: documentPermissions.level,
      createdBy: documentPermissions.createdBy,
      createdAt: documentPermissions.createdAt,
      updatedAt: documentPermissions.updatedAt,
    })
    .from(documentPermissions)
    .where(eq(documentPermissions.documentId, documentId))

  // 获取用户类型权限的用户信息
  const userPermissions = permissions.filter(p => p.targetType === 'user')
  const userIds = userPermissions.map(p => p.targetId)

  let usersMap: Record<string, { id: string; name: string; avatar: string | null }> = {}
  if (userIds.length > 0) {
    const userList = await db
      .select({
        id: users.id,
        name: users.name,
        avatar: users.avatar,
      })
      .from(users)

    usersMap = Object.fromEntries(userList.map(u => [u.id, u]))
  }

  return {
    permissions: permissions.map(p => ({
      id: p.id,
      documentId: p.documentId,
      targetType: p.targetType,
      targetId: p.targetId,
      level: p.level,
      createdAt: p.createdAt,
      updatedAt: p.updatedAt,
      // 如果是用户权限，附加用户信息
      user: p.targetType === 'user' ? usersMap[p.targetId] || null : null,
    })),
    // 文档作者始终有管理权限
    authorId: document.authorId,
  }
})
