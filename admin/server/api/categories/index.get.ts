/**
 * 获取栏目树 API
 * GET /api/categories
 * 
 * Requirements: 2.1, 2.7
 * 返回完整的栏目树结构，包含多语言标题
 */
import { asc, eq, isNull } from 'drizzle-orm'
import { categories, categoryTitles, locales } from '@shared/schema'

// 栏目树节点类型
interface CategoryNode {
  id: string
  slug: string
  parentId: string | null
  sortOrder: number
  createdAt: Date
  titles: Record<string, string> // { localeCode: title }
  children: CategoryNode[]
}

export default defineEventHandler(async () => {
  const db = useDb()

  // 获取所有栏目
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

  // 构建标题映射 { categoryId: { localeCode: title } }
  const titlesMap = new Map<string, Record<string, string>>()
  for (const t of allTitles) {
    if (!titlesMap.has(t.categoryId)) {
      titlesMap.set(t.categoryId, {})
    }
    titlesMap.get(t.categoryId)![t.localeCode] = t.title
  }

  // 构建栏目映射
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
