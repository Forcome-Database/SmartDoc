/**
 * 获取文档编辑锁 API
 * POST /api/documents/:id/lock
 * 
 * Requirements: 13.2, 13.3, 13.4
 * 获取文档的编辑锁，防止多用户同时编辑
 */
import { eq, and, gt } from 'drizzle-orm'
import { documents, editLocks, users } from '@shared/schema'

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

  const now = new Date()
  const expiresAt = new Date(now.getTime() + LOCK_DURATION_MS)

  // 检查是否已有有效的锁
  const [existingLock] = await db
    .select({
      id: editLocks.id,
      userId: editLocks.userId,
      acquiredAt: editLocks.acquiredAt,
      expiresAt: editLocks.expiresAt,
      userName: users.name,
      userAvatar: users.avatar,
    })
    .from(editLocks)
    .leftJoin(users, eq(editLocks.userId, users.id))
    .where(eq(editLocks.documentId, documentId))
    .limit(1)

  // 如果存在锁
  if (existingLock) {
    // 检查锁是否过期
    if (new Date(existingLock.expiresAt) > now) {
      // 锁未过期
      if (existingLock.userId === currentUserId) {
        // 当前用户已持有锁，续期
        const [updatedLock] = await db
          .update(editLocks)
          .set({
            acquiredAt: now,
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
          renewed: true,
        }
      } else {
        // 其他用户持有锁，拒绝
        throw createError({
          statusCode: 409,
          statusMessage: 'Conflict',
          message: `文档正在被 ${existingLock.userName || '其他用户'} 编辑`,
          data: {
            lockedBy: {
              id: existingLock.userId,
              name: existingLock.userName,
              avatar: existingLock.userAvatar,
            },
            expiresAt: existingLock.expiresAt,
          },
        })
      }
    } else {
      // 锁已过期，删除旧锁
      await db
        .delete(editLocks)
        .where(eq(editLocks.id, existingLock.id))
    }
  }

  // 创建新锁
  const [newLock] = await db
    .insert(editLocks)
    .values({
      documentId,
      userId: currentUserId,
      acquiredAt: now,
      expiresAt,
    })
    .returning()

  return {
    success: true,
    lock: {
      id: newLock.id,
      documentId,
      userId: currentUserId,
      acquiredAt: newLock.acquiredAt,
      expiresAt: newLock.expiresAt,
      user: {
        id: currentUserId,
        name: session.user.name,
        avatar: session.user.avatar,
      },
    },
    renewed: false,
  }
})
