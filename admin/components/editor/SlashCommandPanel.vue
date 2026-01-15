<script setup lang="ts">
/**
 * Slash 命令面板
 * 类似 Notion 的 "/" 指令插入内容
 */

export interface SlashCommand {
  id: string
  label: string
  description: string
  icon: string
  keywords: string[]
  action: () => string // 返回要插入的内容
}

const props = defineProps<{
  visible: boolean
  position: { x: number; y: number }
  searchQuery: string
}>()

const emit = defineEmits<{
  select: [command: SlashCommand]
  close: []
}>()

// 命令列表
const commands: SlashCommand[] = [
  {
    id: 'heading1',
    label: '一级标题',
    description: '大标题',
    icon: 'i-lucide-heading-1',
    keywords: ['h1', 'heading', '标题', '一级'],
    action: () => '# ',
  },
  {
    id: 'heading2',
    label: '二级标题',
    description: '中等标题',
    icon: 'i-lucide-heading-2',
    keywords: ['h2', 'heading', '标题', '二级'],
    action: () => '## ',
  },
  {
    id: 'heading3',
    label: '三级标题',
    description: '小标题',
    icon: 'i-lucide-heading-3',
    keywords: ['h3', 'heading', '标题', '三级'],
    action: () => '### ',
  },
  {
    id: 'bold',
    label: '粗体',
    description: '加粗文本',
    icon: 'i-lucide-bold',
    keywords: ['bold', '粗体', '加粗'],
    action: () => '**粗体文本**',
  },
  {
    id: 'italic',
    label: '斜体',
    description: '倾斜文本',
    icon: 'i-lucide-italic',
    keywords: ['italic', '斜体'],
    action: () => '*斜体文本*',
  },
  {
    id: 'code',
    label: '代码块',
    description: '插入代码块',
    icon: 'i-lucide-code',
    keywords: ['code', '代码', 'codeblock'],
    action: () => '\n```javascript\n// 代码\n```\n',
  },
  {
    id: 'quote',
    label: '引用',
    description: '插入引用块',
    icon: 'i-lucide-quote',
    keywords: ['quote', '引用', 'blockquote'],
    action: () => '> ',
  },
  {
    id: 'list',
    label: '无序列表',
    description: '创建列表',
    icon: 'i-lucide-list',
    keywords: ['list', '列表', 'ul'],
    action: () => '- ',
  },
  {
    id: 'ordered-list',
    label: '有序列表',
    description: '创建编号列表',
    icon: 'i-lucide-list-ordered',
    keywords: ['ordered', '有序', '编号', 'ol'],
    action: () => '1. ',
  },
  {
    id: 'task',
    label: '任务列表',
    description: '创建待办事项',
    icon: 'i-lucide-check-square',
    keywords: ['task', 'todo', '任务', '待办'],
    action: () => '- [ ] ',
  },
  {
    id: 'table',
    label: '表格',
    description: '插入表格',
    icon: 'i-lucide-table',
    keywords: ['table', '表格'],
    action: () => '\n| 列1 | 列2 | 列3 |\n| --- | --- | --- |\n| 内容 | 内容 | 内容 |\n',
  },
  {
    id: 'link',
    label: '链接',
    description: '插入超链接',
    icon: 'i-lucide-link',
    keywords: ['link', '链接', 'url'],
    action: () => '[链接文本](https://example.com)',
  },
  {
    id: 'image',
    label: '图片',
    description: '插入图片',
    icon: 'i-lucide-image',
    keywords: ['image', '图片', 'img'],
    action: () => '![图片描述](https://example.com/image.png)',
  },
  {
    id: 'divider',
    label: '分割线',
    description: '插入水平分割线',
    icon: 'i-lucide-minus',
    keywords: ['divider', 'hr', '分割线'],
    action: () => '\n---\n',
  },
  {
    id: 'callout-info',
    label: '提示框 - 信息',
    description: '插入信息提示框',
    icon: 'i-lucide-info',
    keywords: ['callout', 'info', '提示', '信息'],
    action: () => '\n> [!NOTE]\n> 这是一条信息提示\n',
  },
  {
    id: 'callout-warning',
    label: '提示框 - 警告',
    description: '插入警告提示框',
    icon: 'i-lucide-alert-triangle',
    keywords: ['callout', 'warning', '警告'],
    action: () => '\n> [!WARNING]\n> 这是一条警告信息\n',
  },
  {
    id: 'callout-tip',
    label: '提示框 - 技巧',
    description: '插入技巧提示框',
    icon: 'i-lucide-lightbulb',
    keywords: ['callout', 'tip', '技巧', '提示'],
    action: () => '\n> [!TIP]\n> 这是一条技巧提示\n',
  },
]

