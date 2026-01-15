/**
 * 获取内容树 API
 * GET /api/content/tree
 * 
 * 返回完整的内容树结构（栏目 + 文档）
 */
import { asc, eq } from 'drizzle-orm'
import { categories, categoryTitles, documents, locales } from '@shared/schema'

// 内容节点类型
interface ContentNode {
  id: string
  type: 'category' | 'document'
  name: string
  slug: string
  parentId: string | null
  sortOrder: number
  titles?: Record<string, string>
  status?: 'draft' | 'published' | 'archived'
  localeCode?: string
  children: ContentNode[]
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

  // 获取所有文档（按栏目分组）
  const allDocuments = await db
    .select({
      id: documents.id,
      title: documents.title,
      slug: documents.slug,
      status: documents.status,
      categoryId: documents.categoryId,
      localeCode: locales.code,
      createdAt: documents.createdAt,
    })
    .from(documents)
    .leftJoin(locales, eq(documents.localeId, locales.id))
    .orderBy(asc(documents.createdAt))

  // 构建标题映射 { categoryId: { localeCode: title } }
  const titlesMap = new Map<string, Record<string, string>>()
  for (const t of allTitles) {
    if (!titlesMap.has(t.categoryId)) {
      titlesMap.set(t.categoryId, {})
    }
    titlesMap.get(t.categoryId)![t.localeCode] = t.title
  }

  // 构建文档映射 { categoryId: documents[] }
  const documentsMap = new Map<string, ContentNode[]>()
  for (const doc of allDocuments) {
    if (!doc.categoryId) continue
    
    if (!documentsMap.has(doc.categoryId)) {
      documentsMap.set(doc.categoryId, [])
    }
    
    documentsMap.get(doc.categoryId)!.push({
      id: doc.id,
      type: 'document',
      name: doc.title,
      slug: doc.slug,
      parentId: doc.categoryId,
      sortOrder: 0,
      status: doc.status,
      localeCode: doc.localeCode || undefined,
      children: [],
    })
  }

  // 构建栏目映射
  const categoryMap = new Map<string, ContentNode>()
  for (const cat of allCategories) {
    const titles = titlesMap.get(cat.id) || {}
    const docs = documentsMap.get(cat.id) || []
    
    categoryMap.set(cat.id, {
      id: cat.id,
      type: 'category',
      name: titles.zh || cat.slug,
      slug: cat.slug,
      parentId: cat.parentId,
      sortOrder: cat.sortOrder,
      titles,
      children: [...docs], // 先添加文档
    })
  }

  // 构建树结构
  const rootCategories: ContentNode[] = []
  for (const cat of allCategories) {
    const node = categoryMap.get(cat.id)!
    if (cat.parentId && categoryMap.has(cat.parentId)) {
      // 子栏目添加到父栏目的 children 开头（栏目在文档前面）
      const parent = categoryMap.get(cat.parentId)!
      const docStartIndex = parent.children.findIndex(c => c.type === 'document')
      if (docStartIndex === -1) {
        parent.children.push(node)
      } else {
        parent.children.splice(docStartIndex, 0, node)
      }
    } else {
      rootCategories.push(node)
    }
  }

  return rootCategories
})
