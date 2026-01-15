/**
 * 更新栏目 API
 * PATCH /api/categories/:id
 * 
 * Requirements: 2.2
 * 更新栏目信息，包括 slug 和多语言标题
 */
import { z } from 'zod'
import { categories, categoryTitles, locales } from '@shared/schema'
import { eq, and, ne, isNull } from 'drizzle-orm'

// 请求体验证 Schema
const updateCategorySchema = z.object({
  slug: z.string().min(1).max(100).regex(/^[a-z0-9-]+$/, {
    message: 'slug 只能包含小写字母、数字和连字符',
  }).optional(),
  parentId: z.string().nullable().optional(),
  titles: z.record(z.string(), z.string().min(1).max(200)).optional(), // { localeCode: title }
})

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

  // 验证请求体
  const body = await readBody(event)
  const parsed = updateCategorySchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: parsed.error.errors.map(e => e.message).join(', '),
    })
  }

  const { slug, parentId, titles } = parsed.data

  // 检查栏目是否存在
  const [existing] = await db
    .select()
    .from(categories)
    .where(eq(categories.id, id))
    .limit(1)

  if (!existing) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '栏目不存在',
    })
  }

  // 确定目标父栏目 ID
  const targetParentId = parentId !== undefined ? parentId : existing.parentId

  // 如果更新 parentId，验证新父栏目存在且不会造成循环引用
  if (parentId !== undefined && parentId !== existing.parentId) {
    if (parentId) {
      // 检查新父栏目是否存在
      const [parent] = await db
        .select({ id: categories.id })
        .from(categories)
        .where(eq(categories.id, parentId))
        .limit(1)

      if (!parent) {
        throw createError({
          statusCode: 400,
          statusMessage: 'Bad Request',
          message: '父栏目不存在',
        })
      }

      // 检查是否会造成循环引用（不能将栏目移动到自己的子栏目下）
      const isDescendant = await checkIsDescendant(db, parentId, id)
      if (isDescendant) {
        throw createError({
          statusCode: 400,
          statusMessage: 'Bad Request',
          message: '不能将栏目移动到自己的子栏目下',
        })
      }
    }
  }

  // 如果更新 slug，检查同级下是否重复
  if (slug && slug !== existing.slug) {
    const existingSlug = await db
      .select({ id: categories.id })
      .from(categories)
      .where(
        and(
          eq(categories.slug, slug),
          targetParentId ? eq(categories.parentId, targetParentId) : isNull(categories.parentId),
          ne(categories.id, id)
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
  }

  // 更新栏目基本信息
  const updateData: Partial<typeof categories.$inferInsert> = {}
  if (slug !== undefined) updateData.slug = slug
  if (parentId !== undefined) updateData.parentId = parentId

  if (Object.keys(updateData).length > 0) {
    await db
      .update(categories)
      .set(updateData)
      .where(eq(categories.id, id))
  }

  // 更新多语言标题
  if (titles && Object.keys(titles).length > 0) {
    // 获取语言映射
    const allLocales = await db.select().from(locales)
    const localeMap = new Map(allLocales.map(l => [l.code, l.id]))

    for (const [localeCode, title] of Object.entries(titles)) {
      const localeId = localeMap.get(localeCode)
      if (!localeId) continue

      // 检查标题是否存在
      const [existingTitle] = await db
        .select()
        .from(categoryTitles)
        .where(
          and(
            eq(categoryTitles.categoryId, id),
            eq(categoryTitles.localeId, localeId)
          )
        )
        .limit(1)

      if (existingTitle) {
        // 更新标题
        await db
          .update(categoryTitles)
          .set({ title })
          .where(eq(categoryTitles.id, existingTitle.id))
      } else {
        // 创建标题
        await db
          .insert(categoryTitles)
          .values({
            categoryId: id,
            localeId,
            title,
          })
      }
    }
  }

  // 获取更新后的栏目
  const [updatedCategory] = await db
    .select()
    .from(categories)
    .where(eq(categories.id, id))

  // 获取更新后的标题
  const updatedTitles = await db
    .select({
      localeCode: locales.code,
      title: categoryTitles.title,
    })
    .from(categoryTitles)
    .innerJoin(locales, eq(categoryTitles.localeId, locales.id))
    .where(eq(categoryTitles.categoryId, id))

  const titlesMap: Record<string, string> = {}
  for (const t of updatedTitles) {
    titlesMap[t.localeCode] = t.title
  }

  return {
    ...updatedCategory,
    titles: titlesMap,
  }
})

/**
 * 检查 targetId 是否是 categoryId 的后代
 */
async function checkIsDescendant(
  db: ReturnType<typeof useDb>,
  targetId: string,
  categoryId: string
): Promise<boolean> {
  // 获取 targetId 的所有祖先
  let currentId: string | null = targetId
  const visited = new Set<string>()

  while (currentId) {
    if (currentId === categoryId) {
      return true
    }
    if (visited.has(currentId)) {
      break // 防止无限循环
    }
    visited.add(currentId)

    const [parent] = await db
      .select({ parentId: categories.parentId })
      .from(categories)
      .where(eq(categories.id, currentId))
      .limit(1)

    currentId = parent?.parentId || null
  }

  return false
}
