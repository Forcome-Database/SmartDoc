/**
 * 栏目管理 Composable
 * 提供栏目 CRUD、拖拽排序、状态管理功能
 * 
 * Requirements: 2.1, 2.2, 2.3, 2.4, 7.4, 7.5, 7.7
 */
import { ref, computed, readonly } from 'vue'

// 栏目节点类型
export interface CategoryNode {
  id: string
  slug: string
  parentId: string | null
  sortOrder: number
  createdAt: Date | string
  titles: Record<string, string>
  children: CategoryNode[]
}

// 创建栏目请求
export interface CreateCategoryRequest {
  slug: string
  parentId?: string | null
  titles: Record<string, string>
}

// 更新栏目请求
export interface UpdateCategoryRequest {
  slug?: string
  parentId?: string | null
  titles?: Record<string, string>
}

// 重排序项 - 从 shared/types 导入
import type { ReorderItem } from '@shared/types'

// 全局状态
const categories = ref<CategoryNode[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

export function useCategories() {
  /**
   * 获取栏目树
   */
  const fetchCategories = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const data = await $fetch<CategoryNode[]>('/api/categories')
      categories.value = data
      return data
    } catch (e: any) {
      error.value = e.data?.message || e.message || '获取栏目失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 获取单个栏目详情
   */
  const fetchCategory = async (id: string) => {
    try {
      return await $fetch<CategoryNode & { titlesByLocaleId: Record<string, string> }>(`/api/categories/${id}`)
    } catch (e: any) {
      error.value = e.data?.message || e.message || '获取栏目详情失败'
      throw e
    }
  }

  /**
   * 创建栏目
   */
  const createCategory = async (data: CreateCategoryRequest) => {
    isLoading.value = true
    error.value = null
    
    try {
      const newCategory = await $fetch<CategoryNode>('/api/categories', {
        method: 'POST',
        body: data,
      })
      
      // 更新本地状态
      if (data.parentId) {
        // 添加到父栏目的 children
        const addToParent = (nodes: CategoryNode[]): boolean => {
          for (const node of nodes) {
            if (node.id === data.parentId) {
              node.children = node.children || []
              node.children.push(newCategory)
              return true
            }
            if (node.children && addToParent(node.children)) {
              return true
            }
          }
          return false
        }
        addToParent(categories.value)
      } else {
        // 添加到根级别
        categories.value.push(newCategory)
      }
      
      return newCategory
    } catch (e: any) {
      error.value = e.data?.message || e.message || '创建栏目失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 更新栏目
   */
  const updateCategory = async (id: string, data: UpdateCategoryRequest) => {
    isLoading.value = true
    error.value = null
    
    try {
      const updated = await $fetch<CategoryNode>(`/api/categories/${id}`, {
        method: 'PATCH',
        body: data,
      })
      
      // 更新本地状态
      const updateInTree = (nodes: CategoryNode[]): boolean => {
        for (let i = 0; i < nodes.length; i++) {
          if (nodes[i].id === id) {
            nodes[i] = { ...nodes[i], ...updated }
            return true
          }
          if (nodes[i].children && updateInTree(nodes[i].children)) {
            return true
          }
        }
        return false
      }
      updateInTree(categories.value)
      
      return updated
    } catch (e: any) {
      error.value = e.data?.message || e.message || '更新栏目失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 删除栏目
   */
  const deleteCategory = async (id: string) => {
    isLoading.value = true
    error.value = null
    
    try {
      await $fetch(`/api/categories/${id}`, {
        method: 'DELETE',
      })
      
      // 从本地状态中移除
      const removeFromTree = (nodes: CategoryNode[]): boolean => {
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
      removeFromTree(categories.value)
      
      return true
    } catch (e: any) {
      error.value = e.data?.message || e.message || '删除栏目失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 重新排序栏目
   */
  const reorderCategories = async (items: ReorderItem[]) => {
    isLoading.value = true
    error.value = null
    
    try {
      const updated = await $fetch<CategoryNode[]>('/api/categories/reorder', {
        method: 'POST',
        body: { items },
      })
      
      categories.value = updated
      return updated
    } catch (e: any) {
      error.value = e.data?.message || e.message || '排序失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 移动栏目到新的父栏目
   */
  const moveCategory = async (id: string, newParentId: string | null) => {
    // 找到当前栏目
    const findCategory = (nodes: CategoryNode[], targetId: string): CategoryNode | null => {
      for (const node of nodes) {
        if (node.id === targetId) return node
        if (node.children) {
          const found = findCategory(node.children, targetId)
          if (found) return found
        }
      }
      return null
    }
    
    const category = findCategory(categories.value, id)
    if (!category) {
      throw new Error('栏目不存在')
    }
    
    // 获取新父栏目下的最大 sortOrder
    let maxSortOrder = -1
    if (newParentId) {
      const parent = findCategory(categories.value, newParentId)
      if (parent?.children) {
        maxSortOrder = Math.max(...parent.children.map(c => c.sortOrder), -1)
      }
    } else {
      maxSortOrder = Math.max(...categories.value.map(c => c.sortOrder), -1)
    }
    
    // 调用重排序 API
    return reorderCategories([{
      id,
      parentId: newParentId,
      sortOrder: maxSortOrder + 1,
    }])
  }

  /**
   * 根据 ID 查找栏目
   */
  const findCategoryById = (id: string): CategoryNode | null => {
    const find = (nodes: CategoryNode[]): CategoryNode | null => {
      for (const node of nodes) {
        if (node.id === id) return node
        if (node.children) {
          const found = find(node.children)
          if (found) return found
        }
      }
      return null
    }
    return find(categories.value)
  }

  /**
   * 获取栏目路径（面包屑）
   */
  const getCategoryPath = (id: string): CategoryNode[] => {
    const path: CategoryNode[] = []
    
    const findPath = (nodes: CategoryNode[], targetId: string): boolean => {
      for (const node of nodes) {
        if (node.id === targetId) {
          path.push(node)
          return true
        }
        if (node.children && findPath(node.children, targetId)) {
          path.unshift(node)
          return true
        }
      }
      return false
    }
    
    findPath(categories.value, id)
    return path
  }

  /**
   * 扁平化栏目树（用于下拉选择）
   */
  const flattenCategories = computed(() => {
    const result: Array<CategoryNode & { level: number; fullPath: string }> = []
    
    const flatten = (nodes: CategoryNode[], level: number, pathPrefix: string) => {
      for (const node of nodes) {
        const fullPath = pathPrefix ? `${pathPrefix} / ${node.titles['zh'] || node.slug}` : (node.titles['zh'] || node.slug)
        result.push({ ...node, level, fullPath })
        if (node.children) {
          flatten(node.children, level + 1, fullPath)
        }
      }
    }
    
    flatten(categories.value, 0, '')
    return result
  })

  return {
    // 状态
    categories: readonly(categories),
    isLoading: readonly(isLoading),
    error: readonly(error),
    
    // 计算属性
    flattenCategories,
    
    // 方法
    fetchCategories,
    fetchCategory,
    createCategory,
    updateCategory,
    deleteCategory,
    reorderCategories,
    moveCategory,
    findCategoryById,
    getCategoryPath,
  }
}
