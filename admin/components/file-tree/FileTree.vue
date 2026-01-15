<script setup lang="ts">
/**
 * 文件树组件
 * 展示文档栏目的树形结构，支持拖拽排序
 * 
 * Requirements: 7.1, 7.3, 7.4, 7.5, 7.6, 7.7
 */

// 栏目节点类型
export interface CategoryNode {
  id: string
  slug: string
  parentId: string | null
  sortOrder: number
  createdAt: Date | string
  titles: Record<string, string>
  children: CategoryNode[]
  // 文档相关（可选）
  documents?: DocumentNode[]
}

export interface DocumentNode {
  id: string
  title: string
  slug: string
  status: 'draft' | 'published' | 'archived'
  hasUnsavedChanges?: boolean
}

// 树节点类型（用于 UTree）
interface TreeItem {
  id: string
  label: string
  icon?: string
  children?: TreeItem[]
  defaultExpanded?: boolean
  // 自定义数据
  type: 'category' | 'document'
  data: CategoryNode | DocumentNode
  hasUnsavedChanges?: boolean
  sortOrder?: number
  parentId?: string | null
}

const props = defineProps<{
  categories: CategoryNode[]
  locale?: string
  selectedId?: string | null
  isLoading?: boolean
}>()

const emit = defineEmits<{
  select: [item: { type: 'category' | 'document'; data: CategoryNode | DocumentNode }]
  createCategory: [parentId: string | null]
  createDocument: [categoryId: string]
  rename: [item: { type: 'category' | 'document'; data: CategoryNode | DocumentNode }]
  delete: [item: { type: 'category' | 'document'; data: CategoryNode | DocumentNode }]
  move: [item: { type: 'category' | 'document'; data: CategoryNode | DocumentNode }, newParentId: string | null]
  reorder: [items: Array<{ id: string; parentId: string | null; sortOrder: number }>]
}>()

// 当前语言，默认中文
const currentLocale = computed(() => props.locale || 'zh')

// 展开的节点
const expandedItems = ref<string[]>([])

// 选中的节点
const selectedItems = computed({
  get: () => props.selectedId ? [props.selectedId] : [],
  set: () => {} // 由外部控制
})

// 右键菜单状态
const contextMenuOpen = ref(false)
const contextMenuPosition = ref({ x: 0, y: 0 })
const contextMenuItem = ref<TreeItem | null>(null)

// 拖拽状态
const draggedItem = ref<TreeItem | null>(null)
const dropTargetId = ref<string | null>(null)
const dropPosition = ref<'before' | 'after' | 'inside' | null>(null)

// 将栏目数据转换为树节点
const treeItems = computed<TreeItem[]>(() => {
  return convertToTreeItems(props.categories)
})

function convertToTreeItems(categories: CategoryNode[]): TreeItem[] {
  return categories.map(cat => {
    const children: TreeItem[] = []
    
    // 添加子栏目
    if (cat.children && cat.children.length > 0) {
      children.push(...convertToTreeItems(cat.children))
    }
    
    // 添加文档
    if (cat.documents && cat.documents.length > 0) {
      children.push(...cat.documents.map(doc => ({
        id: `doc-${doc.id}`,
        label: doc.title,
        icon: getDocumentIcon(doc.status),
        type: 'document' as const,
        data: doc,
        hasUnsavedChanges: doc.hasUnsavedChanges,
      })))
    }
    
    return {
      id: `cat-${cat.id}`,
      label: cat.titles[currentLocale.value] || cat.titles['zh'] || cat.slug,
      icon: 'i-lucide-folder',
      children: children.length > 0 ? children : undefined,
      defaultExpanded: false,
      type: 'category' as const,
      data: cat,
      sortOrder: cat.sortOrder,
      parentId: cat.parentId,
    }
  })
}

function getDocumentIcon(status: string): string {
  switch (status) {
    case 'published':
      return 'i-lucide-file-check'
    case 'archived':
      return 'i-lucide-file-archive'
    default:
      return 'i-lucide-file-text'
  }
}

// 处理节点选择
function handleSelect(item: TreeItem) {
  const type = item.type
  const data = item.data
  emit('select', { type, data })
}

// 处理右键菜单
function handleContextMenu(event: MouseEvent, item: TreeItem) {
  event.preventDefault()
  contextMenuPosition.value = { x: event.clientX, y: event.clientY }
  contextMenuItem.value = item
  contextMenuOpen.value = true
}

