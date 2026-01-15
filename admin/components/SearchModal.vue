<script setup lang="ts">
import { useDebounceFn } from '@vueuse/core'

/**
 * 搜索模态框组件
 * 支持 Ctrl+K / Cmd+K 快捷键触发
 * 实现实时搜索和键盘导航
 * 
 * Requirements: 9.1, 9.2, 9.4, 9.5, 9.6
 */

// 搜索结果类型
interface SearchResult {
  id: string
  title: string
  slug: string
  status: 'draft' | 'published' | 'archived'
  highlight: string
  matchedIn: {
    title: boolean
    slug: boolean
    content: boolean
  }
  author: {
    id: string
    name: string
    avatar: string | null
  } | null
  locale: {
    id: string
    code: string
    name: string
  } | null
  category: {
    id: string
    slug: string
    titles: Record<string, string>
  } | null
  updatedAt: string
}

interface SearchResponse {
  query: string
  items: SearchResult[]
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
}

// 模态框状态
const isOpen = defineModel<boolean>('open', { default: false })

// 搜索状态
const searchQuery = ref('')
const searchResults = ref<SearchResult[]>([])
const isLoading = ref(false)
const selectedIndex = ref(0)
const totalResults = ref(0)

// 搜索输入框引用
const searchInputRef = ref<HTMLInputElement | null>(null)

// 防抖搜索
const debouncedSearch = useDebounceFn(async (query: string) => {
  if (!query.trim()) {
    searchResults.value = []
    totalResults.value = 0
    isLoading.value = false
    return
  }

  try {
    const response = await $fetch<SearchResponse>('/api/documents/search', {
      query: {
        q: query,
        limit: 10,
      },
    })
    searchResults.value = response.items
    totalResults.value = response.pagination.total
    selectedIndex.value = 0
  } catch (error) {
    console.error('搜索失败:', error)
    searchResults.value = []
    totalResults.value = 0
  } finally {
    isLoading.value = false
  }
}, 300)

// 监听搜索输入
watch(searchQuery, (newQuery) => {
  isLoading.value = true
  selectedIndex.value = 0
  debouncedSearch(newQuery)
})

// 打开模态框时聚焦输入框
watch(isOpen, (open) => {
  if (open) {
    nextTick(() => {
      searchInputRef.value?.focus()
    })
  } else {
    // 关闭时重置状态
    searchQuery.value = ''
    searchResults.value = []
    selectedIndex.value = 0
    totalResults.value = 0
  }
})

// 键盘导航
const handleKeydown = (event: KeyboardEvent) => {
  if (!isOpen.value) return

  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault()
      if (searchResults.value.length > 0) {
        selectedIndex.value = (selectedIndex.value + 1) % searchResults.value.length
      }
      break
    case 'ArrowUp':
      event.preventDefault()
      if (searchResults.value.length > 0) {
        selectedIndex.value = selectedIndex.value === 0 
          ? searchResults.value.length - 1 
          : selectedIndex.value - 1
      }
      break
    case 'Enter':
      event.preventDefault()
      if (searchResults.value.length > 0 && searchResults.value[selectedIndex.value]) {
        navigateToDocument(searchResults.value[selectedIndex.value])
      }
      break
    case 'Escape':
      event.preventDefault()
      isOpen.value = false
      break
  }
}

// 导航到文档
const navigateToDocument = (result: SearchResult) => {
  isOpen.value = false
  navigateTo(`/documents/${result.id}`)
}

// 全局快捷键 Ctrl+K / Cmd+K
defineShortcuts({
  meta_k: () => {
    isOpen.value = !isOpen.value
  },
  ctrl_k: () => {
    isOpen.value = !isOpen.value
  },
})

// 格式化更新时间
const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  if (hours < 24) return `${hours} 小时前`
  if (days < 7) return `${days} 天前`
  return date.toLocaleDateString('zh-CN')
}

// 获取状态标签
const getStatusLabel = (status: string) => {
  const labels: Record<string, { text: string; color: string }> = {
    draft: { text: '草稿', color: 'text-yellow-600 dark:text-yellow-400' },
    published: { text: '已发布', color: 'text-green-600 dark:text-green-400' },
    archived: { text: '已归档', color: 'text-gray-500 dark:text-gray-400' },
  }
  return labels[status] || { text: status, color: 'text-gray-500' }
}

// 高亮搜索关键词
const highlightText = (text: string, query: string) => {
  if (!query.trim()) return text
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  return text.replace(regex, '<mark class="bg-yellow-200 dark:bg-yellow-800 text-inherit rounded px-0.5">$1</mark>')
}
</script>

