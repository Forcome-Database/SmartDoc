<script setup lang="ts">
/**
 * 内容树组件
 * 统一展示栏目和文档的树形结构，支持内联编辑和拖拽排序
 * 类似 Mintlify 的文件管理交互
 */
import ContentTreeNode from './ContentTreeNode.vue'

// 语言类型
interface Locale {
  id: string
  code: string
  name: string
  nativeName: string
  isDefault: boolean
  isEnabled: boolean
}

// 内容节点类型
export interface ContentNode {
  id: string
  type: 'category' | 'document'
  name: string
  slug: string
  parentId: string | null
  sortOrder: number
  titles?: Record<string, string>
  status?: 'draft' | 'published' | 'archived'
  localeCode?: string
  children: ContentNode[]
}

const props = defineProps<{
  tree: ContentNode[]
  selectedId?: string | null
  isLoading?: boolean
  locale?: string
}>()

// 获取可用语言列表
const { data: locales } = useFetch<Locale[]>('/api/locales')

// 当前选中的语言（默认 zh）
const selectedLocaleCode = ref('zh')

// 语言选项
const localeOptions = computed(() => {
  if (!locales.value) return []
  return locales.value
    .filter(l => l.isEnabled)
    .map(l => ({
      label: `${l.nativeName}`,
      value: l.code,
    }))
})

// 按语言筛选后的树
const filteredTree = computed(() => {
  if (!selectedLocaleCode.value) return props.tree
  
  // 递归过滤：保留栏目，只显示匹配语言的文档
  const filterNodes = (nodes: ContentNode[]): ContentNode[] => {
    return nodes.map(node => {
      if (node.type === 'category') {
        // 栏目：递归过滤子节点
        const filteredChildren = filterNodes(node.children)
        return { ...node, children: filteredChildren }
      } else {
        // 文档：检查语言是否匹配
        return node
      }
    }).filter(node => {
      if (node.type === 'category') {
        // 栏目：保留（即使没有子节点也显示）
        return true
      } else {
        // 文档：只保留匹配语言的
        return node.localeCode === selectedLocaleCode.value
      }
    })
  }
  
  return filterNodes(props.tree)
})

const emit = defineEmits<{
  select: [node: ContentNode]
  createCategory: [parentId: string | null, name: string]
  createDocument: [categoryId: string, name: string, localeCode: string]
  rename: [node: ContentNode, newName: string]
  delete: [node: ContentNode]
  move: [node: ContentNode, newParentId: string | null, position?: 'before' | 'after' | 'inside', targetNode?: ContentNode]
  reorder: [items: Array<{ id: string; parentId: string | null; sortOrder: number; type: 'category' | 'document' }>]
  refresh: []
  localeChange: [localeCode: string]
}>()

// 监听语言切换，通知父组件
watch(selectedLocaleCode, (newLocale) => {
  emit('localeChange', newLocale)
})

/**
 * 展开到指定文档并选中
 * @param documentId 文档 ID
 */
const expandToDocument = (documentId: string) => {
  // 递归查找文档并收集父节点路径
  const findDocumentPath = (nodes: ContentNode[], path: string[] = []): string[] | null => {
    for (const node of nodes) {
      if (node.type === 'document' && node.id === documentId) {
        return path
      }
      if (node.type === 'category' && node.children.length > 0) {
        const result = findDocumentPath(node.children, [...path, node.id])
        if (result) return result
      }
    }
    return null
  }
  
  const path = findDocumentPath(props.tree)
  if (path) {
    // 展开所有父栏目
    path.forEach(id => expandedIds.value.add(id))
    
    // 设置语言筛选器为文档的语言
    const doc = findDocumentById(documentId)
    if (doc?.localeCode) {
      selectedLocaleCode.value = doc.localeCode
    }
    
    // 滚动到文档位置
    nextTick(() => {
      const element = document.querySelector(`[data-node-id="doc-${documentId}"]`)
      element?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    })
  }
}

