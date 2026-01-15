/**
 * 发布导航菜单到 VitePress API
 * POST /api/nav-menus/publish
 * 
 * Requirements: 5.1, 5.2
 * 将数据库中的导航菜单配置生成为 VitePress 可用的 JSON 文件
 */
import { asc, eq } from 'drizzle-orm'
import { navMenus, navMenuTitles, locales, categories, documents } from '@shared/schema'
import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'

// VitePress 导航项类型
interface VitePressNavItem {
  text: string
  link?: string
  activeMatch?: string
  target?: string
  rel?: string
  items?: VitePressNavItem[]
}

// 导航菜单节点类型
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
  titles: Record<string, string>
  children: NavMenuNode[]
}

// 栏目类型
interface CategoryRecord {
  id: string
  parentId: string | null
  slug: string
  sortOrder: number
  createdAt: Date
}

export default defineEventHandler(async () => {
  const db = useDb()
  const config = useRuntimeConfig()

  // 获取所有启用的语言
  const enabledLocales = await db
    .select()
    .from(locales)
    .where(eq(locales.isEnabled, true))
    .orderBy(asc(locales.sortOrder))

  if (enabledLocales.length === 0) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '没有启用的语言',
    })
  }

  // 获取所有可见的导航菜单
  const allMenus = await db
    .select()
    .from(navMenus)
    .where(eq(navMenus.isVisible, true))
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

  // 获取所有栏目（用于生成链接）
  const allCategories = await db
    .select({
      id: categories.id,
      parentId: categories.parentId,
      slug: categories.slug,
    })
    .from(categories)

  // 构建栏目路径映射
  const categoryPathMap = buildCategoryPathMap(allCategories)

  // 获取所有文档（用于生成链接）
  const allDocuments = await db
    .select({
      id: documents.id,
      categoryId: documents.categoryId,
      slug: documents.slug,
      localeCode: locales.code,
    })
    .from(documents)
    .innerJoin(locales, eq(documents.localeId, locales.id))

  // 构建文档路径映射 { documentId: { localeCode: path } }
  const documentPathMap = new Map<string, Record<string, string>>()
  for (const doc of allDocuments) {
    if (!documentPathMap.has(doc.id)) {
      documentPathMap.set(doc.id, {})
    }
    const categoryPath = doc.categoryId ? categoryPathMap.get(doc.categoryId) || '' : ''
    documentPathMap.get(doc.id)![doc.localeCode] = `/${doc.localeCode}${categoryPath}/${doc.slug}`
  }

  // 构建菜单树
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
      titles: titlesMap.get(menu.id) || {},
      children: [],
    })
  }

  const rootMenus: NavMenuNode[] = []
  for (const menu of allMenus) {
    const node = menuMap.get(menu.id)!
    if (menu.parentId && menuMap.has(menu.parentId)) {
      menuMap.get(menu.parentId)!.children.push(node)
    } else {
      rootMenus.push(node)
    }
  }

  // 为每种语言生成导航配置
  const navConfigs: Record<string, VitePressNavItem[]> = {}

  for (const locale of enabledLocales) {
    navConfigs[locale.code] = convertToVitePressNav(
      rootMenus,
      locale.code,
      categoryPathMap,
      documentPathMap
    )
  }

  // 写入配置文件
  const docsRoot = config.docsRoot || '../docs'
  const outputPath = join(docsRoot, '.vitepress', 'nav-config.json')

  try {
    // 确保目录存在
    const outputDir = dirname(outputPath)
    if (!existsSync(outputDir)) {
      mkdirSync(outputDir, { recursive: true })
    }
    
    // 写入 JSON 文件
    writeFileSync(outputPath, JSON.stringify(navConfigs, null, 2), 'utf-8')
  } catch (error) {
    console.error('Failed to write nav config:', error)
    throw createError({
      statusCode: 500,
      statusMessage: 'Internal Server Error',
      message: '写入导航配置文件失败',
    })
  }

  return {
    success: true,
    message: '导航菜单已发布',
    outputPath,
    locales: enabledLocales.map(l => l.code),
    menuCount: rootMenus.length,
  }
})

/**
 * 构建栏目路径映射
 */