// 过滤命令
const filteredCommands = computed(() => {
  const query = props.searchQuery.toLowerCase().trim()
  if (!query) return commands
  
  return commands.filter(cmd => {
    return (
      cmd.label.toLowerCase().includes(query) ||
      cmd.description.toLowerCase().includes(query) ||
      cmd.keywords.some(k => k.toLowerCase().includes(query))
    )
  })
})

// 选中的命令索引
const selectedIndex = ref(0)

// 监听搜索变化，重置选中索引
watch(() => props.searchQuery, () => {
  selectedIndex.value = 0
})

// 监听可见性变化，重置选中索引
watch(() => props.visible, (visible) => {
  if (visible) {
    selectedIndex.value = 0
  }
})

// 键盘导航
const handleKeydown = (e: KeyboardEvent) => {
  if (!props.visible) return
  
  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault()
      selectedIndex.value = Math.min(selectedIndex.value + 1, filteredCommands.value.length - 1)
      break
    case 'ArrowUp':
      e.preventDefault()
      selectedIndex.value = Math.max(selectedIndex.value - 1, 0)
      break
    case 'Enter':
      e.preventDefault()
      if (filteredCommands.value[selectedIndex.value]) {
        emit('select', filteredCommands.value[selectedIndex.value])
      }
      break
    case 'Escape':
      e.preventDefault()
      emit('close')
      break
  }
}

// 选择命令
const selectCommand = (command: SlashCommand) => {
  emit('select', command)
}

// 挂载键盘事件
onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="slash-command-panel"
      :style="{
        position: 'fixed',
        left: `${position.x}px`,
        top: `${position.y}px`,
        zIndex: 9999,
      }"
    >
      <div class="panel-container">
        <!-- 搜索提示 -->
        <div v-if="searchQuery" class="search-hint">
          搜索: {{ searchQuery }}
        </div>
        
        <!-- 命令列表 -->
        <div v-if="filteredCommands.length > 0" class="command-list">
          <button
            v-for="(command, index) in filteredCommands"
            :key="command.id"
            :class="['command-item', { selected: index === selectedIndex }]"
            @click="selectCommand(command)"
            @mouseenter="selectedIndex = index"
          >
            <UIcon :name="command.icon" class="command-icon" />
            <div class="command-content">
              <div class="command-label">{{ command.label }}</div>
              <div class="command-description">{{ command.description }}</div>
            </div>
          </button>
        </div>
        
        <!-- 无结果 -->
        <div v-else class="no-results">
          <UIcon name="i-lucide-search-x" class="w-8 h-8 text-gray-400" />
          <p class="mt-2 text-sm text-gray-500">未找到匹配的命令</p>
        </div>
        
        <!-- 提示 -->
        <div class="panel-footer">
          <span class="text-xs text-gray-400">
            <kbd>↑</kbd> <kbd>↓</kbd> 导航 · <kbd>Enter</kbd> 选择 · <kbd>Esc</kbd> 关闭
          </span>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
@reference "tailwindcss";

.slash-command-panel {
  @apply pointer-events-auto;
}

.panel-container {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700;
  @apply w-80 max-h-96 overflow-hidden;
  @apply flex flex-col;
}

.search-hint {
  @apply px-3 py-2 text-xs text-gray-500 border-b border-gray-200 dark:border-gray-700;
}

.command-list {
  @apply overflow-y-auto flex-1;
  @apply py-1;
}

.command-item {
  @apply w-full px-3 py-2 flex items-start gap-3;
  @apply text-left transition-colors duration-150;
  @apply hover:bg-gray-100 dark:hover:bg-gray-700;
  @apply cursor-pointer;
}

.command-item.selected {
  @apply bg-blue-50 dark:bg-blue-900/20;
}

.command-icon {
  @apply w-5 h-5 flex-shrink-0 mt-0.5;
  @apply text-gray-600 dark:text-gray-400;
}

.command-item.selected .command-icon {
  @apply text-blue-600 dark:text-blue-400;
}

.command-content {
  @apply flex-1 min-w-0;
}

.command-label {
  @apply text-sm font-medium text-gray-900 dark:text-white;
}

.command-description {
  @apply text-xs text-gray-500 dark:text-gray-400 mt-0.5;
}

.no-results {
  @apply flex flex-col items-center justify-center py-8;
}

.panel-footer {
  @apply px-3 py-2 border-t border-gray-200 dark:border-gray-700;
  @apply bg-gray-50 dark:bg-gray-900/50;
}

kbd {
  @apply inline-block px-1.5 py-0.5 text-xs;
  @apply bg-gray-200 dark:bg-gray-700 rounded;
  @apply border border-gray-300 dark:border-gray-600;
  @apply font-mono;
}
</style>