// 递归查找文档
const findDocumentById = (documentId: string): ContentNode | null => {
  const find = (nodes: ContentNode[]): ContentNode | null => {
    for (const node of nodes) {
      if (node.type === 'document' && node.id === documentId) return node
      if (node.children) {
        const found = find(node.children)
        if (found) return found
      }
    }
    return null
  }
  return find(props.tree)
}

// 暴露方法给父组件
defineExpose({
  expandToDocument,
})

// 当前语言
const currentLocale = computed(() => props.locale || 'zh')

// 展开的节点
const expandedIds = ref<Set<string>>(new Set())

// 是否全部展开
const isAllExpanded = ref(false)

// 展开/收起所有栏目
const toggleExpandAll = () => {
  if (isAllExpanded.value) {
    // 收起所有
    expandedIds.value.clear()
  } else {
    // 展开所有栏目
    const collectCategoryIds = (nodes: ContentNode[]) => {
      for (const node of nodes) {
        if (node.type === 'category') {
          expandedIds.value.add(node.id)
          if (node.children) {
            collectCategoryIds(node.children)
          }
        }
      }
    }
    collectCategoryIds(props.tree)
  }
  isAllExpanded.value = !isAllExpanded.value
}

// 内联编辑状态
const editingId = ref<string | null>(null)
const editingName = ref('')
const editingType = ref<'rename' | 'new-category' | 'new-document' | null>(null)
const editingParentId = ref<string | null>(null)

// 输入框引用
const inputRef = ref<HTMLInputElement | null>(null)

// 拖拽状态
const draggingNode = ref<ContentNode | null>(null)
const dragOverId = ref<string | null>(null)
const dragOverPosition = ref<'before' | 'after' | 'inside' | null>(null)

// 右键菜单（保留用于未来扩展）
const contextMenuOpen = ref(false)
const contextMenuNode = ref<ContentNode | null>(null)

// 删除确认
const deleteConfirmOpen = ref(false)
const deleteTarget = ref<ContentNode | null>(null)

// 获取节点显示名称
const getNodeName = (node: ContentNode) => {
  if (node.type === 'category') {
    return node.titles?.[currentLocale.value] || node.titles?.zh || node.slug
  }
  return node.name
}

// 获取节点图标
const getNodeIcon = (node: ContentNode) => {
  if (node.type === 'category') {
    return expandedIds.value.has(node.id) ? 'i-lucide-folder-open' : 'i-lucide-folder'
  }
  switch (node.status) {
    case 'published': return 'i-lucide-file-check'
    case 'archived': return 'i-lucide-file-archive'
    default: return 'i-lucide-file-text'
  }
}

// 获取图标颜色
const getIconColor = (node: ContentNode) => {
  if (node.type === 'category') return 'text-amber-500'
  switch (node.status) {
    case 'published': return 'text-green-500'
    case 'archived': return 'text-gray-400'
    default: return 'text-blue-500'
  }
}

// 切换展开状态
const toggleExpand = (node: ContentNode) => {
  if (expandedIds.value.has(node.id)) {
    expandedIds.value.delete(node.id)
  } else {
    expandedIds.value.add(node.id)
  }
}

// 处理节点点击
const handleNodeClick = (node: ContentNode) => {
  if (node.type === 'category') {
    toggleExpand(node)
  }
  emit('select', node)
}

// 开始内联创建栏目
const startCreateCategory = (parentId: string | null) => {
  editingType.value = 'new-category'
  editingParentId.value = parentId
  editingId.value = `new-cat-${Date.now()}`
  editingName.value = ''
  
  // 展开父节点
  if (parentId) {
    expandedIds.value.add(parentId)
  }
  
  nextTick(() => inputRef.value?.focus())
}

// 开始内联创建文档
const startCreateDocument = (categoryId: string) => {
  editingType.value = 'new-document'
  editingParentId.value = categoryId
  editingId.value = `new-doc-${Date.now()}`
  editingName.value = ''
  
  // 展开父节点
  expandedIds.value.add(categoryId)
  
  nextTick(() => inputRef.value?.focus())
}

