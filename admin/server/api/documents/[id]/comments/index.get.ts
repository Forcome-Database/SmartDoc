/**
 * 获取文档评论列表 API
 * GET /api/documents/:id/comments
 * 
 * Requirements: 13.9
 * 返回文档的所有评论，包含作者信息和回复
 */
import { eq, desc, isNull } from 'drizzle-orm'
import { comments, users } from '@shared/schema'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const documentId = getRouterParam(event, 'id')
  const query = getQuery(event)

  if (!documentId) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少文档 ID',
    })
  }

  // 是否只显示未解决的评论
  const unresolvedOnly = query.unresolvedOnly === 'true'

  // 获取顶级评论（没有 parentId 的）
  const topLevelComments = await db
    .select({
      id: comments.id,
      documentId: comments.documentId,
      authorId: comments.authorId,
      parentId: comments.parentId,
      content: comments.content,
      mentions: comments.mentions,
      isResolved: comments.isResolved,
      createdAt: comments.createdAt,
      updatedAt: comments.updatedAt,
      authorName: users.name,
      authorAvatar: users.avatar,
    })
    .from(comments)
    .leftJoin(users, eq(comments.authorId, users.id))
    .where(
      unresolvedOnly
        ? eq(comments.documentId, documentId) && isNull(comments.parentId) && eq(comments.isResolved, false)
        : eq(comments.documentId, documentId) && isNull(comments.parentId)
    )
    .orderBy(desc(comments.createdAt))

  // 获取所有回复
  const allReplies = await db
    .select({
      id: comments.id,
      documentId: comments.documentId,
      authorId: comments.authorId,
      parentId: comments.parentId,
      content: comments.content,
      mentions: comments.mentions,
      isResolved: comments.isResolved,
      createdAt: comments.createdAt,
      updatedAt: comments.updatedAt,
      authorName: users.name,
      authorAvatar: users.avatar,
    })
    .from(comments)
    .leftJoin(users, eq(comments.authorId, users.id))
    .where(eq(comments.documentId, documentId))
    .orderBy(comments.createdAt)

  // 构建评论树
  const repliesMap = new Map<string, typeof allReplies>()
  for (const reply of allReplies) {
    if (reply.parentId) {
      const existing = repliesMap.get(reply.parentId) || []
      existing.push(reply)
      repliesMap.set(reply.parentId, existing)
    }
  }

  // 格式化评论
  const formatComment = (comment: typeof topLevelComments[0]) => ({
    id: comment.id,
    documentId: comment.documentId,
    parentId: comment.parentId,
    content: comment.content,
    mentions: comment.mentions ? JSON.parse(comment.mentions) : [],
    isResolved: comment.isResolved,
    createdAt: comment.createdAt,
    updatedAt: comment.updatedAt,
    author: {
      id: comment.authorId,
      name: comment.authorName,
      avatar: comment.authorAvatar,
    },
    replies: (repliesMap.get(comment.id) || []).map(reply => ({
      id: reply.id,
      documentId: reply.documentId,
      parentId: reply.parentId,
      content: reply.content,
      mentions: reply.mentions ? JSON.parse(reply.mentions) : [],
      isResolved: reply.isResolved,
      createdAt: reply.createdAt,
      updatedAt: reply.updatedAt,
      author: {
        id: reply.authorId,
        name: reply.authorName,
        avatar: reply.authorAvatar,
      },
    })),
  })

  return {
    comments: topLevelComments.map(formatComment),
    total: topLevelComments.length,
  }
})