// 右键菜单项
const contextMenuItems = computed(() => {
  if (!contextMenuItem.value) return []
  
  const item = contextMenuItem.value
  const isCategory = item.type === 'category'
  
  const items: any[][] = []
  
  if (isCategory) {
    items.push([
      {
        label: '新建子栏目',
        icon: 'i-lucide-folder-plus',
        onSelect: () => {
          const cat = item.data as CategoryNode
          emit('createCategory', cat.id)
        }
      },
      {
        label: '新建文档',
        icon: 'i-lucide-file-plus',
        onSelect: () => {
          const cat = item.data as CategoryNode
          emit('createDocument', cat.id)
        }
      }
    ])
  }
  
  items.push([
    {
      label: '重命名',
      icon: 'i-lucide-pencil',
      onSelect: () => {
        emit('rename', { type: item.type, data: item.data })
      }
    },
    {
      label: '移动到...',
      icon: 'i-lucide-move',
      onSelect: () => {
        emit('move', { type: item.type, data: item.data }, null)
      }
    }
  ])
  
  items.push([
    {
      label: '删除',
      icon: 'i-lucide-trash-2',
      color: 'error' as const,
      onSelect: () => {
        emit('delete', { type: item.type, data: item.data })
      }
    }
  ])
  
  return items
})

// 关闭右键菜单
function closeContextMenu() {
  contextMenuOpen.value = false
  contextMenuItem.value = null
}

// 拖拽开始
function handleDragStart(event: DragEvent, item: TreeItem) {
  if (item.type !== 'category') return // 目前只支持栏目拖拽
  
  draggedItem.value = item
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', item.id)
  }
}

// 拖拽经过
function handleDragOver(event: DragEvent, item: TreeItem) {
  event.preventDefault()
  if (!draggedItem.value || draggedItem.value.id === item.id) return
  if (item.type !== 'category') return // 只能拖到栏目上
  
  // 检查是否是拖拽到自己的子节点
  if (isDescendant(draggedItem.value, item)) return
  
  dropTargetId.value = item.id
  
  // 根据鼠标位置确定放置位置
  const rect = (event.target as HTMLElement).getBoundingClientRect()
  const y = event.clientY - rect.top
  const height = rect.height
  
  if (y < height * 0.25) {
    dropPosition.value = 'before'
  } else if (y > height * 0.75) {
    dropPosition.value = 'after'
  } else {
    dropPosition.value = 'inside'
  }
}

// 拖拽离开
function handleDragLeave() {
  dropTargetId.value = null
  dropPosition.value = null
}

// 放置
function handleDrop(event: DragEvent, targetItem: TreeItem) {
  event.preventDefault()
  
  if (!draggedItem.value || draggedItem.value.id === targetItem.id) {
    resetDragState()
    return
  }
  
  if (targetItem.type !== 'category') {
    resetDragState()
    return
  }
  
  // 检查是否是拖拽到自己的子节点
  if (isDescendant(draggedItem.value, targetItem)) {
    resetDragState()
    return
  }
  
  const draggedCat = draggedItem.value.data as CategoryNode
  const targetCat = targetItem.data as CategoryNode
  
  // 根据放置位置计算新的 parentId 和 sortOrder
  let newParentId: string | null
  let newSortOrder: number
  
  if (dropPosition.value === 'inside') {
    // 放到目标内部
    newParentId = targetCat.id
    newSortOrder = targetCat.children?.length || 0
  } else {
    // 放到目标前面或后面
    newParentId = targetCat.parentId
    newSortOrder = dropPosition.value === 'before' 
      ? targetCat.sortOrder 
      : targetCat.sortOrder + 1
  }
  
  // 发出重排序事件
  emit('reorder', [{
    id: draggedCat.id,
    parentId: newParentId,
    sortOrder: newSortOrder,
  }])
  
  resetDragState()
}

// 拖拽结束
function handleDragEnd() {
  resetDragState()
}

// 重置拖拽状态
function resetDragState() {
  draggedItem.value = null
  dropTargetId.value = null
  dropPosition.value = null
}

// 检查 item 是否是 target 的祖先
function isDescendant(ancestor: TreeItem, target: TreeItem): boolean {
  if (ancestor.type !== 'category' || target.type !== 'category') return false
  
  const ancestorCat = ancestor.data as CategoryNode
  const targetCat = target.data as CategoryNode
  
  // 检查 target 的 parentId 链是否包含 ancestor
  let currentParentId = targetCat.parentId
  while (currentParentId) {
    if (currentParentId === ancestorCat.id) return true
    // 在树中查找父节点
    const parent = findCategoryById(currentParentId, props.categories)
    currentParentId = parent?.parentId || null
  }
  
  return false
}

