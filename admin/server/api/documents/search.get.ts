/**
 * 文档搜索 API
 * GET /api/documents/search
 * 
 * Requirements: 9.3
 * 搜索文档标题、内容和元数据
 */
import { asc, desc, eq, and, like, or, sql } from 'drizzle-orm'
import { documents, users, categories, locales, categoryTitles } from '@shared/schema'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const query = getQuery(event)

  // 搜索关键词（必填）
  const q = (query.q as string)?.trim()

  if (!q) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '搜索关键词不能为空',
    })
  }

  // 分页参数
  const page = Math.max(1, parseInt(query.page as string) || 1)
  const limit = Math.min(50, Math.max(1, parseInt(query.limit as string) || 10))
  const offset = (page - 1) * limit

  // 筛选参数
  const categoryId = query.categoryId as string | undefined
  const localeId = query.localeId as string | undefined
  const status = query.status as string | undefined

  // 排序参数
  const sortBy = (query.sortBy as string) || 'relevance'
  const sortOrder = (query.sortOrder as string) === 'asc' ? 'asc' : 'desc'

  // 构建搜索模式
  const searchPattern = `%${q}%`

  // 构建查询条件
  const searchCondition = or(
    like(documents.title, searchPattern),
    like(documents.slug, searchPattern),
    like(documents.content, searchPattern)
  )

  const filterConditions = []

  if (categoryId) {
    filterConditions.push(eq(documents.categoryId, categoryId))
  }

  if (localeId) {
    filterConditions.push(eq(documents.localeId, localeId))
  }

  if (status && ['draft', 'published', 'archived'].includes(status)) {
    filterConditions.push(eq(documents.status, status as 'draft' | 'published' | 'archived'))
  }

  // 组合所有条件
  const whereClause = filterConditions.length > 0
    ? and(searchCondition, ...filterConditions)
    : searchCondition

  // 获取总数
  const [{ count }] = await db
    .select({ count: sql<number>`count(*)::int` })
    .from(documents)
    .where(whereClause)

  // 构建排序
  // 相关性排序：标题匹配优先，然后是更新时间
  let orderByClause
  if (sortBy === 'relevance') {
    // 使用 CASE 表达式实现相关性排序
    // 标题完全匹配 > 标题包含 > 内容包含
    orderByClause = sql`
      CASE 
        WHEN ${documents.title} ILIKE ${q} THEN 1
        WHEN ${documents.title} ILIKE ${searchPattern} THEN 2
        WHEN ${documents.slug} ILIKE ${searchPattern} THEN 3
        ELSE 4
      END,
      ${documents.updatedAt} DESC
    `
  } else {
    const sortColumn = sortBy === 'title' ? documents.title
      : sortBy === 'createdAt' ? documents.createdAt
      : documents.updatedAt

    const orderFn = sortOrder === 'asc' ? asc : desc
    orderByClause = orderFn(sortColumn)
  }

  // 获取搜索结果
  const results = await db
    .select({
      id: documents.id,
      categoryId: documents.categoryId,
      authorId: documents.authorId,
      localeId: documents.localeId,
      title: documents.title,
      slug: documents.slug,
      content: documents.content,
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
    .orderBy(orderByClause)
    .limit(limit)
    .offset(offset)

  // 获取栏目信息
  const categoryIds = [...new Set(results.filter(d => d.categoryId).map(d => d.categoryId!))]
  let categoryMap = new Map<string, { slug: string; titles: Record<string, string> }>()

  if (categoryIds.length > 0) {
    const cats = await db
      .select({
        id: categories.id,
        slug: categories.slug,
      })
      .from(categories)
      .where(sql`${categories.id} IN ${categoryIds}`)

    const catTitles = await db
      .select({
        categoryId: categoryTitles.categoryId,
        localeCode: locales.code,
        title: categoryTitles.title,
      })
      .from(categoryTitles)
      .innerJoin(locales, eq(categoryTitles.localeId, locales.id))
      .where(sql`${categoryTitles.categoryId} IN ${categoryIds}`)

    const titlesByCategory = new Map<string, Record<string, string>>()
    for (const t of catTitles) {
      if (!titlesByCategory.has(t.categoryId)) {
        titlesByCategory.set(t.categoryId, {})
      }
      titlesByCategory.get(t.categoryId)![t.localeCode] = t.title
    }

    for (const cat of cats) {
      categoryMap.set(cat.id, {
        slug: cat.slug,
        titles: titlesByCategory.get(cat.id) || {},
      })
    }
  }

  // 生成搜索结果摘要（高亮匹配内容）
  const generateHighlight = (content: string, keyword: string, maxLength: number = 150): string => {
    const lowerContent = content.toLowerCase()
    const lowerKeyword = keyword.toLowerCase()
    const index = lowerContent.indexOf(lowerKeyword)

    if (index === -1) {
      // 没有匹配，返回开头内容
      return content.substring(0, maxLength) + (content.length > maxLength ? '...' : '')
    }

    // 计算摘要范围
    const start = Math.max(0, index - 50)
    const end = Math.min(content.length, index + keyword.length + 100)

    let highlight = ''
    if (start > 0) highlight += '...'
    highlight += content.substring(start, end)
    if (end < content.length) highlight += '...'

    return highlight
  }

  // 组装返回数据
  const items = results.map(doc => ({
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
    // 搜索相关
    highlight: generateHighlight(doc.content, q),
    matchedIn: {
      title: doc.title.toLowerCase().includes(q.toLowerCase()),
      slug: doc.slug.toLowerCase().includes(q.toLowerCase()),
      content: doc.content.toLowerCase().includes(q.toLowerCase()),
    },
    // 关联数据
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
    query: q,
    items,
    pagination: {
      page,
      limit,
      total: count,
      totalPages: Math.ceil(count / limit),
    },
  }
})
