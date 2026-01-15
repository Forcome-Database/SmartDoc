/**
 * 标记所有通知为已读 API
 * POST /api/notifications/read-all
 * 
 * Requirements: 13.10
 */
import { eq, and } from 'drizzle-orm'
import { notifications } from '@shared/schema'

export default defineEventHandler(async (event) => {
  const db = useDb()

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
  const now = new Date()

  // 标记所有未读通知为已读
  const result = await db
    .update(notifications)
    .set({
      isRead: true,
      readAt: now,
    })
    .where(
      and(
        eq(notifications.userId, currentUserId),
        eq(notifications.isRead, false)
      )
    )
    .returning({ id: notifications.id })

  return {
    success: true,
    count: result.length,
    message: `已标记 ${result.length} 条通知为已读`,
  }
})