<template>
  <UModal 
    v-model:open="isOpen" 
    :ui="{
      width: 'sm:max-w-xl',
    }"
    @keydown="handleKeydown"
  >
    <template #content>
      <div class="flex flex-col max-h-[70vh]">
      <!-- 搜索输入框 -->
      <div class="flex items-center gap-3 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <UIcon 
          name="i-lucide-search" 
          class="w-5 h-5 text-gray-400 flex-shrink-0" 
        />
        <input
          ref="searchInputRef"
          v-model="searchQuery"
          type="text"
          placeholder="搜索文档..."
          class="flex-1 bg-transparent border-none outline-none text-gray-900 dark:text-white placeholder-gray-400 text-base"
        />
        <div v-if="isLoading" class="flex-shrink-0">
          <UIcon 
            name="i-lucide-loader-2" 
            class="w-4 h-4 text-gray-400 animate-spin" 
          />
        </div>
        <kbd 
          v-else
          class="hidden sm:inline-flex items-center px-1.5 py-0.5 text-xs font-medium text-gray-400 bg-gray-100 dark:bg-gray-800 rounded"
        >
          ESC
        </kbd>
      </div>

      <!-- 搜索结果 -->
      <div class="flex-1 overflow-y-auto">
        <!-- 加载状态 -->
        <div 
          v-if="isLoading && searchQuery.trim()" 
          class="flex items-center justify-center py-12"
        >
          <UIcon 
            name="i-lucide-loader-2" 
            class="w-6 h-6 text-gray-400 animate-spin" 
          />
        </div>

        <!-- 无搜索词提示 -->
        <div 
          v-else-if="!searchQuery.trim()" 
          class="flex flex-col items-center justify-center py-12 text-gray-500 dark:text-gray-400"
        >
          <UIcon name="i-lucide-file-search" class="w-12 h-12 mb-3 opacity-50" />
          <p class="text-sm">输入关键词搜索文档</p>
          <p class="text-xs mt-1 opacity-75">支持搜索标题、内容和路径</p>
        </div>

        <!-- 无结果提示 -->
        <div 
          v-else-if="searchResults.length === 0 && !isLoading" 
          class="flex flex-col items-center justify-center py-12 text-gray-500 dark:text-gray-400"
        >
          <UIcon name="i-lucide-search-x" class="w-12 h-12 mb-3 opacity-50" />
          <p class="text-sm">未找到相关文档</p>
          <p class="text-xs mt-1 opacity-75">尝试使用其他关键词</p>
        </div>

        <!-- 搜索结果列表 -->
        <div v-else class="py-2">
          <div 
            v-if="totalResults > 0" 
            class="px-4 py-1.5 text-xs text-gray-500 dark:text-gray-400"
          >
            找到 {{ totalResults }} 个结果
          </div>
          
          <button
            v-for="(result, index) in searchResults"
            :key="result.id"
            class="w-full px-4 py-3 flex items-start gap-3 text-left transition-colors"
            :class="[
              index === selectedIndex 
                ? 'bg-primary-50 dark:bg-primary-900/20' 
                : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
            ]"
            @click="navigateToDocument(result)"
            @mouseenter="selectedIndex = index"
          >
            <!-- 文档图标 -->
            <div 
              class="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center"
              :class="[
                index === selectedIndex 
                  ? 'bg-primary-100 dark:bg-primary-800/50' 
                  : 'bg-gray-100 dark:bg-gray-800'
              ]"
            >
              <UIcon 
                name="i-lucide-file-text" 
                class="w-4 h-4"
                :class="[
                  index === selectedIndex 
                    ? 'text-primary-600 dark:text-primary-400' 
                    : 'text-gray-500 dark:text-gray-400'
                ]"
              />
            </div>

            <!-- 文档信息 -->
            <div class="flex-1 min-w-0">
              <!-- 标题 -->
              <div class="flex items-center gap-2">
                <span 
                  class="font-medium text-gray-900 dark:text-white truncate"
                  v-html="highlightText(result.title, searchQuery)"
                />
                <span 
                  class="text-xs flex-shrink-0"
                  :class="getStatusLabel(result.status).color"
                >
                  {{ getStatusLabel(result.status).text }}
                </span>
              </div>

              <!-- 路径和摘要 -->
              <div class="mt-1 text-sm text-gray-500 dark:text-gray-400 truncate">
                <span v-if="result.category" class="text-gray-400 dark:text-gray-500">
                  {{ result.category.titles['zh'] || result.category.slug }} /
                </span>
                <span v-html="highlightText(result.highlight, searchQuery)" />
              </div>

              <!-- 元信息 -->
              <div class="mt-1.5 flex items-center gap-3 text-xs text-gray-400 dark:text-gray-500">
                <span v-if="result.locale" class="flex items-center gap-1">
                  <UIcon name="i-lucide-globe" class="w-3 h-3" />
                  {{ result.locale.name }}
                </span>
                <span v-if="result.author" class="flex items-center gap-1">
                  <UIcon name="i-lucide-user" class="w-3 h-3" />
                  {{ result.author.name }}
                </span>
                <span class="flex items-center gap-1">
                  <UIcon name="i-lucide-clock" class="w-3 h-3" />
                  {{ formatTime(result.updatedAt) }}
                </span>
              </div>
            </div>

            <!-- 回车提示 -->
            <div 
              v-if="index === selectedIndex"
              class="flex-shrink-0 self-center"
            >
              <kbd class="inline-flex items-center px-1.5 py-0.5 text-xs font-medium text-gray-400 bg-gray-100 dark:bg-gray-700 rounded">
                ↵
              </kbd>
            </div>
          </button>
        </div>
      </div>

      <!-- 底部提示 -->
      <div class="flex items-center justify-between px-4 py-2 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-400 dark:text-gray-500">
        <div class="flex items-center gap-3">
          <span class="flex items-center gap-1">
            <kbd class="px-1 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">↑</kbd>
            <kbd class="px-1 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">↓</kbd>
            导航
          </span>
          <span class="flex items-center gap-1">
            <kbd class="px-1 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">↵</kbd>
            打开
          </span>
          <span class="flex items-center gap-1">
            <kbd class="px-1 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">ESC</kbd>
            关闭
          </span>
        </div>
      </div>
      </div>
    </template>
  </UModal>
</template>
