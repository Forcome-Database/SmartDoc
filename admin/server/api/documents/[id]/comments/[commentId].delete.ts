/**
 * 删除评论 API
 * DELETE /api/documents/:id/comments/:commentId
 * 
 * Requirements: 13.9
 * 删除评论（只有作者或管理员可以删除）
 */
import { eq, and } from 'drizzle-orm'
import { comments } from '@shared/schema'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const documentId = getRouterParam(event, 'id')
  const commentId = getRouterParam(event, 'commentId')

  if (!documentId || !commentId) {
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
  const isAdmin = session.user.role === 'admin'

  // 检查评论是否存在
  const [existingComment] = await db
    .select({
      id: comments.id,
      authorId: comments.authorId,
      documentId: comments.documentId,
    })
    .from(comments)
    .where(
      and(
        eq(comments.id, commentId),
        eq(comments.documentId, documentId)
      )
    )
    .limit(1)

  if (!existingComment) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '评论不存在',
    })
  }

  // 检查权限
  if (existingComment.authorId !== currentUserId && !isAdmin) {
    throw createError({
      statusCode: 403,
      statusMessage: 'Forbidden',
      message: '没有权限删除此评论',
    })
  }

  // 删除评论（级联删除回复）
  await db
    .delete(comments)
    .where(eq(comments.id, commentId))

  return {
    success: true,
    message: '评论已删除',
  }
})
