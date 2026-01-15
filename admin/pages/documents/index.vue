<script setup lang="ts">
import { useDebounceFn } from '@vueuse/core'

/**
 * 文档列表页面
 * 展示所有文档，支持搜索、筛选和排序
 */

definePageMeta({
  layout: 'default',
})

// 文档类型
interface Document {
  id: string
  title: string
  slug: string
  status: 'draft' | 'published' | 'archived'
  author: { id: string; name: string; avatar: string | null } | null
  locale: { id: string; code: string; name: string } | null
  category: { id: string; slug: string; titles: Record<string, string> } | null
  createdAt: string
  updatedAt: string
}

interface DocumentsResponse {
  items: Document[]
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
}

// 状态
const searchQuery = ref('')
const statusFilter = ref<string>('')
const currentPage = ref(1)
const pageSize = ref(20)
const showCreateDialog = ref(false)
const isCreating = ref(false)

// 新建文档表单
const newDoc = ref({
  title: '',
  slug: '',
  categoryId: '',
  localeId: '',
})

// 获取栏目列表
const { data: categories } = await useFetch<any[]>('/api/categories')

// 获取语言列表
const { data: locales } = await useFetch<any[]>('/api/locales')

// 获取文档列表
const { data, pending, refresh } = await useFetch<DocumentsResponse>('/api/documents', {
  query: computed(() => ({
    q: searchQuery.value || undefined,
    status: statusFilter.value || undefined,
    page: currentPage.value,
    limit: pageSize.value,
  })),
})

// 状态选项
const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '草稿', value: 'draft' },
  { label: '已发布', value: 'published' },
  { label: '已归档', value: 'archived' },
]

// 状态标签样式
const getStatusBadge = (status: string) => {
  const styles: Record<string, { color: string; label: string }> = {
    draft: { color: 'warning', label: '草稿' },
    published: { color: 'success', label: '已发布' },
    archived: { color: 'neutral', label: '已归档' },
  }
  return styles[status] || { color: 'neutral', label: status }
}

// 格式化时间
const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 导航到文档
const goToDocument = (id: string) => {
  navigateTo(`/documents/${id}`)
}

// 搜索防抖
const debouncedSearch = useDebounceFn(() => {
  currentPage.value = 1
  refresh()
}, 300)

watch(searchQuery, () => debouncedSearch())
watch(statusFilter, () => {
  currentPage.value = 1
  refresh()
})

// 自动生成 slug
watch(() => newDoc.value.title, (title) => {
  if (title && !newDoc.value.slug) {
    newDoc.value.slug = title
      .toLowerCase()
      .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-')
      .replace(/^-|-$/g, '')
  }
})

// 创建文档
const createDocument = async () => {
  if (!newDoc.value.title.trim()) return
  
  isCreating.value = true
  try {
    const doc = await $fetch<{ id: string }>('/api/documents', {
      method: 'POST',
      body: {
        title: newDoc.value.title,
        slug: newDoc.value.slug || newDoc.value.title.toLowerCase().replace(/\s+/g, '-'),
        categoryId: newDoc.value.categoryId || undefined,
        localeId: newDoc.value.localeId || undefined,
        content: '',
      },
    })
    
    showCreateDialog.value = false
    newDoc.value = { title: '', slug: '', categoryId: '', localeId: '' }
    
    // 跳转到新文档
    navigateTo(`/documents/${doc.id}`)
  } catch (error: any) {
    console.error('创建文档失败:', error)
    alert(error.data?.message || '创建文档失败')
  } finally {
    isCreating.value = false
  }
}

// 栏目选项
const categoryOptions = computed(() => {
  if (!categories.value) return []
  return categories.value.map((c: any) => ({
    label: c.titles?.zh || c.slug,
    value: c.id,
  }))
})

// 语言选项
const localeOptions = computed(() => {
  if (!locales.value) return []
  return locales.value.map((l: any) => ({
    label: l.name,
    value: l.id,
  }))
})
</script>

