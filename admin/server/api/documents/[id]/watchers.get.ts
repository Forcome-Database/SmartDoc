/**
 * 获取文档查看者列表 API
 * GET /api/documents/:id/watchers
 * 
 * Requirements: 13.6
 * 返回当前正在查看文档的用户列表
 */
import { eq, gt, and, desc } from 'drizzle-orm'
import { documentWatchers, users, versions } from '@shared/schema'

// 查看者活跃超时时间（30秒内视为活跃）
const WATCHER_TIMEOUT_MS = 30 * 1000

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

  const now = new Date()
  const activeThreshold = new Date(now.getTime() - WATCHER_TIMEOUT_MS)

  // 获取活跃的查看者
  const watchers = await db
    .select({
      id: users.id,
      name: users.name,
      avatar: users.avatar,
      lastSeenAt: documentWatchers.lastSeenAt,
      lastVersionSeen: documentWatchers.lastVersionSeen,
    })
    .from(documentWatchers)
    .innerJoin(users, eq(documentWatchers.userId, users.id))
    .where(
      and(
        eq(documentWatchers.documentId, documentId),
        gt(documentWatchers.lastSeenAt, activeThreshold)
      )
    )
    .orderBy(desc(documentWatchers.lastSeenAt))

  // 获取文档最新版本号
  const [latestVersion] = await db
    .select({ versionNum: versions.versionNum })
    .from(versions)
    .where(eq(versions.documentId, documentId))
    .orderBy(desc(versions.versionNum))
    .limit(1)

  const currentVersion = latestVersion?.versionNum || 1

  return {
    watchers: watchers.map(w => ({
      id: w.id,
      name: w.name,
      avatar: w.avatar,
      lastSeenAt: w.lastSeenAt,
      // 标记是否需要刷新（查看的版本落后于当前版本）
      needsRefresh: w.lastVersionSeen !== null && w.lastVersionSeen < currentVersion,
    })),
    currentVersion,
  }
})