// 根据 ID 查找栏目
function findCategoryById(id: string, categories: CategoryNode[]): CategoryNode | null {
  for (const cat of categories) {
    if (cat.id === id) return cat
    if (cat.children) {
      const found = findCategoryById(id, cat.children)
      if (found) return found
    }
  }
  return null
}

// 点击外部关闭菜单
onMounted(() => {
  document.addEventListener('click', closeContextMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', closeContextMenu)
})
</script>

<template>
  <div class="file-tree">
    <!-- 工具栏 -->
    <div class="flex items-center justify-between px-3 py-2 border-b border-gray-200 dark:border-gray-800">
      <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
        栏目
      </span>
      <div class="flex items-center gap-1">
        <UTooltip text="刷新">
          <UButton
            variant="ghost"
            color="neutral"
            size="xs"
            icon="i-lucide-refresh-cw"
            :loading="isLoading"
            @click="$emit('refresh' as any)"
          />
        </UTooltip>
        <UTooltip text="新建栏目">
          <UButton
            variant="ghost"
            color="neutral"
            size="xs"
            icon="i-lucide-folder-plus"
            @click="emit('createCategory', null)"
          />
        </UTooltip>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading && categories.length === 0" class="flex items-center justify-center py-8">
      <UIcon name="i-lucide-loader-2" class="w-6 h-6 animate-spin text-gray-400" />
    </div>

    <!-- 树形结构 -->
    <div v-else class="flex-1 overflow-auto p-2">
      <UTree
        v-if="treeItems.length > 0"
        v-model:expanded="expandedItems"
        v-model:selected="selectedItems"
        :items="treeItems"
        class="w-full"
        @select="handleSelect"
      >
        <template #item="{ item }">
          <div
            class="flex items-center gap-2 w-full group relative"
            :class="{
              'opacity-50': draggedItem?.id === item.id,
              'ring-2 ring-primary-500 ring-inset rounded': dropTargetId === item.id && dropPosition === 'inside',
            }"
            draggable="true"
            @contextmenu="handleContextMenu($event, item)"
            @dragstart="handleDragStart($event, item)"
            @dragover="handleDragOver($event, item)"
            @dragleave="handleDragLeave"
            @drop="handleDrop($event, item)"
            @dragend="handleDragEnd"
          >
            <!-- 放置位置指示器 - 上方 -->
            <div
              v-if="dropTargetId === item.id && dropPosition === 'before'"
              class="absolute -top-0.5 left-0 right-0 h-0.5 bg-primary-500 rounded"
            />
            
            <!-- 图标 -->
            <UIcon
              :name="item.icon || 'i-lucide-file'"
              class="w-4 h-4 shrink-0"
              :class="{
                'text-amber-500': item.type === 'category',
                'text-blue-500': item.type === 'document' && item.data?.status === 'published',
                'text-gray-400': item.type === 'document' && item.data?.status !== 'published',
              }"
            />
            
            <!-- 标签 -->
            <span class="truncate flex-1 text-sm">{{ item.label }}</span>
            
            <!-- 未保存指示器 -->
            <span
              v-if="item.hasUnsavedChanges"
              class="w-2 h-2 rounded-full bg-orange-500 shrink-0"
              title="有未保存的更改"
            />
            
            <!-- 更多操作按钮 -->
            <UButton
              variant="ghost"
              color="neutral"
              size="xs"
              icon="i-lucide-more-horizontal"
              class="opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
              @click.stop="handleContextMenu($event, item)"
            />
            
            <!-- 放置位置指示器 - 下方 -->
            <div
              v-if="dropTargetId === item.id && dropPosition === 'after'"
              class="absolute -bottom-0.5 left-0 right-0 h-0.5 bg-primary-500 rounded"
            />
          </div>
        </template>
      </UTree>

      <!-- 空状态 -->
      <div
        v-else
        class="flex flex-col items-center justify-center py-8 text-gray-400 dark:text-gray-500"
      >
        <UIcon name="i-lucide-folder-open" class="w-12 h-12 mb-2" />
        <p class="text-sm">暂无栏目</p>
        <UButton
          variant="link"
          size="sm"
          class="mt-2"
          @click="emit('createCategory', null)"
        >
          创建第一个栏目
        </UButton>
      </div>
    </div>

    <!-- 右键菜单 -->
    <UContextMenu
      v-model:open="contextMenuOpen"
      :items="contextMenuItems"
      :style="{
        position: 'fixed',
        left: `${contextMenuPosition.x}px`,
        top: `${contextMenuPosition.y}px`,
      }"
    />
  </div>
</template>

<style scoped>
.file-tree {
  @apply flex flex-col h-full;
}
</style>