<template>
  <div class="p-6 max-w-7xl mx-auto">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-semibold text-gray-900 dark:text-white">文档管理</h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          查看和管理所有文档
        </p>
      </div>
      <UButton
        icon="i-lucide-plus"
        @click="showCreateDialog = true"
      >
        新建文档
      </UButton>
    </div>

    <!-- 筛选栏 -->
    <div class="flex flex-col sm:flex-row gap-4 mb-6">
      <UInput
        v-model="searchQuery"
        placeholder="搜索文档..."
        icon="i-lucide-search"
        class="flex-1"
      />
      <USelectMenu
        v-model="statusFilter"
        :items="statusOptions"
        value-key="value"
        class="w-40"
      />
    </div>

    <!-- 加载状态 -->
    <div v-if="pending" class="flex items-center justify-center py-12">
      <UIcon name="i-lucide-loader-2" class="w-8 h-8 text-gray-400 animate-spin" />
    </div>

    <!-- 空状态 -->
    <div
      v-else-if="!data?.items?.length"
      class="flex flex-col items-center justify-center py-16 text-gray-500 dark:text-gray-400"
    >
      <UIcon name="i-lucide-file-x" class="w-16 h-16 mb-4 opacity-50" />
      <p class="text-lg font-medium">暂无文档</p>
      <p class="text-sm mt-2 mb-4">点击下方按钮创建第一篇文档</p>
      <UButton icon="i-lucide-plus" @click="showCreateDialog = true">
        新建文档
      </UButton>
    </div>

    <!-- 文档列表 -->
    <div v-else class="space-y-3">
      <div
        v-for="doc in data.items"
        :key="doc.id"
        class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:border-primary-300 dark:hover:border-primary-700 transition-colors cursor-pointer"
        @click="goToDocument(doc.id)"
      >
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1 min-w-0">
            <!-- 标题和状态 -->
            <div class="flex items-center gap-2">
              <h3 class="font-medium text-gray-900 dark:text-white truncate">
                {{ doc.title }}
              </h3>
              <UBadge :color="getStatusBadge(doc.status).color as any" size="xs">
                {{ getStatusBadge(doc.status).label }}
              </UBadge>
            </div>

            <!-- 路径 -->
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400 truncate">
              <span v-if="doc.category">
                {{ doc.category.titles['zh'] || doc.category.slug }} /
              </span>
              {{ doc.slug }}
            </p>

            <!-- 元信息 -->
            <div class="mt-2 flex items-center gap-4 text-xs text-gray-400 dark:text-gray-500">
              <span v-if="doc.locale" class="flex items-center gap-1">
                <UIcon name="i-lucide-globe" class="w-3 h-3" />
                {{ doc.locale.name }}
              </span>
              <span v-if="doc.author" class="flex items-center gap-1">
                <UIcon name="i-lucide-user" class="w-3 h-3" />
                {{ doc.author.name }}
              </span>
              <span class="flex items-center gap-1">
                <UIcon name="i-lucide-clock" class="w-3 h-3" />
                {{ formatTime(doc.updatedAt) }}
              </span>
            </div>
          </div>

          <UIcon name="i-lucide-chevron-right" class="w-5 h-5 text-gray-400 flex-shrink-0" />
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div
      v-if="data?.pagination && data.pagination.totalPages > 1"
      class="mt-6 flex items-center justify-between"
    >
      <p class="text-sm text-gray-500 dark:text-gray-400">
        共 {{ data.pagination.total }} 条记录
      </p>
      <UPagination
        v-model="currentPage"
        :total="data.pagination.total"
        :page-count="pageSize"
      />
    </div>

    <!-- 新建文档对话框 -->
    <UModal v-model:open="showCreateDialog">
      <template #content>
        <div class="p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            新建文档
          </h3>
          
          <div class="space-y-4">
            <UFormField label="标题" required>
              <UInput
                v-model="newDoc.title"
                placeholder="输入文档标题"
                autofocus
              />
            </UFormField>

            <UFormField label="路径 (slug)">
              <UInput
                v-model="newDoc.slug"
                placeholder="自动根据标题生成"
              />
            </UFormField>

            <UFormField label="所属栏目">
              <USelectMenu
                v-model="newDoc.categoryId"
                :items="categoryOptions"
                value-key="value"
                placeholder="选择栏目（可选）"
              />
            </UFormField>

            <UFormField label="语言">
              <USelectMenu
                v-model="newDoc.localeId"
                :items="localeOptions"
                value-key="value"
                placeholder="选择语言（可选）"
              />
            </UFormField>
          </div>

          <div class="flex justify-end gap-3 mt-6">
            <UButton
              variant="ghost"
              color="neutral"
              @click="showCreateDialog = false"
            >
              取消
            </UButton>
            <UButton
              :loading="isCreating"
              :disabled="!newDoc.title.trim()"
              @click="createDocument"
            >
              创建
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
