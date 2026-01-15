/**
 * 续期文档编辑锁 API
 * PATCH /api/documents/:id/lock
 * 
 * Requirements: 13.2, 13.4
 * 续期当前用户持有的编辑锁
 */
import { eq, and } from 'drizzle-orm'
import { editLocks, users } from '@shared/schema'

// 锁的默认有效期（5分钟）
const LOCK_DURATION_MS = 5 * 60 * 1000

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
  const now = new Date()
  const expiresAt = new Date(now.getTime() + LOCK_DURATION_MS)

  // 查找当前用户持有的锁
  const [existingLock] = await db
    .select({
      id: editLocks.id,
      userId: editLocks.userId,
      expiresAt: editLocks.expiresAt,
    })
    .from(editLocks)
    .where(
      and(
        eq(editLocks.documentId, documentId),
        eq(editLocks.userId, currentUserId)
      )
    )
    .limit(1)

  if (!existingLock) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '未找到编辑锁，可能已被释放或过期',
    })
  }

  // 检查锁是否已过期
  if (new Date(existingLock.expiresAt) <= now) {
    // 锁已过期，删除并返回错误
    await db
      .delete(editLocks)
      .where(eq(editLocks.id, existingLock.id))

    throw createError({
      statusCode: 410,
      statusMessage: 'Gone',
      message: '编辑锁已过期，请重新获取',
    })
  }

  // 续期锁
  const [updatedLock] = await db
    .update(editLocks)
    .set({
      expiresAt,
    })
    .where(eq(editLocks.id, existingLock.id))
    .returning()

  return {
    success: true,
    lock: {
      id: updatedLock.id,
      documentId,
      userId: currentUserId,
      acquiredAt: updatedLock.acquiredAt,
      expiresAt: updatedLock.expiresAt,
      user: {
        id: currentUserId,
        name: session.user.name,
        avatar: session.user.avatar,
      },
    },
  }
})