// 开始重命名
const startRename = (node: ContentNode) => {
  editingType.value = 'rename'
  editingId.value = node.id
  editingName.value = getNodeName(node)
  
  nextTick(() => {
    inputRef.value?.focus()
    inputRef.value?.select()
  })
}

// 确认编辑
const confirmEdit = () => {
  if (!editingName.value.trim()) {
    cancelEdit()
    return
  }
  
  if (editingType.value === 'new-category') {
    emit('createCategory', editingParentId.value, editingName.value.trim())
  } else if (editingType.value === 'new-document') {
    emit('createDocument', editingParentId.value!, editingName.value.trim(), selectedLocaleCode.value)
  } else if (editingType.value === 'rename' && editingId.value) {
    const node = findNodeById(editingId.value)
    if (node) {
      emit('rename', node, editingName.value.trim())
    }
  }
  
  cancelEdit()
}

// 取消编辑
const cancelEdit = () => {
  editingType.value = null
  editingId.value = null
  editingName.value = ''
  editingParentId.value = null
}

// 处理键盘事件
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter') {
    confirmEdit()
  } else if (e.key === 'Escape') {
    cancelEdit()
  }
}

// 打开删除确认
const openDeleteConfirm = (node: ContentNode) => {
  deleteTarget.value = node
  deleteConfirmOpen.value = true
}

// 确认删除
const confirmDelete = () => {
  if (deleteTarget.value) {
    emit('delete', deleteTarget.value)
  }
  deleteConfirmOpen.value = false
  deleteTarget.value = null
}

// 拖拽事件处理
const handleDragStart = (node: ContentNode) => {
  draggingNode.value = node
}

const handleDragEnd = () => {
  draggingNode.value = null
  dragOverId.value = null
  dragOverPosition.value = null
}

const handleDragOver = (node: ContentNode, position: 'before' | 'after' | 'inside') => {
  // 不能拖到自己身上
  if (draggingNode.value?.id === node.id) return
  // 不能拖到自己的子节点
  if (draggingNode.value && isDescendant(draggingNode.value, node)) return
  
  dragOverId.value = node.id
  dragOverPosition.value = position
}

const handleDrop = (targetNode: ContentNode, position: 'before' | 'after' | 'inside') => {
  if (!draggingNode.value) return
  if (draggingNode.value.id === targetNode.id) return
  if (isDescendant(draggingNode.value, targetNode)) return
  
  emit('move', draggingNode.value, targetNode.parentId, position, targetNode)
  
  // 重置拖拽状态
  draggingNode.value = null
  dragOverId.value = null
  dragOverPosition.value = null
}

// 检查 node 是否是 target 的祖先
const isDescendant = (ancestor: ContentNode, target: ContentNode): boolean => {
  const check = (nodes: ContentNode[]): boolean => {
    for (const node of nodes) {
      if (node.id === target.id) return true
      if (node.children && check(node.children)) return true
    }
    return false
  }
  return ancestor.children ? check(ancestor.children) : false
}

// 根据 ID 查找节点
const findNodeById = (id: string): ContentNode | null => {
  const find = (nodes: ContentNode[]): ContentNode | null => {
    for (const node of nodes) {
      if (node.id === id) return node
      if (node.children) {
        const found = find(node.children)
        if (found) return found
      }
    }
    return null
  }
  return find(props.tree)
}
</script>

