/**
 * 内容树管理 Composable
 * 统一管理栏目和文档的树形结构
 * 
 * 功能：
 * - 获取完整的内容树（栏目 + 文档）
 * - 创建/重命名/删除/移动 栏目和文档
 * - 拖拽排序
 */
import { ref, readonly } from 'vue'

// 内容节点类型
export interface ContentNode {
  id: string
  type: 'category' | 'document'
  name: string
  slug: string
  parentId: string | null
  sortOrder: number
  // 栏目特有
  titles?: Record<string, string>
  // 文档特有
  status?: 'draft' | 'published' | 'archived'
  localeCode?: string
  // 子节点
  children: ContentNode[]
}

// 全局状态
const tree = ref<ContentNode[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

export function useContentTree() {
  /**
   * 获取完整内容树
   */
  const fetchTree = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const data = await $fetch<ContentNode[]>('/api/content/tree')
      tree.value = data
      return data
    } catch (e: any) {
      error.value = e.data?.message || e.message || '获取内容树失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 创建栏目
   */
  const createCategory = async (parentId: string | null, name: string) => {
    isLoading.value = true
    
    try {
      // 生成 slug（只保留英文、数字和连字符）
      const slug = name
        .toLowerCase()
        .replace(/[\u4e00-\u9fa5]/g, '') // 移除中文字符
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '')
        || `category-${Date.now()}` // 如果全是中文，使用时间戳
      
      const newCategory = await $fetch<ContentNode>('/api/categories', {
        method: 'POST',
        body: {
          slug,
          parentId,
          titles: { zh: name, en: name, vi: name },
        },
      })
      
      // 刷新树
      await fetchTree()
      
      return newCategory
    } catch (e: any) {
      error.value = e.data?.message || e.message || '创建栏目失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 创建文档
   */
  const createDocument = async (categoryId: string, name: string, localeCode?: string) => {
    isLoading.value = true
    
    try {
      // 生成 slug（只保留英文、数字和连字符）
      const slug = name
        .toLowerCase()
        .replace(/[\u4e00-\u9fa5]/g, '') // 移除中文字符
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '')
        || `doc-${Date.now()}` // 如果全是中文，使用时间戳
      
      // 获取语言 ID
      const locales = await $fetch<Array<{ id: string; code: string; isDefault: boolean }>>('/api/locales')
      let targetLocale = locales.find(l => l.code === localeCode)
      if (!targetLocale) {
        targetLocale = locales.find(l => l.isDefault) || locales[0]
      }
      
      if (!targetLocale) {
        throw new Error('没有可用的语言配置')
      }
      
      const newDoc = await $fetch<{ id: string }>('/api/documents', {
        method: 'POST',
        body: {
          title: name,
          slug,
          categoryId,
          localeId: targetLocale.id,
          content: '',
        },
      })
      
      // 刷新树
      await fetchTree()
      
      return newDoc
    } catch (e: any) {
      error.value = e.data?.message || e.message || '创建文档失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 重命名节点
   */
  const renameItem = async (node: ContentNode, newName: string) => {
    isLoading.value = true
    
    try {
      if (node.type === 'category') {
        await $fetch(`/api/categories/${node.id}`, {
          method: 'PATCH',
          body: {
            titles: { ...node.titles, zh: newName },
          },
        })
      } else {
        await $fetch(`/api/documents/${node.id}`, {
          method: 'PATCH',
          body: { title: newName },
        })
      }
      
      // 刷新树
      await fetchTree()
    } catch (e: any) {
      error.value = e.data?.message || e.message || '重命名失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 删除节点
   */
  const deleteItem = async (node: ContentNode) => {
    isLoading.value = true
    
    try {
      const endpoint = node.type === 'category' 
        ? `/api/categories/${node.id}`
        : `/api/documents/${node.id}`
      
      await $fetch(endpoint, { method: 'DELETE' })
      
      // 刷新树
      await fetchTree()
    } catch (e: any) {
      error.value = e.data?.message || e.message || '删除失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 移动节点
   */
  const moveItem = async (
    node: ContentNode, 
    newParentId: string | null,
    position?: 'before' | 'after' | 'inside',
    targetNode?: ContentNode
  ) => {
    isLoading.value = true
    
    try {
      if (node.type === 'category') {
        // 栏目移动
        let targetParentId = newParentId
        let sortOrder = 0
        
        if (position === 'inside' && targetNode?.type === 'category') {
          // 移动到栏目内部
          targetParentId = targetNode.id
        } else if (position === 'before' || position === 'after') {
          // 移动到目标节点前后
          targetParentId = targetNode?.parentId ?? null
          // 计算排序位置
          sortOrder = targetNode?.sortOrder ?? 0
          if (position === 'after') sortOrder += 1
        }
        
        await $fetch('/api/categories/reorder', {
          method: 'POST',
          body: {
            items: [{
              id: node.id,
              parentId: targetParentId,
              sortOrder,
            }],
          },
        })
      } else {
        // 文档移动
        let targetCategoryId = newParentId
        
        if (position === 'inside' && targetNode?.type === 'category') {
          targetCategoryId = targetNode.id
        } else if (targetNode) {
          // 文档只能移动到栏目内，取目标的父栏目
          targetCategoryId = targetNode.type === 'category' ? targetNode.id : targetNode.parentId
        }
        
        await $fetch(`/api/documents/${node.id}`, {
          method: 'PATCH',
          body: { categoryId: targetCategoryId },
        })
      }
      
      // 刷新树
      await fetchTree()
    } catch (e: any) {
      error.value = e.data?.message || e.message || '移动失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 重新排序
   */
  const reorderItems = async (items: Array<{ id: string; parentId: string | null; sortOrder: number; type: 'category' | 'document' }>) => {
    isLoading.value = true
    
    try {
      // 分离栏目和文档
      const categoryItems = items.filter(i => i.type === 'category')
      const documentItems = items.filter(i => i.type === 'document')
      
      // 栏目排序
      if (categoryItems.length > 0) {
        await $fetch('/api/categories/reorder', {
          method: 'POST',
          body: { items: categoryItems },
        })
      }
      
      // 文档排序（如果需要）
      // TODO: 实现文档排序 API
      
      // 刷新树
      await fetchTree()
    } catch (e: any) {
      error.value = e.data?.message || e.message || '排序失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 根据 ID 查找节点
   */
  const findNodeById = (id: string, type: 'category' | 'document'): ContentNode | null => {
    const find = (nodes: ContentNode[]): ContentNode | null => {
      for (const node of nodes) {
        if (node.id === id && node.type === type) return node
        if (node.children) {
          const found = find(node.children)
          if (found) return found
        }
      }
      return null
    }
    return find(tree.value)
  }

  /**
   * 更新文档标题（本地更新，不请求 API）
   */
  const updateDocumentTitle = (documentId: string, newTitle: string) => {
    const updateInTree = (nodes: ContentNode[]): boolean => {
      for (const node of nodes) {
        if (node.type === 'document' && node.id === documentId) {
          node.name = newTitle
          return true
        }
        if (node.children && updateInTree(node.children)) {
          return true
        }
      }
      return false
    }
    updateInTree(tree.value)
  }

  return {
    // 状态
    tree: readonly(tree),
    isLoading: readonly(isLoading),
    error: readonly(error),
    
    // 方法
    fetchTree,
    createCategory,
    createDocument,
    renameItem,
    deleteItem,
    moveItem,
    reorderItems,
    findNodeById,
    updateDocumentTitle,
  }
}
