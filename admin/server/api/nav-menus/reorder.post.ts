/**
 * 重新排序导航菜单 API
 * POST /api/nav-menus/reorder
 * 
 * Requirements: 5.1
 * 支持拖拽排序和移动菜单到新的父菜单
 */
import { z } from 'zod'
import { navMenus, navMenuTitles, locales } from '@shared/schema'
import { eq, inArray, asc } from 'drizzle-orm'

// 单个菜单的排序信息
const menuOrderSchema = z.object({
  id: z.string(),
  parentId: z.string().nullable(),
  sortOrder: z.number().int().min(0),
})

// 请求体验证 Schema
const reorderSchema = z.object({
  items: z.array(menuOrderSchema).min(1),
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
  const existingMenus = await db
    .select({ id: navMenus.id })
    .from(navMenus)
    .where(inArray(navMenus.id, ids))

  if (existingMenus.length !== ids.length) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '部分菜单 ID 不存在',
    })
  }

  // 验证所有 parentId 都有效（如果不为 null）
  const parentIds = items
    .map(item => item.parentId)
    .filter((id): id is string => id !== null)

  if (parentIds.length > 0) {
    const existingParents = await db
      .select({ id: navMenus.id, type: navMenus.type })
      .from(navMenus)
      .where(inArray(navMenus.id, parentIds))

    const existingParentMap = new Map(existingParents.map(p => [p.id, p]))
    
    for (const parentId of parentIds) {
      const parent = existingParentMap.get(parentId)
      if (!parent) {
        throw createError({
          statusCode: 400,
          statusMessage: 'Bad Request',
          message: `父菜单 ${parentId} 不存在`,
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
  }

  // 检查是否会造成循环引用
  for (const item of items) {
    if (item.parentId) {
      const isDescendant = await checkIsDescendant(db, item.parentId, item.id, items)
      if (isDescendant) {
        throw createError({
          statusCode: 400,
          statusMessage: 'Bad Request',
          message: `菜单 ${item.id} 不能移动到自己的子菜单下`,
        })
      }
    }
  }

  // 批量更新菜单
  const updatePromises = items.map(item =>
    db
      .update(navMenus)
      .set({
        parentId: item.parentId,
        sortOrder: item.sortOrder,
        updatedAt: new Date(),
      })
      .where(eq(navMenus.id, item.id))
  )

  await Promise.all(updatePromises)

  // 返回更新后的菜单树
  const allMenus = await db
    .select()
    .from(navMenus)
    .orderBy(asc(navMenus.sortOrder))

  // 获取所有菜单标题
  const allTitles = await db
    .select({
      navMenuId: navMenuTitles.navMenuId,
      localeCode: locales.code,
      title: navMenuTitles.title,
    })
    .from(navMenuTitles)
    .innerJoin(locales, eq(navMenuTitles.localeId, locales.id))

  // 构建标题映射
  const titlesMap = new Map<string, Record<string, string>>()
  for (const t of allTitles) {
    if (!titlesMap.has(t.navMenuId)) {
      titlesMap.set(t.navMenuId, {})
    }
    titlesMap.get(t.navMenuId)![t.localeCode] = t.title
  }

  // 构建菜单映射
  interface NavMenuNode {
    id: string
    parentId: string | null
    type: 'link' | 'dropdown' | 'divider'
    targetType: 'category' | 'document' | 'external' | 'none'
    targetId: string | null
    externalUrl: string | null
    openInNewTab: boolean
    icon: string | null
    sortOrder: number
    isVisible: boolean
    createdAt: Date
    updatedAt: Date
    titles: Record<string, string>
    children: NavMenuNode[]
  }

  const menuMap = new Map<string, NavMenuNode>()
  for (const menu of allMenus) {
    menuMap.set(menu.id, {
      id: menu.id,
      parentId: menu.parentId,
      type: menu.type,
      targetType: menu.targetType,
      targetId: menu.targetId,
      externalUrl: menu.externalUrl,
      openInNewTab: menu.openInNewTab,
      icon: menu.icon,
      sortOrder: menu.sortOrder,
      isVisible: menu.isVisible,
      createdAt: menu.createdAt,
      updatedAt: menu.updatedAt,
      titles: titlesMap.get(menu.id) || {},
      children: [],
    })
  }

  // 构建树结构
  const rootMenus: NavMenuNode[] = []
  for (const menu of allMenus) {
    const node = menuMap.get(menu.id)!
    if (menu.parentId && menuMap.has(menu.parentId)) {
      menuMap.get(menu.parentId)!.children.push(node)
    } else {
      rootMenus.push(node)
    }
  }

  return rootMenus
})

/**
 * 检查 targetId 是否是 menuId 的后代
 * 考虑待更新的 items 中的新父子关系
 */
async function checkIsDescendant(
  db: ReturnType<typeof useDb>,
  targetId: string,
  menuId: string,
  items: Array<{ id: string; parentId: string | null }>
): Promise<boolean> {
  // 构建新的父子关系映射
  const newParentMap = new Map(items.map(item => [item.id, item.parentId]))

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

    // 优先使用新的父子关系
    if (newParentMap.has(currentId)) {
      currentId = newParentMap.get(currentId) || null
    } else {
      // 从数据库获取当前父菜单
      const [parent] = await db
        .select({ parentId: navMenus.parentId })
        .from(navMenus)
        .where(eq(navMenus.id, currentId))
        .limit(1)

      currentId = parent?.parentId || null
    }
  }

  return false
}
