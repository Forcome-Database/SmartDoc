<script setup lang="ts">
/**
 * 内容树节点组件
 * 递归渲染树节点，支持内联编辑和拖拽排序
 */
import type { ContentNode } from './ContentTree.vue'

const props = defineProps<{
  node: ContentNode
  level: number
  expandedIds: Set<string>
  selectedId?: string | null
  editingId: string | null
  editingName: string
  editingType: 'rename' | 'new-category' | 'new-document' | null
  editingParentId: string | null
  locale: string
  dragOverId?: string | null
  dragOverPosition?: 'before' | 'after' | 'inside' | null
}>()

const emit = defineEmits<{
  click: [node: ContentNode]
  toggle: [node: ContentNode]
  createCategory: [parentId: string]
  createDocument: [categoryId: string]
  rename: [node: ContentNode]
  delete: [node: ContentNode]
  'update:editingName': [value: string]
  confirmEdit: []
  cancelEdit: []
  dragStart: [node: ContentNode]
  dragEnd: []
  dragOver: [node: ContentNode, position: 'before' | 'after' | 'inside']
  drop: [targetNode: ContentNode, position: 'before' | 'after' | 'inside']
}>()

// 输入框引用
const inputRef = ref<HTMLInputElement | null>(null)

// 计算属性
const isExpanded = computed(() => props.expandedIds.has(props.node.id))
const isSelected = computed(() => {
  const prefix = props.node.type === 'category' ? 'cat-' : 'doc-'
  return props.selectedId === `${prefix}${props.node.id}`
})
const isEditing = computed(() => props.editingType === 'rename' && props.editingId === props.node.id)
const hasChildren = computed(() => props.node.children && props.node.children.length > 0)

// 拖拽状态
const isDragOver = computed(() => props.dragOverId === props.node.id)
const dragPosition = computed(() => props.dragOverPosition)

// 缩进
const indentStyle = computed(() => ({
  paddingLeft: `${props.level * 16 + 12}px`
}))

// 获取显示名称
const displayName = computed(() => {
  if (props.node.type === 'category') {
    return props.node.titles?.[props.locale] || props.node.titles?.zh || props.node.slug
  }
  return props.node.name
})

// 获取图标
const nodeIcon = computed(() => {
  if (props.node.type === 'category') {
    return isExpanded.value ? 'i-lucide-folder-open' : 'i-lucide-folder'
  }
  switch (props.node.status) {
    case 'published': return 'i-lucide-file-check'
    case 'archived': return 'i-lucide-file-archive'
    default: return 'i-lucide-file-text'
  }
})

// 图标颜色
const iconColor = computed(() => {
  if (props.node.type === 'category') return 'text-amber-500'
  switch (props.node.status) {
    case 'published': return 'text-green-500'
    case 'archived': return 'text-gray-400'
    default: return 'text-blue-500'
  }
})

// 下拉菜单项
const dropdownItems = computed(() => {
  const items: any[][] = []
  
  // 栏目特有操作
  if (props.node.type === 'category') {
    items.push([
      {
        label: '新建子栏目',
        icon: 'i-lucide-folder-plus',
        onSelect: () => emit('createCategory', props.node.id)
      },
      {
        label: '新建文档',
        icon: 'i-lucide-file-plus',
        onSelect: () => emit('createDocument', props.node.id)
      }
    ])
  }
  
  // 通用操作
  items.push([
    {
      label: '重命名',
      icon: 'i-lucide-pencil',
      onSelect: () => emit('rename', props.node)
    }
  ])
  
  items.push([
    {
      label: '删除',
      icon: 'i-lucide-trash-2',
      color: 'error' as const,
      onSelect: () => emit('delete', props.node)
    }
  ])
  
  return items
})

// 处理点击
const handleClick = () => {
  emit('click', props.node)
}

// 处理展开/折叠
const handleToggle = (e: MouseEvent) => {
  e.stopPropagation()
  emit('toggle', props.node)
}

