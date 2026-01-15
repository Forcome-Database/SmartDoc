/**
 * 获取通知列表 API
 * GET /api/notifications
 * 
 * Requirements: 13.10
 * 返回当前用户的通知列表
 */
import { eq, desc, and } from 'drizzle-orm'
import { notifications, users, documents } from '@shared/schema'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const query = getQuery(event)

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

  // 分页参数
  const page = Math.max(1, parseInt(query.page as string) || 1)
  const limit = Math.min(50, Math.max(1, parseInt(query.limit as string) || 20))
  const offset = (page - 1) * limit

  // 是否只显示未读
  const unreadOnly = query.unreadOnly === 'true'

  // 构建查询条件
  const conditions = [eq(notifications.userId, currentUserId)]
  if (unreadOnly) {
    conditions.push(eq(notifications.isRead, false))
  }

  // 获取通知列表
  const notificationList = await db
    .select({
      id: notifications.id,
      type: notifications.type,
      title: notifications.title,
      content: notifications.content,
      documentId: notifications.documentId,
      commentId: notifications.commentId,
      fromUserId: notifications.fromUserId,
      isRead: notifications.isRead,
      readAt: notifications.readAt,
      createdAt: notifications.createdAt,
      // 关联数据
      documentTitle: documents.title,
      fromUserName: users.name,
      fromUserAvatar: users.avatar,
    })
    .from(notifications)
    .leftJoin(documents, eq(notifications.documentId, documents.id))
    .leftJoin(users, eq(notifications.fromUserId, users.id))
    .where(and(...conditions))
    .orderBy(desc(notifications.createdAt))
    .limit(limit)
    .offset(offset)

  // 获取总数
  const allNotifications = await db
    .select({ id: notifications.id })
    .from(notifications)
    .where(and(...conditions))

  const total = allNotifications.length

  // 获取未读数量
  const unreadNotifications = await db
    .select({ id: notifications.id })
    .from(notifications)
    .where(
      and(
        eq(notifications.userId, currentUserId),
        eq(notifications.isRead, false)
      )
    )

  const unreadCount = unreadNotifications.length

  return {
    notifications: notificationList.map(n => ({
      id: n.id,
      type: n.type,
      title: n.title,
      content: n.content,
      documentId: n.documentId,
      documentTitle: n.documentTitle,
      commentId: n.commentId,
      isRead: n.isRead,
      readAt: n.readAt,
      createdAt: n.createdAt,
      fromUser: n.fromUserId ? {
        id: n.fromUserId,
        name: n.fromUserName,
        avatar: n.fromUserAvatar,
      } : null,
    })),
    pagination: {
      page,
      limit,
      total,
      totalPages: Math.ceil(total / limit),
    },
    unreadCount,
  }
})
