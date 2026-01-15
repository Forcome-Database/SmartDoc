/**
 * 获取当前会话信息
 * 返回当前登录用户的信息
 * 
 * Requirements: 1.4, 12.5
 */
import { eq } from 'drizzle-orm'
import { users } from '@shared/schema'

export default defineEventHandler(async (event) => {
  const session = await getUserSession(event)

  if (!session?.user) {
    return null
  }

  // 从数据库获取最新的用户信息
  try {
    const db = useDb()
    const user = await db.query.users.findFirst({
      where: eq(users.id, session.user.id),
    })

    if (!user) {
      // 用户不存在，清除会话
      await clearUserSession(event)
      return null
    }

    // 返回用户信息（不包含敏感字段）
    return {
      id: user.id,
      name: user.name,
      avatar: user.avatar,
      email: user.email,
      role: user.role,
      department: user.department,
      dingtalkId: user.dingtalkId,
      createdAt: user.createdAt,
      updatedAt: user.updatedAt,
    }
  } catch (error) {
    console.error('Failed to fetch user from database:', error)
    // 返回会话中的基本信息
    return session.user
  }
})
