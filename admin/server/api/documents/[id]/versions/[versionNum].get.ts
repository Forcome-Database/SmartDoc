/**
 * 获取文档特定版本 API
 * GET /api/documents/:id/versions/:versionNum
 * 
 * Requirements: 4.3
 * 返回文档特定版本的完整内容
 */
import { eq, and } from 'drizzle-orm'
import { documents, versions, users } from '@shared/schema'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const id = getRouterParam(event, 'id')
  const versionNumStr = getRouterParam(event, 'versionNum')

  if (!id) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少文档 ID',
    })
  }

  if (!versionNumStr) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少版本号',
    })
  }

  const versionNum = parseInt(versionNumStr)
  if (isNaN(versionNum) || versionNum < 1) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '无效的版本号',
    })
  }

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

  // 获取指定版本
  const [version] = await db
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
    .where(
      and(
        eq(versions.documentId, id),
        eq(versions.versionNum, versionNum)
      )
    )
    .limit(1)

  if (!version) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: `版本 ${versionNum} 不存在`,
    })
  }

  return {
    id: version.id,
    documentId: version.documentId,
    versionNum: version.versionNum,
    content: version.content,
    changeLog: version.changeLog,
    createdAt: version.createdAt,
    isPublished: document.publishedVersion === version.versionNum,
    author: version.authorId ? {
      id: version.authorId,
      name: version.authorName,
      avatar: version.authorAvatar,
    } : null,
    document: {
      id: document.id,
      title: document.title,
      publishedVersion: document.publishedVersion,
    },
  }
})
