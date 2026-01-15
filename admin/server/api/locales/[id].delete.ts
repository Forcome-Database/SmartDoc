/**
 * 删除语言 API
 * DELETE /api/locales/:id
 * 
 * Requirements: 6.9
 */
import { locales, documents, categoryTitles, navMenuTitles, translations } from '@shared/schema'
import { eq, or } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const id = getRouterParam(event, 'id')

  if (!id) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少语言 ID',
    })
  }

  // 检查语言是否存在
  const existing = await db
    .select()
    .from(locales)
    .where(eq(locales.id, id))
    .limit(1)

  if (existing.length === 0) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '语言不存在',
    })
  }

  // 检查是否为默认语言
  if (existing[0].isDefault) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '无法删除默认语言，请先设置其他语言为默认',
    })
  }

  // 检查是否有关联的文档
  const relatedDocs = await db
    .select({ id: documents.id })
    .from(documents)
    .where(eq(documents.localeId, id))
    .limit(1)

  if (relatedDocs.length > 0) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '该语言下存在文档，无法删除',
    })
  }

  // 检查是否有关联的翻译任务
  const relatedTranslations = await db
    .select({ id: translations.id })
    .from(translations)
    .where(
      or(
        eq(translations.sourceLocaleId, id),
        eq(translations.targetLocaleId, id)
      )
    )
    .limit(1)

  if (relatedTranslations.length > 0) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '该语言存在关联的翻译任务，无法删除',
    })
  }

  // 删除关联的栏目标题
  await db
    .delete(categoryTitles)
    .where(eq(categoryTitles.localeId, id))

  // 删除关联的导航菜单标题
  await db
    .delete(navMenuTitles)
    .where(eq(navMenuTitles.localeId, id))

  // 删除语言
  await db
    .delete(locales)
    .where(eq(locales.id, id))

  return { success: true, message: '语言已删除' }
})