function buildCategoryPathMap(allCategories: Array<{ id: string; parentId: string | null; slug: string }>) {
  const pathMap = new Map<string, string>()
  const categoryMap = new Map(allCategories.map(c => [c.id, c]))

  function getPath(categoryId: string): string {
    if (pathMap.has(categoryId)) {
      return pathMap.get(categoryId)!
    }

    const category = categoryMap.get(categoryId)
    if (!category) return ''

    let categoryPath = ''
    if (category.parentId) {
      categoryPath = getPath(category.parentId)
    }
    categoryPath = `${categoryPath}/${category.slug}`
    pathMap.set(categoryId, categoryPath)
    return categoryPath
  }

  for (const category of allCategories) {
    getPath(category.id)
  }

  return pathMap
}

/**
 * 将菜单树转换为 VitePress 导航格式
 */
function convertToVitePressNav(
  menus: NavMenuNode[],
  localeCode: string,
  categoryPathMap: Map<string, string>,
  documentPathMap: Map<string, Record<string, string>>
): VitePressNavItem[] {
  const result: VitePressNavItem[] = []

  for (const menu of menus) {
    // 跳过分割线（VitePress 不支持导航分割线）
    if (menu.type === 'divider') {
      continue
    }

    const title = menu.titles[localeCode] || menu.titles['zh'] || menu.titles['en'] || ''
    if (!title) continue

    const navItem: VitePressNavItem = {
      text: title,
    }

    // 处理链接
    if (menu.type === 'link') {
      const link = getMenuLink(menu, localeCode, categoryPathMap, documentPathMap)
      if (link) {
        navItem.link = link
        // 设置 activeMatch
        if (menu.targetType === 'category' && menu.targetId) {
          const categoryPath = categoryPathMap.get(menu.targetId)
          if (categoryPath) {
            navItem.activeMatch = `^/${localeCode}${categoryPath}/`
          }
        }
      }
      if (menu.openInNewTab) {
        navItem.target = '_blank'
        navItem.rel = 'noopener noreferrer'
      }
    }

    // 处理下拉菜单
    if (menu.type === 'dropdown' && menu.children.length > 0) {
      navItem.items = convertToVitePressNav(
        menu.children,
        localeCode,
        categoryPathMap,
        documentPathMap
      )
      // 如果下拉菜单有 activeMatch 的子项，设置父级的 activeMatch
      const childMatches = menu.children
        .filter(c => c.targetType === 'category' && c.targetId)
        .map(c => categoryPathMap.get(c.targetId!))
        .filter(Boolean)
      if (childMatches.length > 0) {
        // 找到共同前缀作为 activeMatch
        const commonPrefix = findCommonPrefix(childMatches as string[])
        if (commonPrefix) {
          navItem.activeMatch = `^/${localeCode}${commonPrefix}`
        }
      }
    }

    result.push(navItem)
  }

  return result
}

/**
 * 获取菜单链接
 */
function getMenuLink(
  menu: NavMenuNode,
  localeCode: string,
  categoryPathMap: Map<string, string>,
  documentPathMap: Map<string, Record<string, string>>
): string | undefined {
  switch (menu.targetType) {
    case 'category':
      if (menu.targetId) {
        const categoryPath = categoryPathMap.get(menu.targetId)
        if (categoryPath) {
          return `/${localeCode}${categoryPath}/`
        }
      }
      break
    case 'document':
      if (menu.targetId) {
        const docPaths = documentPathMap.get(menu.targetId)
        if (docPaths && docPaths[localeCode]) {
          return docPaths[localeCode]
        }
      }
      break
    case 'external':
      return menu.externalUrl || undefined
    case 'none':
    default:
      return undefined
  }
  return undefined
}

/**
 * 找到字符串数组的共同前缀
 */
function findCommonPrefix(strings: string[]): string {
  if (strings.length === 0) return ''
  if (strings.length === 1) return strings[0]

  let prefix = strings[0]
  for (let i = 1; i < strings.length; i++) {
    while (strings[i].indexOf(prefix) !== 0) {
      prefix = prefix.substring(0, prefix.length - 1)
      if (prefix === '') return ''
    }
  }
  return prefix
}
