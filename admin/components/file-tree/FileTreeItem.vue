<script setup lang="ts">
/**
 * 文件树项组件
 * 单个树节点的渲染组件，支持展开/折叠、选中、右键菜单
 * 
 * Requirements: 7.1, 7.3, 7.6
 */

export interface TreeItemData {
  id: string
  label: string
  icon?: string
  type: 'category' | 'document'
  hasChildren: boolean
  hasUnsavedChanges?: boolean
  status?: 'draft' | 'published' | 'archived'
}

const props = defineProps<{
  item: TreeItemData
  level?: number
  isExpanded?: boolean
  isSelected?: boolean
  isDragging?: boolean
  isDropTarget?: boolean
}>()

const emit = defineEmits<{
  toggle: []
  select: []
  contextmenu: [event: MouseEvent]
  dragstart: [event: DragEvent]
  dragover: [event: DragEvent]
  drop: [event: DragEvent]
  dragend: [event: DragEvent]
}>()

// 缩进级别
const indentLevel = computed(() => props.level || 0)
const indentPadding = computed(() => `${indentLevel.value * 16 + 8}px`)

// 图标
const itemIcon = computed(() => {
  if (props.item.icon) return props.item.icon
  
  if (props.item.type === 'category') {
    return props.isExpanded ? 'i-lucide-folder-open' : 'i-lucide-folder'
  }
  
  switch (props.item.status) {
    case 'published':
      return 'i-lucide-file-check'
    case 'archived':
      return 'i-lucide-file-archive'
    default:
      return 'i-lucide-file-text'
  }
})

// 图标颜色
const iconColorClass = computed(() => {
  if (props.item.type === 'category') {
    return 'text-amber-500 dark:text-amber-400'
  }
  
  switch (props.item.status) {
    case 'published':
      return 'text-green-500 dark:text-green-400'
    case 'archived':
      return 'text-gray-400 dark:text-gray-500'
    default:
      return 'text-blue-500 dark:text-blue-400'
  }
})

// 处理点击
function handleClick(event: MouseEvent) {
  // 如果点击的是展开按钮区域，则切换展开状态
  const target = event.target as HTMLElement
  if (target.closest('.expand-button')) {
    emit('toggle')
  } else {
    emit('select')
  }
}

// 处理右键
function handleContextMenu(event: MouseEvent) {
  event.preventDefault()
  emit('contextmenu', event)
}

// 拖拽处理
function handleDragStart(event: DragEvent) {
  emit('dragstart', event)
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
  emit('dragover', event)
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  emit('drop', event)
}

function handleDragEnd(event: DragEvent) {
  emit('dragend', event)
}
</script>

<template>
  <div
    class="file-tree-item group"
    :class="{
      'is-selected': isSelected,
      'is-dragging': isDragging,
      'is-drop-target': isDropTarget,
    }"
    :style="{ paddingLeft: indentPadding }"
    draggable="true"
    @click="handleClick"
    @contextmenu="handleContextMenu"
    @dragstart="handleDragStart"
    @dragover="handleDragOver"
    @drop="handleDrop"
    @dragend="handleDragEnd"
  >
    <!-- 展开/折叠按钮 -->
    <button
      v-if="item.hasChildren"
      class="expand-button w-4 h-4 flex items-center justify-center shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
      @click.stop="emit('toggle')"
    >
      <UIcon
        :name="isExpanded ? 'i-lucide-chevron-down' : 'i-lucide-chevron-right'"
        class="w-3 h-3 transition-transform"
      />
    </button>
    <span v-else class="w-4 shrink-0" />

    <!-- 图标 -->
    <UIcon
      :name="itemIcon"
      class="w-4 h-4 shrink-0 transition-colors"
      :class="iconColorClass"
    />

    <!-- 标签 -->
    <span class="truncate flex-1 text-sm">
      {{ item.label }}
    </span>

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
      @click.stop="handleContextMenu($event as any)"
    />
  </div>
</template>

<style scoped>
.file-tree-item {
  @apply flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer select-none;
  @apply text-gray-700 dark:text-gray-300;
  @apply hover:bg-gray-100 dark:hover:bg-gray-800;
  @apply transition-colors duration-150;
}

.file-tree-item.is-selected {
  @apply bg-primary-100 dark:bg-primary-500/20;
  @apply text-primary-700 dark:text-primary-300;
}

.file-tree-item.is-dragging {
  @apply opacity-50;
}

.file-tree-item.is-drop-target {
  @apply bg-primary-50 dark:bg-primary-500/10;
  @apply ring-2 ring-primary-500 ring-inset;
}
</style>
