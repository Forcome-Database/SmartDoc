/**
 * 删除文档权限 API
 * DELETE /api/documents/:id/permissions/:permissionId
 * 
 * Requirements: 13.12
 * 删除文档的权限设置
 */
import { eq, and } from 'drizzle-orm'
import { documentPermissions, documents } from '@shared/schema'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const documentId = getRouterParam(event, 'id')
  const permissionId = getRouterParam(event, 'permissionId')

  if (!documentId || !permissionId) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少必要参数',
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

  // 检查权限是否存在
  const [existing] = await db
    .select({ id: documentPermissions.id })
    .from(documentPermissions)
    .where(
      and(
        eq(documentPermissions.id, permissionId),
        eq(documentPermissions.documentId, documentId)
      )
    )
    .limit(1)

  if (!existing) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '权限设置不存在',
    })
  }

  // 删除权限
  await db
    .delete(documentPermissions)
    .where(eq(documentPermissions.id, permissionId))

  return {
    success: true,
    message: '权限已删除',
  }
})
