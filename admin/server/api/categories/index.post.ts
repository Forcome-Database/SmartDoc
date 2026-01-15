/**
 * 创建栏目 API
 * POST /api/categories
 * 
 * Requirements: 2.1, 2.6
 * 创建新栏目，需要提供所有启用语言的标题
 */
import { z } from 'zod'
import { categories, categoryTitles, locales } from '@shared/schema'
import { eq, max, and, isNull } from 'drizzle-orm'

// 请求体验证 Schema
const createCategorySchema = z.object({
  slug: z.string().min(1).max(100).regex(/^[a-z0-9-]+$/, {
    message: 'slug 只能包含小写字母、数字和连字符',
  }),
  parentId: z.string().nullable().optional(),
  titles: z.record(z.string(), z.string().min(1).max(200)), // { localeCode: title }
})

export default defineEventHandler(async (event) => {
  const db = useDb()

  // 验证请求体
  const body = await readBody(event)
  const parsed = createCategorySchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: parsed.error.errors.map(e => e.message).join(', '),
    })
  }

  const { slug, parentId, titles } = parsed.data

  // 如果有父栏目，验证父栏目存在
  if (parentId) {
    const parent = await db
      .select({ id: categories.id })
      .from(categories)
      .where(eq(categories.id, parentId))
      .limit(1)

    if (parent.length === 0) {
      throw createError({
        statusCode: 400,
        statusMessage: 'Bad Request',
        message: '父栏目不存在',
      })
    }
  }

  // 检查同级下 slug 是否重复
  const existingSlug = await db
    .select({ id: categories.id })
    .from(categories)
    .where(
      and(
        eq(categories.slug, slug),
        parentId ? eq(categories.parentId, parentId) : isNull(categories.parentId)
      )
    )
    .limit(1)

  if (existingSlug.length > 0) {
    throw createError({
      statusCode: 409,
      statusMessage: 'Conflict',
      message: `同级栏目下已存在 slug "${slug}"`,
    })
  }

  // 获取所有启用的语言
  const enabledLocales = await db
    .select()
    .from(locales)
    .where(eq(locales.isEnabled, true))

  // 验证是否提供了所有启用语言的标题
  const missingLocales = enabledLocales.filter(l => !titles[l.code])
  if (missingLocales.length > 0) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: `缺少以下语言的标题: ${missingLocales.map(l => l.name).join(', ')}`,
    })
  }

  // 获取同级栏目的最大 sortOrder
  const maxOrderResult = await db
    .select({ maxOrder: max(categories.sortOrder) })
    .from(categories)
    .where(
      parentId ? eq(categories.parentId, parentId) : isNull(categories.parentId)
    )

  const nextOrder = (maxOrderResult[0]?.maxOrder ?? -1) + 1

  // 创建栏目
  const [newCategory] = await db
    .insert(categories)
    .values({
      slug,
      parentId: parentId || null,
      sortOrder: nextOrder,
    })
    .returning()

  // 创建多语言标题
  const titleInserts = enabledLocales
    .filter(l => titles[l.code])
    .map(l => ({
      categoryId: newCategory.id,
      localeId: l.id,
      title: titles[l.code],
    }))

  if (titleInserts.length > 0) {
    await db.insert(categoryTitles).values(titleInserts)
  }

  // 获取创建的标题
  const createdTitles = await db
    .select({
      localeCode: locales.code,
      title: categoryTitles.title,
    })
    .from(categoryTitles)
    .innerJoin(locales, eq(categoryTitles.localeId, locales.id))
    .where(eq(categoryTitles.categoryId, newCategory.id))

  const titlesMap: Record<string, string> = {}
  for (const t of createdTitles) {
    titlesMap[t.localeCode] = t.title
  }

  return {
    ...newCategory,
    titles: titlesMap,
    children: [],
  }
})
