/**
 * 更新导航菜单项 API
 * PATCH /api/nav-menus/:id
 * 
 * Requirements: 5.1
 * 更新菜单项信息，包括类型、目标和多语言标题
 */
import { z } from 'zod'
import { navMenus, navMenuTitles, locales, categories, documents } from '@shared/schema'
import { eq, and, ne } from 'drizzle-orm'

// 请求体验证 Schema
const updateNavMenuSchema = z.object({
  parentId: z.string().nullable().optional(),
  type: z.enum(['link', 'dropdown', 'divider']).optional(),
  targetType: z.enum(['category', 'document', 'external', 'none']).optional(),
  targetId: z.string().nullable().optional(),
  externalUrl: z.string().url().nullable().optional(),
  openInNewTab: z.boolean().optional(),
  icon: z.string().nullable().optional(),
  isVisible: z.boolean().optional(),
  titles: z.record(z.string(), z.string().min(1).max(200)).optional(), // { localeCode: title }
})

export default defineEventHandler(async (event) => {
  const db = useDb()
  const id = getRouterParam(event, 'id')

  if (!id) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少菜单 ID',
    })
  }

  // 验证请求体
  const body = await readBody(event)
  const parsed = updateNavMenuSchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: parsed.error.errors.map(e => e.message).join(', '),
    })
  }

  const { parentId, type, targetType, targetId, externalUrl, openInNewTab, icon, isVisible, titles } = parsed.data

  // 检查菜单是否存在
  const [existing] = await db
    .select()
    .from(navMenus)
    .where(eq(navMenus.id, id))
    .limit(1)

  if (!existing) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '菜单项不存在',
    })
  }

  // 如果更新 parentId，验证新父菜单存在且不会造成循环引用
  if (parentId !== undefined && parentId !== existing.parentId) {
    if (parentId) {
      // 检查新父菜单是否存在
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

      // 检查是否会造成循环引用
      const isDescendant = await checkIsDescendant(db, parentId, id)
      if (isDescendant) {
        throw createError({
          statusCode: 400,
          statusMessage: 'Bad Request',
          message: '不能将菜单移动到自己的子菜单下',
        })
      }
    }
  }

  // 确定最终的目标类型
  const finalTargetType = targetType ?? existing.targetType

  // 验证目标类型和目标 ID 的一致性
  if (finalTargetType === 'category' && targetId) {
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

  if (finalTargetType === 'document' && targetId) {
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

  // 更新菜单基本信息
  const updateData: Partial<typeof navMenus.$inferInsert> = {
    updatedAt: new Date(),
  }
  if (parentId !== undefined) updateData.parentId = parentId
  if (type !== undefined) updateData.type = type
  if (targetType !== undefined) updateData.targetType = targetType
  if (targetId !== undefined) updateData.targetId = targetId
  if (externalUrl !== undefined) updateData.externalUrl = externalUrl
  if (openInNewTab !== undefined) updateData.openInNewTab = openInNewTab
  if (icon !== undefined) updateData.icon = icon
  if (isVisible !== undefined) updateData.isVisible = isVisible

  await db
    .update(navMenus)
    .set(updateData)
    .where(eq(navMenus.id, id))

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
        .from(navMenuTitles)
        .where(
          and(
            eq(navMenuTitles.navMenuId, id),
            eq(navMenuTitles.localeId, localeId)
          )
        )
        .limit(1)

      if (existingTitle) {
        // 更新标题
        await db
          .update(navMenuTitles)
          .set({ title })
          .where(eq(navMenuTitles.id, existingTitle.id))
      } else {
        // 创建标题
        await db
          .insert(navMenuTitles)
          .values({
            navMenuId: id,
            localeId,
            title,
          })
      }
    }
  }

  // 获取更新后的菜单
  const [updatedMenu] = await db
    .select()
    .from(navMenus)
    .where(eq(navMenus.id, id))

  // 获取更新后的标题
  const updatedTitles = await db
    .select({
      localeCode: locales.code,
      title: navMenuTitles.title,
    })
    .from(navMenuTitles)
    .innerJoin(locales, eq(navMenuTitles.localeId, locales.id))
    .where(eq(navMenuTitles.navMenuId, id))

  const titlesMap: Record<string, string> = {}
  for (const t of updatedTitles) {
    titlesMap[t.localeCode] = t.title
  }

  return {
    ...updatedMenu,
    titles: titlesMap,
  }
})

/**
 * 检查 targetId 是否是 menuId 的后代
 */
async function checkIsDescendant(
  db: ReturnType<typeof useDb>,
  targetId: string,
  menuId: string
): Promise<boolean> {
  let currentId: string | null = targetId
  const visited = new Set<string>()

  while (currentId) {
    if (currentId === menuId) {
      return true
    }
    if (visited.has(currentId)) {
      break // 防止无限循环
    }
    visited.add(currentId)

    const [parent] = await db
      .select({ parentId: navMenus.parentId })
      .from(navMenus)
      .where(eq(navMenus.id, currentId))
      .limit(1)

    currentId = parent?.parentId || null
  }

  return false
}
