/**
 * 获取文档翻译历史 API
 * GET /api/translations/:documentId
 * 
 * Requirements: 6.8, 6.9
 * 获取指定文档的翻译任务历史
 */
import { eq, desc } from 'drizzle-orm'
import { translations, locales, users, documents } from '@shared/schema'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const documentId = getRouterParam(event, 'documentId')

  if (!documentId) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少文档 ID',
    })
  }

  // 验证文档存在
  const [document] = await db
    .select({ id: documents.id })
    .from(documents)
    .where(eq(documents.id, documentId))
    .limit(1)

  if (!document) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '文档不存在',
    })
  }

  // 获取翻译历史
  const translationRecords = await db
    .select({
      id: translations.id,
      status: translations.status,
      result: translations.result,
      createdAt: translations.createdAt,
      sourceLocale: {
        id: locales.id,
        code: locales.code,
        name: locales.name,
        nativeName: locales.nativeName,
      },
    })
    .from(translations)
    .innerJoin(locales, eq(translations.sourceLocaleId, locales.id))
    .where(eq(translations.documentId, documentId))
    .orderBy(desc(translations.createdAt))

  // 获取目标语言和创建者信息
  const results = await Promise.all(
    translationRecords.map(async (record) => {
      // 获取目标语言
      const [targetLocale] = await db
        .select({
          id: locales.id,
          code: locales.code,
          name: locales.name,
          nativeName: locales.nativeName,
        })
        .from(locales)
        .innerJoin(translations, eq(translations.targetLocaleId, locales.id))
        .where(eq(translations.id, record.id))
        .limit(1)

      // 获取创建者
      const [createdBy] = await db
        .select({
          id: users.id,
          name: users.name,
          avatar: users.avatar,
        })
        .from(users)
        .innerJoin(translations, eq(translations.createdBy, users.id))
        .where(eq(translations.id, record.id))
        .limit(1)

      // 获取翻译后的文档信息（如果有）
      let translatedDocument = null
      if (record.result) {
        const [doc] = await db
          .select({
            id: documents.id,
            title: documents.title,
            slug: documents.slug,
            status: documents.status,
          })
          .from(documents)
          .where(eq(documents.id, record.result))
          .limit(1)
        
        translatedDocument = doc || null
      }

      return {
        id: record.id,
        status: record.status,
        createdAt: record.createdAt,
        sourceLocale: record.sourceLocale,
        targetLocale,
        createdBy,
        translatedDocument,
      }
    })
  )

  return results
})
