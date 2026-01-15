/**
 * 获取文档列表 API
 * GET /api/documents
 * 
 * Requirements: 3.1
 * 返回文档列表，支持分页和筛选
 */
import { asc, desc, eq, and, like, or, sql } from 'drizzle-orm'
import { documents, users, categories, locales, categoryTitles } from '@shared/schema'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const query = getQuery(event)

  // 分页参数
  const page = Math.max(1, parseInt(query.page as string) || 1)
  const limit = Math.min(100, Math.max(1, parseInt(query.limit as string) || 20))
  const offset = (page - 1) * limit

  // 筛选参数
  const categoryId = query.categoryId as string | undefined
  const localeId = query.localeId as string | undefined
  const status = query.status as string | undefined
  const authorId = query.authorId as string | undefined
  const search = query.search as string | undefined

  // 排序参数
  const sortBy = (query.sortBy as string) || 'updatedAt'
  const sortOrder = (query.sortOrder as string) === 'asc' ? 'asc' : 'desc'

  // 构建查询条件
  const conditions = []

  if (categoryId) {
    conditions.push(eq(documents.categoryId, categoryId))
  }

  if (localeId) {
    conditions.push(eq(documents.localeId, localeId))
  }

  if (status && ['draft', 'published', 'archived'].includes(status)) {
    conditions.push(eq(documents.status, status as 'draft' | 'published' | 'archived'))
  }

  if (authorId) {
    conditions.push(eq(documents.authorId, authorId))
  }

  if (search) {
    const searchPattern = `%${search}%`
    conditions.push(
      or(
        like(documents.title, searchPattern),
        like(documents.slug, searchPattern)
      )
    )
  }

  const whereClause = conditions.length > 0 ? and(...conditions) : undefined

  // 获取总数
  const [{ count }] = await db
    .select({ count: sql<number>`count(*)::int` })
    .from(documents)
    .where(whereClause)

  // 获取文档列表
  const sortColumn = sortBy === 'title' ? documents.title
    : sortBy === 'createdAt' ? documents.createdAt
    : documents.updatedAt

  const orderFn = sortOrder === 'asc' ? asc : desc

  const docList = await db
    .select({
      id: documents.id,
      categoryId: documents.categoryId,
      authorId: documents.authorId,
      localeId: documents.localeId,
      title: documents.title,
      slug: documents.slug,
      status: documents.status,
      publishedVersion: documents.publishedVersion,
      createdAt: documents.createdAt,
      updatedAt: documents.updatedAt,
      // 关联数据
      authorName: users.name,
      authorAvatar: users.avatar,
      localeCode: locales.code,
      localeName: locales.name,
    })
    .from(documents)
    .leftJoin(users, eq(documents.authorId, users.id))
    .leftJoin(locales, eq(documents.localeId, locales.id))
    .where(whereClause)
    .orderBy(orderFn(sortColumn))
    .limit(limit)
    .offset(offset)

  // 获取栏目信息（如果有 categoryId）
  const categoryIds = [...new Set(docList.filter(d => d.categoryId).map(d => d.categoryId!))]
  let categoryMap = new Map<string, { slug: string; titles: Record<string, string> }>()

  if (categoryIds.length > 0) {
    // 获取栏目基本信息
    const cats = await db
      .select({
        id: categories.id,
        slug: categories.slug,
      })
      .from(categories)
      .where(sql`${categories.id} IN ${categoryIds}`)

    // 获取栏目标题
    const catTitles = await db
      .select({
        categoryId: categoryTitles.categoryId,
        localeCode: locales.code,
        title: categoryTitles.title,
      })
      .from(categoryTitles)
      .innerJoin(locales, eq(categoryTitles.localeId, locales.id))
      .where(sql`${categoryTitles.categoryId} IN ${categoryIds}`)

    // 构建标题映射
    const titlesByCategory = new Map<string, Record<string, string>>()
    for (const t of catTitles) {
      if (!titlesByCategory.has(t.categoryId)) {
        titlesByCategory.set(t.categoryId, {})
      }
      titlesByCategory.get(t.categoryId)![t.localeCode] = t.title
    }

    // 构建栏目映射
    for (const cat of cats) {
      categoryMap.set(cat.id, {
        slug: cat.slug,
        titles: titlesByCategory.get(cat.id) || {},
      })
    }
  }

  // 组装返回数据
  const items = docList.map(doc => ({
    id: doc.id,
    categoryId: doc.categoryId,
    authorId: doc.authorId,
    localeId: doc.localeId,
    title: doc.title,
    slug: doc.slug,
    status: doc.status,
    publishedVersion: doc.publishedVersion,
    createdAt: doc.createdAt,
    updatedAt: doc.updatedAt,
    author: doc.authorId ? {
      id: doc.authorId,
      name: doc.authorName,
      avatar: doc.authorAvatar,
    } : null,
    locale: doc.localeId ? {
      id: doc.localeId,
      code: doc.localeCode,
      name: doc.localeName,
    } : null,
    category: doc.categoryId && categoryMap.has(doc.categoryId) ? {
      id: doc.categoryId,
      ...categoryMap.get(doc.categoryId),
    } : null,
  }))

  return {
    items,
    pagination: {
      page,
      limit,
      total: count,
      totalPages: Math.ceil(count / limit),
    },
  }
})
