/**
 * 获取文档的所有语言版本 API
 * GET /api/documents/:id/related
 * 
 * 根据文档的 slug 和 categoryId 查找所有语言版本
 */
import { eq, and } from 'drizzle-orm'
import { documents, locales } from '@shared/schema'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const id = getRouterParam(event, 'id')

  if (!id) {
    throw createError({
      statusCode: 400,
      message: '缺少文档 ID',
    })
  }

  // 获取当前文档信息
  const [currentDoc] = await db
    .select({
      id: documents.id,
      slug: documents.slug,
      categoryId: documents.categoryId,
    })
    .from(documents)
    .where(eq(documents.id, id))
    .limit(1)

  if (!currentDoc) {
    throw createError({
      statusCode: 404,
      message: '文档不存在',
    })
  }

  // 查找同一 slug 和 categoryId 的所有语言版本
  const conditions = [eq(documents.slug, currentDoc.slug)]
  
  if (currentDoc.categoryId) {
    conditions.push(eq(documents.categoryId, currentDoc.categoryId))
  } else {
    // 如果没有 categoryId，只查找同样没有 categoryId 的文档
    // 使用 SQL 的 IS NULL 比较
  }

  const relatedDocs = await db
    .select({
      id: documents.id,
      title: documents.title,
      slug: documents.slug,
      status: documents.status,
      hasUnpublishedChanges: documents.hasUnpublishedChanges,
      localeId: documents.localeId,
      localeCode: locales.code,
      localeName: locales.nativeName,
    })
    .from(documents)
    .innerJoin(locales, eq(documents.localeId, locales.id))
    .where(
      currentDoc.categoryId 
        ? and(eq(documents.slug, currentDoc.slug), eq(documents.categoryId, currentDoc.categoryId))
        : eq(documents.slug, currentDoc.slug)
    )

  return relatedDocs.map(doc => ({
    id: doc.id,
    title: doc.title,
    localeCode: doc.localeCode,
    localeName: doc.localeName,
    status: doc.status,
    hasUnpublishedChanges: doc.hasUnpublishedChanges,
  }))
})
