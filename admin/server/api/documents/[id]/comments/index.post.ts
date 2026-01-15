/**
 * 添加文档评论 API
 * POST /api/documents/:id/comments
 * 
 * Requirements: 13.9
 * 添加新评论，支持 @提及用户
 */
import { z } from 'zod'
import { eq } from 'drizzle-orm'
import { comments, documents, users } from '@shared/schema'

const createCommentSchema = z.object({
  content: z.string().min(1, '评论内容不能为空').max(2000, '评论内容最多 2000 个字符'),
  parentId: z.string().optional(),
  mentions: z.array(z.string()).optional(),
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
  const parsed = createCommentSchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: parsed.error.errors.map(e => e.message).join(', '),
    })
  }

  const { content, parentId, mentions } = parsed.data

  // 检查文档是否存在
  const [document] = await db
    .select({ id: documents.id })
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

  // 如果是回复，检查父评论是否存在
  if (parentId) {
    const [parentComment] = await db
      .select({ id: comments.id, documentId: comments.documentId })
      .from(comments)
      .where(eq(comments.id, parentId))
      .limit(1)

    if (!parentComment) {
      throw createError({
        statusCode: 404,
        statusMessage: 'Not Found',
        message: '父评论不存在',
      })
    }

    if (parentComment.documentId !== documentId) {
      throw createError({
        statusCode: 400,
        statusMessage: 'Bad Request',
        message: '父评论不属于此文档',
      })
    }
  }

  // 创建评论
  const [newComment] = await db
    .insert(comments)
    .values({
      documentId,
      authorId: currentUserId,
      parentId: parentId || null,
      content,
      mentions: mentions && mentions.length > 0 ? JSON.stringify(mentions) : null,
    })
    .returning()

  // 获取作者信息
  const [author] = await db
    .select({
      id: users.id,
      name: users.name,
      avatar: users.avatar,
    })
    .from(users)
    .where(eq(users.id, currentUserId))
    .limit(1)

  return {
    comment: {
      id: newComment.id,
      documentId: newComment.documentId,
      parentId: newComment.parentId,
      content: newComment.content,
      mentions: mentions || [],
      isResolved: newComment.isResolved,
      createdAt: newComment.createdAt,
      updatedAt: newComment.updatedAt,
      author,
      replies: [],
    },
  }
})