// 处理键盘事件
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter') {
    emit('confirmEdit')
  } else if (e.key === 'Escape') {
    emit('cancelEdit')
  }
}

// 拖拽事件处理
const handleDragStart = (e: DragEvent) => {
  if (isEditing.value) {
    e.preventDefault()
    return
  }
  e.dataTransfer?.setData('text/plain', JSON.stringify({
    id: props.node.id,
    type: props.node.type,
    parentId: props.node.parentId
  }))
  emit('dragStart', props.node)
}

const handleDragEnd = () => {
  emit('dragEnd')
}

const handleDragOver = (e: DragEvent) => {
  e.preventDefault()
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  const y = e.clientY - rect.top
  const height = rect.height
  
  let position: 'before' | 'after' | 'inside'
  if (props.node.type === 'category') {
    // 栏目：上 1/4 为 before，下 1/4 为 after，中间为 inside
    if (y < height * 0.25) {
      position = 'before'
    } else if (y > height * 0.75) {
      position = 'after'
    } else {
      position = 'inside'
    }
  } else {
    // 文档：上半为 before，下半为 after
    position = y < height / 2 ? 'before' : 'after'
  }
  
  emit('dragOver', props.node, position)
}

const handleDrop = (e: DragEvent) => {
  e.preventDefault()
  const position = dragPosition.value || 'after'
  emit('drop', props.node, position)
}

// 聚焦输入框
watch(() => props.editingId, (id) => {
  if (id === props.node.id && props.editingType === 'rename') {
    nextTick(() => {
      inputRef.value?.focus()
      inputRef.value?.select()
    })
  }
})

// 是否显示新建节点输入框
const showNewCategoryInput = computed(() => 
  props.editingType === 'new-category' && props.editingParentId === props.node.id
)
const showNewDocumentInput = computed(() => 
  props.editingType === 'new-document' && props.editingParentId === props.node.id
)
</script>

