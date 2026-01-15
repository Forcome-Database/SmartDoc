/**
 * 释放文档编辑锁 API
 * DELETE /api/documents/:id/lock
 * 
 * Requirements: 13.2, 13.4
 * 释放当前用户持有的编辑锁
 */
import { eq, and } from 'drizzle-orm'
import { editLocks } from '@shared/schema'

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

  // 查找并删除当前用户持有的锁
  const result = await db
    .delete(editLocks)
    .where(
      and(
        eq(editLocks.documentId, documentId),
        eq(editLocks.userId, currentUserId)
      )
    )
    .returning({ id: editLocks.id })

  if (result.length === 0) {
    // 锁不存在或不属于当前用户，但这不是错误
    // 可能是锁已过期被自动清理，或者用户没有持有锁
    return {
      success: true,
      released: false,
      message: '未找到需要释放的锁',
    }
  }

  return {
    success: true,
    released: true,
    message: '编辑锁已释放',
  }
})
