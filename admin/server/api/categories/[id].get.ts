/**
 * 获取栏目详情 API
 * GET /api/categories/:id
 * 
 * Requirements: 2.1
 * 返回单个栏目的详细信息，包含多语言标题
 */
import { eq } from 'drizzle-orm'
import { categories, categoryTitles, locales } from '@shared/schema'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const id = getRouterParam(event, 'id')

  if (!id) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少栏目 ID',
    })
  }

  // 获取栏目
  const [category] = await db
    .select()
    .from(categories)
    .where(eq(categories.id, id))
    .limit(1)

  if (!category) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '栏目不存在',
    })
  }

  // 获取栏目标题
  const titles = await db
    .select({
      localeId: categoryTitles.localeId,
      localeCode: locales.code,
      title: categoryTitles.title,
    })
    .from(categoryTitles)
    .innerJoin(locales, eq(categoryTitles.localeId, locales.id))
    .where(eq(categoryTitles.categoryId, id))

  // 构建标题映射
  const titlesMap: Record<string, string> = {}
  const titlesByLocaleId: Record<string, string> = {}
  for (const t of titles) {
    titlesMap[t.localeCode] = t.title
    titlesByLocaleId[t.localeId] = t.title
  }

  return {
    ...category,
    titles: titlesMap,
    titlesByLocaleId,
  }
})
