/**
 * 服务端认证中间件
 * 保护需要认证的 API 路由
 * 
 * Requirements: 1.4, 12.9
 */
import { eq } from 'drizzle-orm'
import { users } from '@shared/schema'

export default defineEventHandler(async (event) => {
  // 跳过不需要认证的路由
  const publicPaths = [
    '/api/auth/dingtalk',
    '/api/auth/logout',
    '/api/auth/session',
    '/api/health',
    '/api/_nuxt_icon',  // Nuxt Icon 内部 API
  ]

  const path = getRequestURL(event).pathname

  // 公开路由不需要认证
  if (publicPaths.some(p => path.startsWith(p))) {
    return
  }

  // 非 API 路由不需要认证（由客户端中间件处理）
  if (!path.startsWith('/api/')) {
    return
  }

  // 检查会话
  const session = await getUserSession(event)

  if (!session?.user) {
    throw createError({
      statusCode: 401,
      statusMessage: 'Unauthorized',
      message: '请先登录',
    })
  }

  // 从数据库获取最新的用户信息（确保 role 是最新的）
  const db = useDb()
  const dbUser = await db.query.users.findFirst({
    where: eq(users.id, session.user.id),
  })

  if (!dbUser) {
    throw createError({
      statusCode: 401,
      statusMessage: 'Unauthorized',
      message: '用户不存在',
    })
  }

  // 将最新的用户信息附加到 event context
  event.context.user = {
    ...session.user,
    role: dbUser.role, // 使用数据库中最新的 role
  }
})
