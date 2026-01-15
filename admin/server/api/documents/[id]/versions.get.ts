/**
 * 获取文档版本历史 API
 * GET /api/documents/:id/versions
 * 
 * Requirements: 4.1, 4.2
 * 返回文档的所有版本历史，包含作者信息
 */
import { eq, desc, asc } from 'drizzle-orm'
import { documents, versions, users } from '@shared/schema'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const id = getRouterParam(event, 'id')
  const query = getQuery(event)

  if (!id) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少文档 ID',
    })
  }

  // 分页参数
  const page = Math.max(1, parseInt(query.page as string) || 1)
  const limit = Math.min(100, Math.max(1, parseInt(query.limit as string) || 20))
  const offset = (page - 1) * limit

  // 排序参数（默认按版本号降序）
  const sortOrder = (query.sortOrder as string) === 'asc' ? 'asc' : 'desc'

  // 检查文档是否存在
  const [document] = await db
    .select({
      id: documents.id,
      title: documents.title,
      publishedVersion: documents.publishedVersion,
    })
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

  // 获取版本总数
  const allVersions = await db
    .select({ id: versions.id })
    .from(versions)
    .where(eq(versions.documentId, id))

  const total = allVersions.length

  // 获取版本列表
  const orderFn = sortOrder === 'asc' ? asc : desc

  const versionList = await db
    .select({
      id: versions.id,
      documentId: versions.documentId,
      versionNum: versions.versionNum,
      content: versions.content,
      changeLog: versions.changeLog,
      authorId: versions.authorId,
      createdAt: versions.createdAt,
      // 作者信息
      authorName: users.name,
      authorAvatar: users.avatar,
    })
    .from(versions)
    .leftJoin(users, eq(versions.authorId, users.id))
    .where(eq(versions.documentId, id))
    .orderBy(orderFn(versions.versionNum))
    .limit(limit)
    .offset(offset)

  // 组装返回数据
  const items = versionList.map(v => ({
    id: v.id,
    documentId: v.documentId,
    versionNum: v.versionNum,
    changeLog: v.changeLog,
    createdAt: v.createdAt,
    isPublished: document.publishedVersion === v.versionNum,
    author: v.authorId ? {
      id: v.authorId,
      name: v.authorName,
      avatar: v.authorAvatar,
    } : null,
    // 内容摘要（前 200 字符）
    contentPreview: v.content.substring(0, 200) + (v.content.length > 200 ? '...' : ''),
  }))

  return {
    document: {
      id: document.id,
      title: document.title,
      publishedVersion: document.publishedVersion,
    },
    items,
    pagination: {
      page,
      limit,
      total,
      totalPages: Math.ceil(total / limit),
    },
  }
})
