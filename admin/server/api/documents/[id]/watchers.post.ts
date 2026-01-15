/**
 * 注册/更新文档查看者 API
 * POST /api/documents/:id/watchers
 * 
 * Requirements: 13.6, 13.7
 * 注册当前用户为文档查看者，或更新心跳时间
 */
import { eq, and, gt, desc } from 'drizzle-orm'
import { documentWatchers, users, versions, documents } from '@shared/schema'
import { z } from 'zod'

// 查看者活跃超时时间（30秒内视为活跃）
const WATCHER_TIMEOUT_MS = 30 * 1000

const bodySchema = z.object({
  versionSeen: z.number().optional(),
})

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

  // 解析请求体
  const body = await readBody(event)
  const parsed = bodySchema.safeParse(body)
  const versionSeen = parsed.success ? parsed.data.versionSeen : undefined

  const now = new Date()

  // 检查是否已存在记录
  const [existing] = await db
    .select({ id: documentWatchers.id })
    .from(documentWatchers)
    .where(
      and(
        eq(documentWatchers.documentId, documentId),
        eq(documentWatchers.userId, currentUserId)
      )
    )
    .limit(1)

  if (existing) {
    // 更新心跳时间
    await db
      .update(documentWatchers)
      .set({
        lastSeenAt: now,
        ...(versionSeen !== undefined ? { lastVersionSeen: versionSeen } : {}),
      })
      .where(eq(documentWatchers.id, existing.id))
  } else {
    // 创建新记录
    await db
      .insert(documentWatchers)
      .values({
        documentId,
        userId: currentUserId,
        lastSeenAt: now,
        lastVersionSeen: versionSeen || null,
      })
  }

  // 清理过期的查看者记录
  const expiredThreshold = new Date(now.getTime() - WATCHER_TIMEOUT_MS * 2)
  await db
    .delete(documentWatchers)
    .where(
      and(
        eq(documentWatchers.documentId, documentId),
        gt(expiredThreshold, documentWatchers.lastSeenAt)
      )
    )

  // 获取当前活跃的查看者
  const activeThreshold = new Date(now.getTime() - WATCHER_TIMEOUT_MS)
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

  // 获取文档最新版本号和更新时间
  const [doc] = await db
    .select({
      updatedAt: documents.updatedAt,
    })
    .from(documents)
    .where(eq(documents.id, documentId))
    .limit(1)

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
      needsRefresh: w.lastVersionSeen !== null && w.lastVersionSeen < currentVersion,
    })),
    currentVersion,
    documentUpdatedAt: doc?.updatedAt,
    // 当前用户是否需要刷新
    needsRefresh: versionSeen !== undefined && versionSeen < currentVersion,
  }
})
