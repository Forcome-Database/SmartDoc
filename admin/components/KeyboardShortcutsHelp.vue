<script setup lang="ts">
/**
 * 快捷键帮助对话框
 * 显示所有可用的快捷键
 * 
 * Requirements: 8.5
 */
import { getModifierKey } from '~/composables/useKeyboardShortcuts'

// 模态框状态
const isOpen = defineModel<boolean>('open', { default: false })

// 获取修饰键
const modifierKey = getModifierKey()

// 快捷键分组
const shortcutGroups = [
  {
    title: '通用',
    shortcuts: [
      { keys: [modifierKey, 'K'], description: '打开搜索' },
      { keys: [modifierKey, 'S'], description: '保存文档' },
      { keys: ['ESC'], description: '关闭对话框/面板' },
    ],
  },
  {
    title: '导航',
    shortcuts: [
      { keys: ['↑', '↓'], description: '在列表中导航' },
      { keys: ['Enter'], description: '确认选择' },
    ],
  },
  {
    title: '编辑器',
    shortcuts: [
      { keys: ['/'], description: '打开命令菜单' },
      { keys: [modifierKey, 'B'], description: '加粗' },
      { keys: [modifierKey, 'I'], description: '斜体' },
      { keys: [modifierKey, 'U'], description: '下划线' },
      { keys: [modifierKey, 'Shift', 'S'], description: '删除线' },
      { keys: [modifierKey, 'E'], description: '行内代码' },
      { keys: [modifierKey, 'K'], description: '插入链接' },
    ],
  },
]

// 全局快捷键 ? 打开帮助
defineShortcuts({
  'shift_/': () => {
    isOpen.value = !isOpen.value
  },
})
</script>

<template>
  <UModal 
    v-model:open="isOpen"
    :ui="{
      width: 'sm:max-w-lg',
    }"
  >
    <template #header>
      <div class="flex items-center gap-2">
        <UIcon name="i-lucide-keyboard" class="w-5 h-5 text-primary-500" />
        <span class="font-semibold">快捷键</span>
      </div>
    </template>

    <template #body>
      <div class="space-y-6">
        <div 
          v-for="group in shortcutGroups" 
          :key="group.title"
          class="space-y-2"
        >
          <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">
            {{ group.title }}
          </h3>
          <div class="space-y-1">
            <div 
              v-for="shortcut in group.shortcuts" 
              :key="shortcut.description"
              class="flex items-center justify-between py-1.5 px-2 rounded hover:bg-gray-50 dark:hover:bg-gray-800/50"
            >
              <span class="text-sm text-gray-700 dark:text-gray-300">
                {{ shortcut.description }}
              </span>
              <div class="flex items-center gap-1">
                <kbd 
                  v-for="(key, index) in shortcut.keys" 
                  :key="index"
                  class="inline-flex items-center justify-center min-w-[24px] h-6 px-1.5 text-xs font-medium text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded shadow-sm"
                >
                  {{ key }}
                </kbd>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
        <span class="flex items-center gap-1">
          按 
          <kbd class="px-1 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">?</kbd>
          打开此帮助
        </span>
        <UButton 
          variant="ghost" 
          size="xs"
          @click="isOpen = false"
        >
          关闭
        </UButton>
      </div>
    </template>
  </UModal>
</template>
