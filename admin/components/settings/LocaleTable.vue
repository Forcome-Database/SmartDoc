<script setup lang="ts">
/**
 * 语言列表表格组件
 * 支持拖拽排序、启用/禁用切换、编辑/删除操作
 * 
 * Requirements: 6.9
 */
import type { Locale } from '~/types'

const props = defineProps<{
  locales: Locale[]
}>()

const emit = defineEmits<{
  edit: [locale: Locale]
  delete: [locale: Locale]
  toggleEnabled: [locale: Locale]
  reorder: [ids: string[]]
}>()

// 本地排序列表（用于拖拽）
const sortedLocales = ref<Locale[]>([])

// 同步 props 到本地状态
watch(() => props.locales, (newLocales) => {
  sortedLocales.value = [...newLocales]
}, { immediate: true })

// 拖拽状态
const draggedIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)

// 开始拖拽
const handleDragStart = (index: number) => {
  draggedIndex.value = index
}

// 拖拽经过
const handleDragOver = (e: DragEvent, index: number) => {
  e.preventDefault()
  dragOverIndex.value = index
}

// 拖拽离开
const handleDragLeave = () => {
  dragOverIndex.value = null
}

// 放置
const handleDrop = (targetIndex: number) => {
  if (draggedIndex.value === null || draggedIndex.value === targetIndex) {
    draggedIndex.value = null
    dragOverIndex.value = null
    return
  }

  // 重新排序
  const newList = [...sortedLocales.value]
  const [removed] = newList.splice(draggedIndex.value, 1)
  newList.splice(targetIndex, 0, removed)
  
  sortedLocales.value = newList
  
  // 发送新顺序
  emit('reorder', newList.map(l => l.id))
  
  draggedIndex.value = null
  dragOverIndex.value = null
}

// 拖拽结束
const handleDragEnd = () => {
  draggedIndex.value = null
  dragOverIndex.value = null
}
</script>

<template>
  <div class="overflow-x-auto">
    <table class="w-full">
      <thead>
        <tr class="border-b border-gray-100 dark:border-gray-800">
          <th class="w-10 px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            <!-- 拖拽手柄列 -->
          </th>
          <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            语言代码
          </th>
          <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            名称
          </th>
          <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            本地名称
          </th>
          <th class="px-4 py-3 text-center text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            状态
          </th>
          <th class="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            操作
          </th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
        <tr
          v-for="(locale, index) in sortedLocales"
          :key="locale.id"
          draggable="true"
          class="group transition-colors"
          :class="{
            'bg-primary-50 dark:bg-primary-500/10': dragOverIndex === index,
            'opacity-50': draggedIndex === index,
          }"
          @dragstart="handleDragStart(index)"
          @dragover="handleDragOver($event, index)"
          @dragleave="handleDragLeave"
          @drop="handleDrop(index)"
          @dragend="handleDragEnd"
        >
          <!-- 拖拽手柄 -->
          <td class="px-4 py-4">
            <div class="cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
              <UIcon name="i-lucide-grip-vertical" class="w-4 h-4" />
            </div>
          </td>
          
          <!-- 语言代码 -->
          <td class="px-4 py-4">
            <div class="flex items-center gap-2">
              <code class="px-2 py-1 text-sm font-mono bg-gray-100 dark:bg-gray-800 rounded">
                {{ locale.code }}
              </code>
              <span
                v-if="locale.isDefault"
                class="px-2 py-0.5 text-xs font-medium bg-primary-100 text-primary-700 dark:bg-primary-500/20 dark:text-primary-400 rounded-full"
              >
                默认
              </span>
            </div>
          </td>
          
          <!-- 名称 -->
          <td class="px-4 py-4 text-sm text-gray-900 dark:text-white">
            {{ locale.name }}
          </td>
          
          <!-- 本地名称 -->
          <td class="px-4 py-4 text-sm text-gray-500 dark:text-gray-400">
            {{ locale.nativeName }}
          </td>
          
          <!-- 状态 -->
          <td class="px-4 py-4 text-center">
            <USwitch
              :model-value="locale.isEnabled"
              size="sm"
              @update:model-value="emit('toggleEnabled', locale)"
            />
          </td>
          
          <!-- 操作 -->
          <td class="px-4 py-4 text-right">
            <div class="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <UButton
                variant="ghost"
                color="neutral"
                size="xs"
                icon="i-lucide-pencil"
                @click="emit('edit', locale)"
              />
              <UButton
                variant="ghost"
                color="error"
                size="xs"
                icon="i-lucide-trash-2"
                :disabled="locale.isDefault"
                @click="emit('delete', locale)"
              />
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
