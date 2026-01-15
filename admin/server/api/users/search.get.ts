/**
 * 搜索用户 API
 * GET /api/users/search
 * 
 * Requirements: 13.9
 * 用于 @提及用户自动补全
 */
import { ilike, or } from 'drizzle-orm'
import { users } from '@shared/schema'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const query = getQuery(event)

  const searchTerm = (query.q as string) || ''
  const limit = Math.min(20, Math.max(1, parseInt(query.limit as string) || 10))

  // 如果没有搜索词，返回最近的用户
  if (!searchTerm.trim()) {
    const recentUsers = await db
      .select({
        id: users.id,
        name: users.name,
        avatar: users.avatar,
        department: users.department,
      })
      .from(users)
      .limit(limit)

    return {
      users: recentUsers,
    }
  }

  // 搜索用户（按名称或部门）
  const searchPattern = `%${searchTerm}%`
  const matchedUsers = await db
    .select({
      id: users.id,
      name: users.name,
      avatar: users.avatar,
      department: users.department,
    })
    .from(users)
    .where(
      or(
        ilike(users.name, searchPattern),
        ilike(users.department, searchPattern)
      )
    )
    .limit(limit)

  return {
    users: matchedUsers,
  }
})
