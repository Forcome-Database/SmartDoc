/**
 * 创建导航菜单项 API
 * POST /api/nav-menus
 * 
 * Requirements: 5.1
 * 创建新的导航菜单项，支持链接/下拉菜单/分割线类型
 */
import { z } from 'zod'
import { navMenus, navMenuTitles, locales, categories, documents } from '@shared/schema'
import { eq, max, isNull } from 'drizzle-orm'

// 请求体验证 Schema
const createNavMenuSchema = z.object({
  parentId: z.string().nullable().optional(),
  type: z.enum(['link', 'dropdown', 'divider']).default('link'),
  targetType: z.enum(['category', 'document', 'external', 'none']).default('none'),
  targetId: z.string().nullable().optional(),
  externalUrl: z.string().url().nullable().optional(),
  openInNewTab: z.boolean().default(false),
  icon: z.string().nullable().optional(),
  isVisible: z.boolean().default(true),
  titles: z.record(z.string(), z.string().min(1).max(200)).optional(), // { localeCode: title }
})

export default defineEventHandler(async (event) => {
  const db = useDb()

  // 验证请求体
  const body = await readBody(event)
  const parsed = createNavMenuSchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: parsed.error.errors.map(e => e.message).join(', '),
    })
  }

  const { parentId, type, targetType, targetId, externalUrl, openInNewTab, icon, isVisible, titles } = parsed.data

  // 如果有父菜单，验证父菜单存在且类型为 dropdown
  if (parentId) {
    const [parent] = await db
      .select({ id: navMenus.id, type: navMenus.type })
      .from(navMenus)
      .where(eq(navMenus.id, parentId))
      .limit(1)

    if (!parent) {
      throw createError({
        statusCode: 400,
        statusMessage: 'Bad Request',
        message: '父菜单不存在',
      })
    }

    if (parent.type !== 'dropdown') {
      throw createError({
        statusCode: 400,
        statusMessage: 'Bad Request',
        message: '只能在下拉菜单下添加子菜单',
      })
    }
  }

  // 验证目标类型和目标 ID 的一致性
  if (targetType === 'category' && targetId) {
    const [category] = await db
      .select({ id: categories.id })
      .from(categories)
      .where(eq(categories.id, targetId))
      .limit(1)

    if (!category) {
      throw createError({
        statusCode: 400,
        statusMessage: 'Bad Request',
        message: '目标栏目不存在',
      })
    }
  }

  if (targetType === 'document' && targetId) {
    const [document] = await db
      .select({ id: documents.id })
      .from(documents)
      .where(eq(documents.id, targetId))
      .limit(1)

    if (!document) {
      throw createError({
        statusCode: 400,
        statusMessage: 'Bad Request',
        message: '目标文档不存在',
      })
    }
  }

  if (targetType === 'external' && !externalUrl) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '外部链接类型需要提供 URL',
    })
  }

  // 分割线类型不需要标题
  if (type !== 'divider' && (!titles || Object.keys(titles).length === 0)) {
    // 获取所有启用的语言
    const enabledLocales = await db
      .select()
      .from(locales)
      .where(eq(locales.isEnabled, true))

    if (enabledLocales.length > 0) {
      throw createError({
        statusCode: 400,
        statusMessage: 'Bad Request',
        message: '非分割线类型需要提供标题',
      })
    }
  }

  // 获取同级菜单的最大 sortOrder
  const maxOrderResult = await db
    .select({ maxOrder: max(navMenus.sortOrder) })
    .from(navMenus)
    .where(
      parentId ? eq(navMenus.parentId, parentId) : isNull(navMenus.parentId)
    )

  const nextOrder = (maxOrderResult[0]?.maxOrder ?? -1) + 1

  // 创建菜单项
  const [newMenu] = await db
    .insert(navMenus)
    .values({
      parentId: parentId || null,
      type,
      targetType,
      targetId: targetId || null,
      externalUrl: externalUrl || null,
      openInNewTab,
      icon: icon || null,
      sortOrder: nextOrder,
      isVisible,
    })
    .returning()

  // 创建多语言标题（分割线类型除外）
  if (type !== 'divider' && titles && Object.keys(titles).length > 0) {
    const allLocales = await db.select().from(locales)
    const localeMap = new Map(allLocales.map(l => [l.code, l.id]))

    const titleInserts = Object.entries(titles)
      .filter(([code]) => localeMap.has(code))
      .map(([code, title]) => ({
        navMenuId: newMenu.id,
        localeId: localeMap.get(code)!,
        title,
      }))

    if (titleInserts.length > 0) {
      await db.insert(navMenuTitles).values(titleInserts)
    }
  }

  // 获取创建的标题
  const createdTitles = await db
    .select({
      localeCode: locales.code,
      title: navMenuTitles.title,
    })
    .from(navMenuTitles)
    .innerJoin(locales, eq(navMenuTitles.localeId, locales.id))
    .where(eq(navMenuTitles.navMenuId, newMenu.id))

  const titlesMap: Record<string, string> = {}
  for (const t of createdTitles) {
    titlesMap[t.localeCode] = t.title
  }

  return {
    ...newMenu,
    titles: titlesMap,
    children: [],
  }
})
