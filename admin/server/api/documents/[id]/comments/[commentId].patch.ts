/**
 * 更新评论 API
 * PATCH /api/documents/:id/comments/:commentId
 * 
 * Requirements: 13.9
 * 更新评论内容或标记为已解决
 */
import { z } from 'zod'
import { eq, and } from 'drizzle-orm'
import { comments, users } from '@shared/schema'

const updateCommentSchema = z.object({
  content: z.string().min(1).max(2000).optional(),
  isResolved: z.boolean().optional(),
  mentions: z.array(z.string()).optional(),
})

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

  // 验证请求体
  const body = await readBody(event)
  const parsed = updateCommentSchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: parsed.error.errors.map(e => e.message).join(', '),
    })
  }

  const { content, isResolved, mentions } = parsed.data

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

  // 只有作者可以编辑内容，但任何人都可以标记为已解决
  if (content !== undefined && existingComment.authorId !== currentUserId) {
    throw createError({
      statusCode: 403,
      statusMessage: 'Forbidden',
      message: '只有作者可以编辑评论',
    })
  }

  // 构建更新数据
  const updateData: Partial<typeof comments.$inferInsert> = {
    updatedAt: new Date(),
  }

  if (content !== undefined) {
    updateData.content = content
  }

  if (isResolved !== undefined) {
    updateData.isResolved = isResolved
  }

  if (mentions !== undefined) {
    updateData.mentions = mentions.length > 0 ? JSON.stringify(mentions) : null
  }

  // 更新评论
  const [updatedComment] = await db
    .update(comments)
    .set(updateData)
    .where(eq(comments.id, commentId))
    .returning()

  // 获取作者信息
  const [author] = await db
    .select({
      id: users.id,
      name: users.name,
      avatar: users.avatar,
    })
    .from(users)
    .where(eq(users.id, updatedComment.authorId))
    .limit(1)

  return {
    comment: {
      id: updatedComment.id,
      documentId: updatedComment.documentId,
      parentId: updatedComment.parentId,
      content: updatedComment.content,
      mentions: updatedComment.mentions ? JSON.parse(updatedComment.mentions) : [],
      isResolved: updatedComment.isResolved,
      createdAt: updatedComment.createdAt,
      updatedAt: updatedComment.updatedAt,
      author,
    },
  }
})
