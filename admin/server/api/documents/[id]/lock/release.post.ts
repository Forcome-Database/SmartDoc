/**
 * Beacon 释放文档编辑锁 API
 * POST /api/documents/:id/lock/release
 * 
 * Requirements: 13.2, 13.4
 * 使用 Beacon API 在页面卸载时释放锁
 * 
 * 注意：Beacon API 只支持 POST 请求，且不能读取响应
 * 因此这个端点专门用于页面关闭时的锁释放
 */
import { eq, and } from 'drizzle-orm'
import { editLocks } from '@shared/schema'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const documentId = getRouterParam(event, 'id')

  if (!documentId) {
    // Beacon 请求不需要返回详细错误
    return { success: false }
  }

  // 获取当前用户
  const session = await getUserSession(event)
  if (!session?.user?.id) {
    return { success: false }
  }

  const currentUserId = session.user.id

  try {
    // 尝试删除当前用户持有的锁
    await db
      .delete(editLocks)
      .where(
        and(
          eq(editLocks.documentId, documentId),
          eq(editLocks.userId, currentUserId)
        )
      )

    return { success: true }
  } catch (error) {
    // Beacon 请求失败时静默处理
    console.error('Beacon lock release error:', error)
    return { success: false }
  }
})
