/**
 * 获取导航菜单树 API
 * GET /api/nav-menus
 * 
 * Requirements: 5.1
 * 返回完整的导航菜单树结构，包含多语言标题
 */
import { asc, eq } from 'drizzle-orm'
import { navMenus, navMenuTitles, locales } from '@shared/schema'

// 导航菜单树节点类型
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
  titles: Record<string, string> // { localeCode: title }
  children: NavMenuNode[]
}

export default defineEventHandler(async () => {
  const db = useDb()

  // 获取所有导航菜单
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

  // 构建标题映射 { navMenuId: { localeCode: title } }
  const titlesMap = new Map<string, Record<string, string>>()
  for (const t of allTitles) {
    if (!titlesMap.has(t.navMenuId)) {
      titlesMap.set(t.navMenuId, {})
    }
    titlesMap.get(t.navMenuId)![t.localeCode] = t.title
  }

  // 构建菜单映射
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
