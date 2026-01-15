/**
 * 数据库连接工具
 * 使用 Drizzle ORM 连接 PostgreSQL
 */
import { drizzle } from 'drizzle-orm/postgres-js'
import postgres from 'postgres'
import * as schema from '@shared/schema'

// 数据库连接实例（单例）
let db: ReturnType<typeof drizzle<typeof schema>> | null = null

/**
 * 获取数据库连接实例
 */
export function useDb() {
  if (db) return db

  const config = useRuntimeConfig()

  if (!config.databaseUrl) {
    throw new Error('DATABASE_URL is not configured')
  }

  // 创建 PostgreSQL 连接
  const client = postgres(config.databaseUrl, {
    max: 10, // 最大连接数
    idle_timeout: 20, // 空闲超时（秒）
    connect_timeout: 10, // 连接超时（秒）
  })

  // 创建 Drizzle 实例
  db = drizzle(client, { schema })

  return db
}

/**
 * 获取数据库连接（别名）
 */
export const getDb = useDb
