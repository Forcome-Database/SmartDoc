/**
 * 获取活动动态列表 API
 * GET /api/activities
 * 
 * Requirements: 13.11
 * 返回最近的文档变更动态
 */
import { eq, desc, and, gte } from 'drizzle-orm'
import { activities, users, documents } from '@shared/schema'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const query = getQuery(event)

  // 分页参数
  const page = Math.max(1, parseInt(query.page as string) || 1)
  const limit = Math.min(50, Math.max(1, parseInt(query.limit as string) || 20))
  const offset = (page - 1) * limit

  // 时间范围（默认最近 7 天）
  const days = Math.min(30, Math.max(1, parseInt(query.days as string) || 7))
  const since = new Date()
  since.setDate(since.getDate() - days)

  // 用户过滤
  const userId = query.userId as string | undefined

  // 构建查询条件
  const conditions = [gte(activities.createdAt, since)]
  if (userId) {
    conditions.push(eq(activities.userId, userId))
  }

  // 获取活动列表
  const activityList = await db
    .select({
      id: activities.id,
      type: activities.type,
      documentId: activities.documentId,
      documentTitle: activities.documentTitle,
      versionNum: activities.versionNum,
      commentId: activities.commentId,
      metadata: activities.metadata,
      createdAt: activities.createdAt,
      // 用户信息
      userId: activities.userId,
      userName: users.name,
      userAvatar: users.avatar,
    })
    .from(activities)
    .leftJoin(users, eq(activities.userId, users.id))
    .where(and(...conditions))
    .orderBy(desc(activities.createdAt))
    .limit(limit)
    .offset(offset)

  // 获取总数
  const allActivities = await db
    .select({ id: activities.id })
    .from(activities)
    .where(and(...conditions))

  const total = allActivities.length

  return {
    activities: activityList.map(a => ({
      id: a.id,
      type: a.type,
      documentId: a.documentId,
      documentTitle: a.documentTitle,
      versionNum: a.versionNum,
      commentId: a.commentId,
      metadata: a.metadata ? JSON.parse(a.metadata) : null,
      createdAt: a.createdAt,
      user: {
        id: a.userId,
        name: a.userName,
        avatar: a.userAvatar,
      },
    })),
    pagination: {
      page,
      limit,
      total,
      totalPages: Math.ceil(total / limit),
    },
  }
})