<template>
  <div class="content-tree flex flex-col h-full">
    <!-- 工具栏 -->
    <div class="flex items-center justify-between px-3 py-2 border-b border-gray-200 dark:border-gray-800">
      <div class="flex items-center gap-2">
        <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
          Files
        </span>
        <!-- 语言选择器 -->
        <USelectMenu
          v-model="selectedLocaleCode"
          :items="localeOptions"
          value-key="value"
          size="xs"
          class="w-20"
        />
      </div>
      <div class="flex items-center gap-1">
        <UTooltip :text="isAllExpanded ? '收起全部' : '展开全部'">
          <UButton
            variant="ghost"
            color="neutral"
            size="xs"
            :icon="isAllExpanded ? 'i-lucide-fold-vertical' : 'i-lucide-unfold-vertical'"
            @click="toggleExpandAll"
          />
        </UTooltip>
        <UTooltip text="新建栏目">
          <UButton
            variant="ghost"
            color="neutral"
            size="xs"
            icon="i-lucide-folder-plus"
            @click="startCreateCategory(null)"
          />
        </UTooltip>
        <UTooltip text="刷新">
          <UButton
            variant="ghost"
            color="neutral"
            size="xs"
            icon="i-lucide-refresh-cw"
            :loading="isLoading"
            @click="emit('refresh')"
          />
        </UTooltip>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading && tree.length === 0" class="flex items-center justify-center py-8">
      <UIcon name="i-lucide-loader-2" class="w-6 h-6 animate-spin text-gray-400" />
    </div>

    <!-- 树形结构 -->
    <div v-else class="flex-1 overflow-auto py-2">
      <!-- 递归渲染树 -->
      <ContentTreeNode
        v-for="node in filteredTree"
        :key="node.id"
        :node="node"
        :level="0"
        :expanded-ids="expandedIds"
        :selected-id="selectedId"
        :editing-id="editingId"
        :editing-name="editingName"
        :editing-type="editingType"
        :editing-parent-id="editingParentId"
        :locale="currentLocale"
        :drag-over-id="dragOverId"
        :drag-over-position="dragOverPosition"
        @click="handleNodeClick"
        @toggle="toggleExpand"
        @create-category="startCreateCategory"
        @create-document="startCreateDocument"
        @rename="startRename"
        @delete="openDeleteConfirm"
        @update:editing-name="editingName = $event"
        @confirm-edit="confirmEdit"
        @cancel-edit="cancelEdit"
        @drag-start="handleDragStart"
        @drag-end="handleDragEnd"
        @drag-over="handleDragOver"
        @drop="handleDrop"
      />
      
      <!-- 根级别新建节点 -->
      <div
        v-if="editingType === 'new-category' && editingParentId === null"
        class="flex items-center gap-2 px-3 py-1.5"
      >
        <UIcon name="i-lucide-folder" class="w-4 h-4 text-amber-500 shrink-0" />
        <input
          ref="inputRef"
          v-model="editingName"
          type="text"
          class="flex-1 text-sm bg-transparent border border-primary-500 rounded px-2 py-0.5 outline-none"
          placeholder="栏目名称"
          @keydown="handleKeydown"
          @blur="confirmEdit"
        />
      </div>

      <!-- 空状态 -->
      <div
        v-if="tree.length === 0 && !isLoading && !editingType"
        class="flex flex-col items-center justify-center py-8 text-gray-400"
      >
        <UIcon name="i-lucide-folder-open" class="w-12 h-12 mb-2" />
        <p class="text-sm">暂无内容</p>
        <UButton
          variant="link"
          size="sm"
          class="mt-2"
          @click="startCreateCategory(null)"
        >
          创建第一个栏目
        </UButton>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <UModal v-model:open="deleteConfirmOpen">
      <template #content>
        <div class="p-6">
          <div class="flex items-start gap-4">
            <div class="p-3 rounded-full bg-red-100 dark:bg-red-500/20">
              <UIcon name="i-lucide-alert-triangle" class="w-6 h-6 text-red-600 dark:text-red-400" />
            </div>
            <div class="flex-1">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                确认删除
              </h3>
              <p class="text-gray-500 dark:text-gray-400 mt-2">
                确定要删除 "{{ deleteTarget ? (deleteTarget.type === 'category' ? (deleteTarget.titles?.zh || deleteTarget.slug) : deleteTarget.name) : '' }}" 吗？
              </p>
              <p v-if="deleteTarget?.type === 'category'" class="text-sm text-red-500 mt-2">
                注意：如果该栏目下有子栏目或文档，需要先删除或移动它们。
              </p>
            </div>
          </div>
          
          <div class="flex justify-end gap-3 mt-6">
            <UButton variant="ghost" color="neutral" @click="deleteConfirmOpen = false">
              取消
            </UButton>
            <UButton color="error" @click="confirmDelete">
              删除
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
