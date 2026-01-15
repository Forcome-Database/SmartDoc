<script setup lang="ts">
/**
 * Slash Command 命令列表组件
 * 显示可用命令并支持键盘导航
 */
import { ref, watch } from 'vue'

interface CommandItem {
  title: string
  description: string
  icon: string
  command: (props: any) => void
}

const props = defineProps<{
  items: CommandItem[]
  command: (item: CommandItem) => void
}>()

const selectedIndex = ref(0)

// 当命令列表变化时重置选中索引
watch(() => props.items, () => {
  selectedIndex.value = 0
})

// 选择命令
const selectItem = (index: number) => {
  const item = props.items[index]
  if (item) {
    props.command(item)
  }
}

// 键盘导航
const onKeyDown = ({ event }: { event: KeyboardEvent }) => {
  if (event.key === 'ArrowUp') {
    selectedIndex.value = (selectedIndex.value + props.items.length - 1) % props.items.length
    return true
  }
  if (event.key === 'ArrowDown') {
    selectedIndex.value = (selectedIndex.value + 1) % props.items.length
    return true
  }
  if (event.key === 'Enter') {
    selectItem(selectedIndex.value)
    return true
  }
  return false
}

// 暴露方法给父组件
defineExpose({ onKeyDown })
</script>

<template>
  <div class="slash-command-list">
    <template v-if="items.length">
      <button
        v-for="(item, index) in items"
        :key="index"
        class="slash-command-item"
        :class="{ 'is-selected': index === selectedIndex }"
        @click="selectItem(index)"
        @mouseenter="selectedIndex = index"
      >
        <div class="item-icon">
          <UIcon :name="item.icon" class="w-5 h-5" />
        </div>
        <div class="item-content">
          <div class="item-title">{{ item.title }}</div>
          <div class="item-description">{{ item.description }}</div>
        </div>
      </button>
    </template>
    <div v-else class="slash-command-empty">
      <UIcon name="i-lucide-search-x" class="w-5 h-5 text-gray-400" />
      <span>没有找到匹配的命令</span>
    </div>
  </div>
</template>

<style scoped>
@reference "tailwindcss";

.slash-command-list {
  @apply bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg overflow-hidden max-h-80 overflow-y-auto w-72;
}

.slash-command-item {
  @apply flex items-center gap-3 w-full px-3 py-2.5 text-left transition-colors duration-150;
  @apply hover:bg-gray-100 dark:hover:bg-gray-700;
}

.slash-command-item.is-selected {
  @apply bg-gray-100 dark:bg-gray-700;
}

.item-icon {
  @apply flex items-center justify-center w-8 h-8 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300;
}

.slash-command-item.is-selected .item-icon {
  background-color: color-mix(in srgb, var(--ui-primary) 15%, transparent);
  color: var(--ui-primary);
}

.item-content {
  @apply flex-1 min-w-0;
}

.item-title {
  @apply font-medium text-sm text-gray-900 dark:text-gray-100;
}

.item-description {
  @apply text-xs text-gray-500 dark:text-gray-400 truncate;
}

.slash-command-empty {
  @apply flex items-center justify-center gap-2 px-3 py-4 text-gray-500 dark:text-gray-400 text-sm;
}
</style>
