/**
 * 版本回滚 API
 * POST /api/documents/:id/versions/rollback
 * 
 * Requirements: 4.5, 4.6, 4.7
 * 回滚到指定版本，创建新版本记录
 */
import { z } from 'zod'
import { eq, and, desc } from 'drizzle-orm'
import { documents, versions, users } from '@shared/schema'

// 请求体验证 Schema
const rollbackSchema = z.object({
  versionNum: z.number().int().positive('版本号必须为正整数'),
  changeLog: z.string().max(500).optional(),
})

export default defineEventHandler(async (event) => {
  const db = useDb()
  const id = getRouterParam(event, 'id')

  if (!id) {
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

  // 验证请求体
  const body = await readBody(event)
  const parsed = rollbackSchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: parsed.error.errors.map(e => e.message).join(', '),
    })
  }

  const { versionNum, changeLog } = parsed.data

  // 检查文档是否存在
  const [document] = await db
    .select()
    .from(documents)
    .where(eq(documents.id, id))
    .limit(1)

  if (!document) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '文档不存在',
    })
  }

  // 获取目标版本
  const [targetVersion] = await db
    .select()
    .from(versions)
    .where(
      and(
        eq(versions.documentId, id),
        eq(versions.versionNum, versionNum)
      )
    )
    .limit(1)

  if (!targetVersion) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: `版本 ${versionNum} 不存在`,
    })
  }

  // 获取当前最大版本号
  const [latestVersion] = await db
    .select({ versionNum: versions.versionNum })
    .from(versions)
    .where(eq(versions.documentId, id))
    .orderBy(desc(versions.versionNum))
    .limit(1)

  const nextVersionNum = (latestVersion?.versionNum || 0) + 1

  // 创建新版本（使用目标版本的内容）
  const [newVersion] = await db
    .insert(versions)
    .values({
      documentId: id,
      versionNum: nextVersionNum,
      content: targetVersion.content,
      changeLog: changeLog || `回滚到版本 ${versionNum}`,
      authorId: currentUserId,
    })
    .returning()

  // 更新文档内容
  const [updatedDocument] = await db
    .update(documents)
    .set({
      content: targetVersion.content,
      updatedAt: new Date(),
    })
    .where(eq(documents.id, id))
    .returning()

  // 获取作者信息
  const [author] = await db
    .select({
      id: users.id,
      name: users.name,
      avatar: users.avatar,
    })
    .from(users)
    .where(eq(users.id, currentUserId))
    .limit(1)

  return {
    success: true,
    message: `已回滚到版本 ${versionNum}`,
    document: {
      id: updatedDocument.id,
      title: updatedDocument.title,
      content: updatedDocument.content,
      updatedAt: updatedDocument.updatedAt,
    },
    newVersion: {
      id: newVersion.id,
      versionNum: newVersion.versionNum,
      changeLog: newVersion.changeLog,
      createdAt: newVersion.createdAt,
      author,
    },
    rolledBackFrom: {
      versionNum: targetVersion.versionNum,
      createdAt: targetVersion.createdAt,
    },
  }
})