<template>
  <div class="content-tree-node">
    <!-- 节点本身 -->
    <div
      class="flex items-center gap-2 py-1.5 pr-2 cursor-pointer select-none group hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md mx-1 relative"
      :class="[
        { 'bg-primary-100 dark:bg-primary-500/20': isSelected },
        { 'opacity-50': isEditing }
      ]"
      :style="indentStyle"
      :data-node-id="`${node.type === 'category' ? 'cat' : 'doc'}-${node.id}`"
      draggable="true"
      @click="handleClick"
      @dragstart="handleDragStart"
      @dragend="handleDragEnd"
      @dragover="handleDragOver"
      @drop="handleDrop"
    >
      <!-- 拖拽指示器 -->
      <div
        v-if="isDragOver && dragPosition === 'before'"
        class="absolute left-0 right-0 top-0 h-0.5 bg-primary-500 -translate-y-0.5"
      />
      <div
        v-if="isDragOver && dragPosition === 'after'"
        class="absolute left-0 right-0 bottom-0 h-0.5 bg-primary-500 translate-y-0.5"
      />
      <div
        v-if="isDragOver && dragPosition === 'inside' && node.type === 'category'"
        class="absolute inset-0 border-2 border-primary-500 rounded-md pointer-events-none"
      />

      <!-- 展开/折叠按钮 -->
      <button
        v-if="node.type === 'category'"
        class="w-4 h-4 flex items-center justify-center shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        @click="handleToggle"
      >
        <UIcon
          :name="hasChildren || showNewCategoryInput || showNewDocumentInput ? (isExpanded ? 'i-lucide-chevron-down' : 'i-lucide-chevron-right') : 'i-lucide-chevron-right'"
          class="w-3 h-3"
          :class="{ 'opacity-0': !hasChildren && !showNewCategoryInput && !showNewDocumentInput }"
        />
      </button>
      <span v-else class="w-4 shrink-0" />

      <!-- 图标 -->
      <UIcon :name="nodeIcon" class="w-4 h-4 shrink-0" :class="iconColor" />

      <!-- 名称（编辑模式） -->
      <input
        v-if="isEditing"
        ref="inputRef"
        :value="editingName"
        type="text"
        class="flex-1 text-sm bg-transparent border border-primary-500 rounded px-2 py-0.5 outline-none min-w-0"
        @input="emit('update:editingName', ($event.target as HTMLInputElement).value)"
        @keydown="handleKeydown"
        @blur="emit('confirmEdit')"
        @click.stop
      />
      
      <!-- 名称（显示模式） -->
      <span v-else class="flex-1 text-sm truncate" :class="{ 'text-primary-600 dark:text-primary-400': isSelected }">
        {{ displayName }}
      </span>

      <!-- 状态指示器 -->
      <span
        v-if="node.type === 'document' && node.status === 'draft'"
        class="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0"
        title="草稿"
      />

      <!-- 更多操作下拉菜单 -->
      <UDropdownMenu :items="dropdownItems">
        <UButton
          variant="ghost"
          color="neutral"
          size="xs"
          icon="i-lucide-more-horizontal"
          class="opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
          @click.stop
        />
      </UDropdownMenu>
    </div>

    <!-- 子节点 -->
    <div v-if="node.type === 'category' && isExpanded" class="children">
      <!-- 递归渲染子节点 -->
      <ContentTreeNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :level="level + 1"
        :expanded-ids="expandedIds"
        :selected-id="selectedId"
        :editing-id="editingId"
        :editing-name="editingName"
        :editing-type="editingType"
        :editing-parent-id="editingParentId"
        :locale="locale"
        :drag-over-id="dragOverId"
        :drag-over-position="dragOverPosition"
        @click="emit('click', $event)"
        @toggle="emit('toggle', $event)"
        @create-category="emit('createCategory', $event)"
        @create-document="emit('createDocument', $event)"
        @rename="emit('rename', $event)"
        @delete="emit('delete', $event)"
        @update:editing-name="emit('update:editingName', $event)"
        @confirm-edit="emit('confirmEdit')"
        @cancel-edit="emit('cancelEdit')"
        @drag-start="emit('dragStart', $event)"
        @drag-end="emit('dragEnd')"
        @drag-over="emit('dragOver', $event, arguments[1])"
        @drop="emit('drop', $event, arguments[1])"
      />

      <!-- 新建栏目输入框 -->
      <div
        v-if="showNewCategoryInput"
        class="flex items-center gap-2 py-1.5 pr-2 mx-1"
        :style="{ paddingLeft: `${(level + 1) * 16 + 12}px` }"
      >
        <span class="w-4 shrink-0" />
        <UIcon name="i-lucide-folder" class="w-4 h-4 text-amber-500 shrink-0" />
        <input
          :value="editingName"
          type="text"
          class="flex-1 text-sm bg-transparent border border-primary-500 rounded px-2 py-0.5 outline-none min-w-0"
          placeholder="栏目名称"
          autofocus
          @input="emit('update:editingName', ($event.target as HTMLInputElement).value)"
          @keydown="handleKeydown"
          @blur="emit('confirmEdit')"
        />
      </div>

      <!-- 新建文档输入框 -->
      <div
        v-if="showNewDocumentInput"
        class="flex items-center gap-2 py-1.5 pr-2 mx-1"
        :style="{ paddingLeft: `${(level + 1) * 16 + 12}px` }"
      >
        <span class="w-4 shrink-0" />
        <UIcon name="i-lucide-file-text" class="w-4 h-4 text-blue-500 shrink-0" />
        <input
          :value="editingName"
          type="text"
          class="flex-1 text-sm bg-transparent border border-primary-500 rounded px-2 py-0.5 outline-none min-w-0"
          placeholder="文档标题"
          autofocus
          @input="emit('update:editingName', ($event.target as HTMLInputElement).value)"
          @keydown="handleKeydown"
          @blur="emit('confirmEdit')"
        />
      </div>
    </div>
  </div>
</template>
