/**
 * 更新通知状态 API
 * PATCH /api/notifications/:id
 * 
 * Requirements: 13.10
 * 标记通知为已读
 */
import { z } from 'zod'
import { eq, and } from 'drizzle-orm'
import { notifications } from '@shared/schema'

const updateSchema = z.object({
  isRead: z.boolean(),
})

export default defineEventHandler(async (event) => {
  const db = useDb()
  const notificationId = getRouterParam(event, 'id')

  if (!notificationId) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少通知 ID',
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
  const parsed = updateSchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: parsed.error.errors.map(e => e.message).join(', '),
    })
  }

  const { isRead } = parsed.data

  // 检查通知是否存在且属于当前用户
  const [existing] = await db
    .select({ id: notifications.id })
    .from(notifications)
    .where(
      and(
        eq(notifications.id, notificationId),
        eq(notifications.userId, currentUserId)
      )
    )
    .limit(1)

  if (!existing) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '通知不存在',
    })
  }

  // 更新通知
  const [updated] = await db
    .update(notifications)
    .set({
      isRead,
      readAt: isRead ? new Date() : null,
    })
    .where(eq(notifications.id, notificationId))
    .returning()

  return {
    notification: updated,
  }
})
