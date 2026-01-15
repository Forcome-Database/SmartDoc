/**
 * 重新排序栏目 API
 * POST /api/categories/reorder
 * 
 * Requirements: 2.4
 * 支持拖拽排序和移动栏目到新的父栏目
 */
import { z } from 'zod'
import { categories, categoryTitles, locales } from '@shared/schema'
import { eq, inArray, asc, isNull, and, ne } from 'drizzle-orm'

// 单个栏目的排序信息
const categoryOrderSchema = z.object({
  id: z.string(),
  parentId: z.string().nullable(),
  sortOrder: z.number().int().min(0),
})

// 请求体验证 Schema
const reorderSchema = z.object({
  // 栏目排序信息数组
  items: z.array(categoryOrderSchema).min(1),
})

export default defineEventHandler(async (event) => {
  const db = useDb()

  // 验证请求体
  const body = await readBody(event)
  const parsed = reorderSchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: parsed.error.errors.map(e => e.message).join(', '),
    })
  }

  const { items } = parsed.data
  const ids = items.map(item => item.id)

  // 验证所有 ID 都存在
  const existingCategories = await db
    .select({ id: categories.id })
    .from(categories)
    .where(inArray(categories.id, ids))

  if (existingCategories.length !== ids.length) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '部分栏目 ID 不存在',
    })
  }

  // 验证所有 parentId 都有效（如果不为 null）
  const parentIds = items
    .map(item => item.parentId)
    .filter((id): id is string => id !== null)

  if (parentIds.length > 0) {
    const existingParents = await db
      .select({ id: categories.id })
      .from(categories)
      .where(inArray(categories.id, parentIds))

    const existingParentIds = new Set(existingParents.map(p => p.id))
    const invalidParents = parentIds.filter(id => !existingParentIds.has(id))

    if (invalidParents.length > 0) {
      throw createError({
        statusCode: 400,
        statusMessage: 'Bad Request',
        message: '部分父栏目 ID 不存在',
      })
    }
  }

  // 检查是否会造成循环引用
  for (const item of items) {
    if (item.parentId) {
      // 检查 parentId 是否是 item.id 的后代
      const isDescendant = await checkIsDescendant(db, item.parentId, item.id, items)
      if (isDescendant) {
        throw createError({
          statusCode: 400,
          statusMessage: 'Bad Request',
          message: `栏目 ${item.id} 不能移动到自己的子栏目下`,
        })
      }
    }
  }

  // 检查同级下 slug 是否重复
  const categoryDetails = await db
    .select({ id: categories.id, slug: categories.slug })
    .from(categories)
    .where(inArray(categories.id, ids))

  const slugMap = new Map(categoryDetails.map(c => [c.id, c.slug]))

  // 按 parentId 分组检查 slug 重复
  const parentGroups = new Map<string | null, string[]>()
  for (const item of items) {
    const key = item.parentId
    if (!parentGroups.has(key)) {
      parentGroups.set(key, [])
    }
    parentGroups.get(key)!.push(item.id)
  }

  for (const [parentId, groupIds] of parentGroups) {
    const slugs = groupIds.map(id => slugMap.get(id)!)
    const uniqueSlugs = new Set(slugs)
    if (slugs.length !== uniqueSlugs.size) {
      throw createError({
        statusCode: 409,
        statusMessage: 'Conflict',
        message: '同级栏目下存在重复的 slug',
      })
    }

    // 检查与现有同级栏目的 slug 冲突
    const existingSiblings = await db
      .select({ id: categories.id, slug: categories.slug })
      .from(categories)
      .where(
        and(
          parentId ? eq(categories.parentId, parentId) : isNull(categories.parentId),
          // 排除当前正在移动的栏目
          ...groupIds.map(id => ne(categories.id, id))
        )
      )

    for (const sibling of existingSiblings) {
      if (uniqueSlugs.has(sibling.slug)) {
        throw createError({
          statusCode: 409,
          statusMessage: 'Conflict',
          message: `同级栏目下已存在 slug "${sibling.slug}"`,
        })
      }
    }
  }

  // 批量更新栏目
  const updatePromises = items.map(item =>
    db
      .update(categories)
      .set({
        parentId: item.parentId,
        sortOrder: item.sortOrder,
      })
      .where(eq(categories.id, item.id))
  )

  await Promise.all(updatePromises)

  // 返回更新后的栏目树
  const allCategories = await db
    .select()
    .from(categories)
    .orderBy(asc(categories.sortOrder))

  // 获取所有栏目标题
  const allTitles = await db
    .select({
      categoryId: categoryTitles.categoryId,
      localeCode: locales.code,
      title: categoryTitles.title,
    })
    .from(categoryTitles)
    .innerJoin(locales, eq(categoryTitles.localeId, locales.id))

  // 构建标题映射
  const titlesMap = new Map<string, Record<string, string>>()
  for (const t of allTitles) {
    if (!titlesMap.has(t.categoryId)) {
      titlesMap.set(t.categoryId, {})
    }
    titlesMap.get(t.categoryId)![t.localeCode] = t.title
  }

  // 构建栏目映射
  interface CategoryNode {
    id: string
    slug: string
    parentId: string | null
    sortOrder: number
    createdAt: Date
    titles: Record<string, string>
    children: CategoryNode[]
  }

  const categoryMap = new Map<string, CategoryNode>()
  for (const cat of allCategories) {
    categoryMap.set(cat.id, {
      id: cat.id,
      slug: cat.slug,
      parentId: cat.parentId,
      sortOrder: cat.sortOrder,
      createdAt: cat.createdAt,
      titles: titlesMap.get(cat.id) || {},
      children: [],
    })
  }

  // 构建树结构
  const rootCategories: CategoryNode[] = []
  for (const cat of allCategories) {
    const node = categoryMap.get(cat.id)!
    if (cat.parentId && categoryMap.has(cat.parentId)) {
      categoryMap.get(cat.parentId)!.children.push(node)
    } else {
      rootCategories.push(node)
    }
  }

  return rootCategories
})

/**
 * 检查 targetId 是否是 categoryId 的后代
 * 考虑待更新的 items 中的新父子关系
 */
async function checkIsDescendant(
  db: ReturnType<typeof useDb>,
  targetId: string,
  categoryId: string,
  items: Array<{ id: string; parentId: string | null }>
): Promise<boolean> {
  // 构建新的父子关系映射
  const newParentMap = new Map(items.map(item => [item.id, item.parentId]))

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

    // 优先使用新的父子关系
    if (newParentMap.has(currentId)) {
      currentId = newParentMap.get(currentId) || null
    } else {
      // 从数据库获取当前父栏目
      const [parent] = await db
        .select({ parentId: categories.parentId })
        .from(categories)
        .where(eq(categories.id, currentId))
        .limit(1)

      currentId = parent?.parentId || null
    }
  }

  return false
}
