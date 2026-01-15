/**
 * 导航菜单管理 Composable
 * 提供导航菜单 CRUD、拖拽排序、发布功能
 * 
 * Requirements: 5.1, 5.2
 */
import { ref, computed, readonly } from 'vue'

// 导航菜单节点类型
export interface NavMenuNode {
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
  createdAt: Date | string
  updatedAt: Date | string
  titles: Record<string, string>
  children: NavMenuNode[]
}

// 创建菜单请求
export interface CreateNavMenuRequest {
  parentId?: string | null
  type?: 'link' | 'dropdown' | 'divider'
  targetType?: 'category' | 'document' | 'external' | 'none'
  targetId?: string | null
  externalUrl?: string | null
  openInNewTab?: boolean
  icon?: string | null
  isVisible?: boolean
  titles?: Record<string, string>
}

// 更新菜单请求
export interface UpdateNavMenuRequest {
  parentId?: string | null
  type?: 'link' | 'dropdown' | 'divider'
  targetType?: 'category' | 'document' | 'external' | 'none'
  targetId?: string | null
  externalUrl?: string | null
  openInNewTab?: boolean
  icon?: string | null
  isVisible?: boolean
  titles?: Record<string, string>
}

// 重排序项 - 从 shared/types 导入
import type { ReorderItem } from '@shared/types'

// 全局状态
const navMenus = ref<NavMenuNode[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

export function useNavMenus() {
  /**
   * 获取导航菜单树
   */
  const fetchNavMenus = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const data = await $fetch<NavMenuNode[]>('/api/nav-menus')
      navMenus.value = data
      return data
    } catch (e: any) {
      error.value = e.data?.message || e.message || '获取导航菜单失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 创建菜单项
   */
  const createNavMenu = async (data: CreateNavMenuRequest) => {
    isLoading.value = true
    error.value = null
    
    try {
      const newMenu = await $fetch<NavMenuNode>('/api/nav-menus', {
        method: 'POST',
        body: data,
      })
      
      // 更新本地状态
      if (data.parentId) {
        // 添加到父菜单的 children
        const addToParent = (nodes: NavMenuNode[]): boolean => {
          for (const node of nodes) {
            if (node.id === data.parentId) {
              node.children = node.children || []
              node.children.push(newMenu)
              return true
            }
            if (node.children && addToParent(node.children)) {
              return true
            }
          }
          return false
        }
        addToParent(navMenus.value)
      } else {
        // 添加到根级别
        navMenus.value.push(newMenu)
      }
      
      return newMenu
    } catch (e: any) {
      error.value = e.data?.message || e.message || '创建菜单失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 更新菜单项
   */
  const updateNavMenu = async (id: string, data: UpdateNavMenuRequest) => {
    isLoading.value = true
    error.value = null
    
    try {
      const updated = await $fetch<NavMenuNode>(`/api/nav-menus/${id}`, {
        method: 'PATCH',
        body: data,
      })
      
      // 更新本地状态
      const updateInTree = (nodes: NavMenuNode[]): boolean => {
        for (let i = 0; i < nodes.length; i++) {
          if (nodes[i].id === id) {
            nodes[i] = { ...nodes[i], ...updated, children: nodes[i].children }
            return true
          }
          if (nodes[i].children && updateInTree(nodes[i].children)) {
            return true
          }
        }
        return false
      }
      updateInTree(navMenus.value)
      
      return updated
    } catch (e: any) {
      error.value = e.data?.message || e.message || '更新菜单失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 删除菜单项
   */
  const deleteNavMenu = async (id: string) => {
    isLoading.value = true
    error.value = null
    
    try {
      await $fetch(`/api/nav-menus/${id}`, {
        method: 'DELETE',
      })
      
      // 从本地状态中移除
      const removeFromTree = (nodes: NavMenuNode[]): boolean => {
        for (let i = 0; i < nodes.length; i++) {
          if (nodes[i].id === id) {
            nodes.splice(i, 1)
            return true
          }
          if (nodes[i].children && removeFromTree(nodes[i].children)) {
            return true
          }
        }
        return false
      }
      removeFromTree(navMenus.value)
      
      return true
    } catch (e: any) {
      error.value = e.data?.message || e.message || '删除菜单失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 重新排序菜单
   */
  const reorderNavMenus = async (items: ReorderItem[]) => {
    isLoading.value = true
    error.value = null
    
    try {
      const updated = await $fetch<NavMenuNode[]>('/api/nav-menus/reorder', {
        method: 'POST',
        body: { items },
      })
      
      navMenus.value = updated
      return updated
    } catch (e: any) {
      error.value = e.data?.message || e.message || '排序失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 发布导航菜单到 VitePress
   */
  const publishNavMenus = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const result = await $fetch<{
        success: boolean
        message: string
        outputPath: string
        locales: string[]
        menuCount: number
      }>('/api/nav-menus/publish', {
        method: 'POST',
      })
      
      return result
    } catch (e: any) {
      error.value = e.data?.message || e.message || '发布失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 根据 ID 查找菜单
   */
  const findNavMenuById = (id: string): NavMenuNode | null => {
    const find = (nodes: NavMenuNode[]): NavMenuNode | null => {
      for (const node of nodes) {
        if (node.id === id) return node
        if (node.children) {
          const found = find(node.children)
          if (found) return found
        }
      }
      return null
    }
    return find(navMenus.value)
  }

  /**
   * 扁平化菜单树（用于下拉选择）
   */
  const flattenNavMenus = computed(() => {
    const result: Array<NavMenuNode & { level: number; fullPath: string }> = []
    
    const flatten = (nodes: NavMenuNode[], level: number, pathPrefix: string) => {
      for (const node of nodes) {
        const title = node.titles['zh'] || node.titles['en'] || `菜单 ${node.id.slice(0, 8)}`
        const fullPath = pathPrefix ? `${pathPrefix} / ${title}` : title
        result.push({ ...node, level, fullPath })
        if (node.children) {
          flatten(node.children, level + 1, fullPath)
        }
      }
    }
    
    flatten(navMenus.value, 0, '')
    return result
  })

  /**
   * 获取所有下拉菜单（可作为父菜单）
   */
  const dropdownMenus = computed(() => {
    return flattenNavMenus.value.filter(m => m.type === 'dropdown')
  })

  /**
   * 菜单类型选项
   */
  const menuTypeOptions = [
    { label: '链接', value: 'link', icon: 'i-lucide-link' },
    { label: '下拉菜单', value: 'dropdown', icon: 'i-lucide-chevron-down' },
    { label: '分割线', value: 'divider', icon: 'i-lucide-minus' },
  ]

  /**
   * 目标类型选项
   */
  const targetTypeOptions = [
    { label: '栏目', value: 'category', icon: 'i-lucide-folder' },
    { label: '文档', value: 'document', icon: 'i-lucide-file-text' },
    { label: '外部链接', value: 'external', icon: 'i-lucide-external-link' },
    { label: '无', value: 'none', icon: 'i-lucide-circle-off' },
  ]

  return {
    // 状态
    navMenus: readonly(navMenus),
    isLoading: readonly(isLoading),
    error: readonly(error),
    
    // 计算属性
    flattenNavMenus,
    dropdownMenus,
    
    // 常量
    menuTypeOptions,
    targetTypeOptions,
    
    // 方法
    fetchNavMenus,
    createNavMenu,
    updateNavMenu,
    deleteNavMenu,
    reorderNavMenus,
    publishNavMenus,
    findNavMenuById,
  }
}
