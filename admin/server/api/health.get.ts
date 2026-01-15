/**
 * 健康检查 API
 * 验证数据库连接和服务状态
 */
import { sql } from 'drizzle-orm'

export default defineEventHandler(async () => {
  try {
    const db = useDb()

    // 测试数据库连接
    await db.execute(sql`SELECT 1`)

    return {
      status: 'ok',
      timestamp: new Date().toISOString(),
      database: 'connected',
    }
  } catch (error) {
    return {
      status: 'error',
      timestamp: new Date().toISOString(),
      database: 'disconnected',
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
})
