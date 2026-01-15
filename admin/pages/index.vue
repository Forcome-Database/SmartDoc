<script setup lang="ts">
/**
 * Dashboard 首页
 * 显示最近编辑的文档、团队活动、待处理通知
 * Mintlify 风格：简约大气，充足留白
 * 
 * Requirements: 13.11
 */
import { useUserStore } from '~/stores/user'
import type { DocumentStatus } from '~/types'

definePageMeta({
  middleware: ['auth'],
})

const userStore = useUserStore()
const toast = useToast()

// 最近文档
interface RecentDocument {
  id: string
  title: string
  status: DocumentStatus
  updatedAt: Date
  author?: {
    id: string
    name: string | null
    avatar: string | null
  } | null
}

const recentDocuments = ref<RecentDocument[]>([])
const isLoadingDocuments = ref(true)

// 统计数据
const stats = ref({
  totalDocuments: 0,
  publishedDocuments: 0,
  draftDocuments: 0,
  weeklyUpdates: 0,
})
const isLoadingStats = ref(true)

// 通知
const { notifications, unreadCount, loading: loadingNotifications, markAsRead } = useNotifications({
  autoLoad: true,
  autoPoll: true,
})

// 活动动态
const { activities, loading: loadingActivities, refresh: refreshActivities } = useActivities({
  days: 7,
  limit: 10,
  autoLoad: true,
})

// 获取最近文档
const fetchRecentDocuments = async () => {
  isLoadingDocuments.value = true
  try {
    const data = await $fetch<{
      items: RecentDocument[]
    }>('/api/documents', {
      query: {
        limit: 5,
        sortBy: 'updatedAt',
        sortOrder: 'desc',
      },
    })
    recentDocuments.value = data.items.map(doc => ({
      ...doc,
      updatedAt: new Date(doc.updatedAt),
    }))
  } catch (error: any) {
    console.error('Failed to fetch recent documents:', error)
  } finally {
    isLoadingDocuments.value = false
  }
}

// 获取统计数据
const fetchStats = async () => {
  isLoadingStats.value = true
  try {
    // 获取总文档数
    const allDocs = await $fetch<{ pagination: { total: number } }>('/api/documents', {
      query: { limit: 1 },
    })
    stats.value.totalDocuments = allDocs.pagination.total

    // 获取已发布文档数
    const publishedDocs = await $fetch<{ pagination: { total: number } }>('/api/documents', {
      query: { limit: 1, status: 'published' },
    })
    stats.value.publishedDocuments = publishedDocs.pagination.total

    // 获取草稿文档数
    const draftDocs = await $fetch<{ pagination: { total: number } }>('/api/documents', {
      query: { limit: 1, status: 'draft' },
    })
    stats.value.draftDocuments = draftDocs.pagination.total

    // 本周更新数（通过活动统计）
    const weeklyActivities = await $fetch<{ pagination: { total: number } }>('/api/activities', {
      query: { days: 7, limit: 1 },
    })
    stats.value.weeklyUpdates = weeklyActivities.pagination.total
  } catch (error: any) {
    console.error('Failed to fetch stats:', error)
  } finally {
    isLoadingStats.value = false
  }
}

// 初始化加载
onMounted(() => {
  fetchRecentDocuments()
  fetchStats()
})

// 格式化时间
const formatTime = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60 * 1000) return '刚刚'
  if (diff < 60 * 60 * 1000) return `${Math.floor(diff / (60 * 1000))} 分钟前`
  if (diff < 24 * 60 * 60 * 1000) return `${Math.floor(diff / (60 * 60 * 1000))} 小时前`
  if (diff < 7 * 24 * 60 * 60 * 1000) return `${Math.floor(diff / (24 * 60 * 60 * 1000))} 天前`
  
  return date.toLocaleDateString('zh-CN')
}

// 获取活动类型文本
const getActivityTypeText = (type: string) => {
  const textMap: Record<string, string> = {
    document_created: '创建了文档',
    document_updated: '更新了文档',
    document_published: '发布了文档',
    document_deleted: '删除了文档',
    comment_added: '添加了评论',
    version_created: '创建了新版本',
  }
  return textMap[type] || type
}

// 处理通知点击
const handleNotificationClick = async (notification: any) => {
  if (!notification.isRead) {
    await markAsRead(notification.id)
  }
  if (notification.documentId) {
    navigateTo(`/documents/${notification.documentId}`)
  }
}

// 统计卡片配置
const statCards = computed(() => [
  { 
    label: '文档总数', 
    value: stats.value.totalDocuments, 
    icon: 'i-lucide-file-text', 
    gradient: 'from-blue-500/10 to-indigo-500/10', 
    iconColor: 'text-blue-600 dark:text-blue-400' 
  },
  { 
    label: '已发布', 
    value: stats.value.publishedDocuments, 
    icon: 'i-lucide-check-circle', 
    gradient: 'from-emerald-500/10 to-teal-500/10', 
    iconColor: 'text-emerald-600 dark:text-emerald-400' 
  },
  { 
    label: '草稿', 
    value: stats.value.draftDocuments, 
    icon: 'i-lucide-edit-3', 
    gradient: 'from-amber-500/10 to-orange-500/10', 
    iconColor: 'text-amber-600 dark:text-amber-400' 
  },
  { 
    label: '本周动态', 
    value: stats.value.weeklyUpdates, 
    icon: 'i-lucide-trending-up', 
    gradient: 'from-violet-500/10 to-purple-500/10', 
    iconColor: 'text-violet-600 dark:text-violet-400' 
  },
])
</script>

<template>
  <div class="p-8 lg:p-12 max-w-6xl mx-auto">
    <!-- 欢迎区域 -->
    <div class="mb-10">
      <h1 class="text-3xl font-semibold text-gray-900 dark:text-white tracking-tight">
        欢迎回来，{{ userStore.displayName }}
      </h1>
      <p class="text-gray-500 dark:text-gray-400 mt-2 text-base">
        这是 FORCOME 知识库管理系统的控制台
      </p>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-10">
      <div 
        v-for="stat in statCards" 
        :key="stat.label" 
        class="group relative overflow-hidden rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/60 dark:border-gray-800 p-5 transition-all duration-200 hover:border-gray-300 dark:hover:border-gray-700 hover:shadow-lg hover:shadow-gray-200/50 dark:hover:shadow-gray-900/50"
      >
        <!-- 渐变背景装饰 -->
        <div :class="['absolute inset-0 bg-gradient-to-br opacity-50', stat.gradient]" />
        
        <div class="relative flex items-start justify-between">
          <div>
            <p class="text-3xl font-bold text-gray-900 dark:text-white">
              <template v-if="isLoadingStats">
                <UIcon name="i-lucide-loader-2" class="w-6 h-6 animate-spin" />
              </template>
              <template v-else>
                {{ stat.value }}
              </template>
            </p>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ stat.label }}</p>
          </div>
          <div class="p-2.5 rounded-xl bg-white/80 dark:bg-gray-800/80 shadow-sm">
            <UIcon :name="stat.icon" :class="['w-5 h-5', stat.iconColor]" />
          </div>
        </div>
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="grid lg:grid-cols-3 gap-6 lg:gap-8">
      <!-- 最近文档 -->
      <div class="lg:col-span-2 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/60 dark:border-gray-800 overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800">
          <h2 class="font-semibold text-gray-900 dark:text-white">最近编辑</h2>
          <NuxtLink 
            to="/content" 
            class="text-sm text-gray-500 hover:text-primary-600 dark:text-gray-400 dark:hover:text-primary-400 flex items-center gap-1 transition-colors"
          >
            查看全部
            <UIcon name="i-lucide-arrow-right" class="w-4 h-4" />
          </NuxtLink>
        </div>

        <!-- 加载状态 -->
        <div v-if="isLoadingDocuments" class="flex items-center justify-center py-12">
          <UIcon name="i-lucide-loader-2" class="w-6 h-6 animate-spin text-gray-400" />
        </div>

        <!-- 空状态 -->
        <div v-else-if="recentDocuments.length === 0" class="text-center py-12">
          <UIcon name="i-lucide-file-text" class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-gray-500">暂无文档</p>
          <UButton color="primary" size="sm" class="mt-4" to="/content">
            <UIcon name="i-lucide-plus" class="w-4 h-4 mr-1" />
            创建文档
          </UButton>
        </div>

        <!-- 文档列表 -->
        <div v-else class="divide-y divide-gray-100 dark:divide-gray-800">
          <NuxtLink 
            v-for="doc in recentDocuments" 
            :key="doc.id"
            :to="`/documents/${doc.id}`"
            class="flex items-center justify-between px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
          >
            <div class="flex items-center gap-4">
              <div class="w-10 h-10 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                <UIcon name="i-lucide-file-text" class="w-5 h-5 text-gray-400" />
              </div>
              <div>
                <p class="font-medium text-gray-900 dark:text-white">{{ doc.title }}</p>
                <p class="text-sm text-gray-500 dark:text-gray-400">{{ formatTime(doc.updatedAt) }}</p>
              </div>
            </div>
            <span 
              :class="[
                'px-2.5 py-1 text-xs font-medium rounded-full',
                doc.status === 'published' 
                  ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400' 
                  : 'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400'
              ]"
            >
              {{ doc.status === 'published' ? '已发布' : '草稿' }}
            </span>
          </NuxtLink>
        </div>
      </div>

      <!-- 右侧栏：通知和活动 -->
      <div class="space-y-6">
        <!-- 待处理通知 -->
        <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/60 dark:border-gray-800 overflow-hidden">
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800">
            <div class="flex items-center gap-2">
              <h2 class="font-semibold text-gray-900 dark:text-white">通知</h2>
              <UBadge v-if="unreadCount > 0" color="error" size="xs">
                {{ unreadCount }}
              </UBadge>
            </div>
          </div>

          <!-- 加载状态 -->
          <div v-if="loadingNotifications && notifications.length === 0" class="flex items-center justify-center py-8">
            <UIcon name="i-lucide-loader-2" class="w-5 h-5 animate-spin text-gray-400" />
          </div>

          <!-- 空状态 -->
          <div v-else-if="notifications.length === 0" class="text-center py-8">
            <UIcon name="i-lucide-bell" class="w-10 h-10 text-gray-300 mx-auto mb-2" />
            <p class="text-sm text-gray-500">暂无通知</p>
          </div>

          <!-- 通知列表 -->
          <div v-else class="divide-y divide-gray-100 dark:divide-gray-800 max-h-64 overflow-y-auto">
            <div 
              v-for="notification in notifications.slice(0, 5)" 
              :key="notification.id"
              class="px-6 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer transition-colors"
              :class="{ 'bg-primary-50/50 dark:bg-primary-500/5': !notification.isRead }"
              @click="handleNotificationClick(notification)"
            >
              <div class="flex items-start gap-3">
                <div 
                  class="w-2 h-2 rounded-full mt-2 flex-shrink-0"
                  :class="notification.isRead ? 'bg-gray-300' : 'bg-primary-500'"
                />
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {{ notification.title }}
                  </p>
                  <p class="text-xs text-gray-500 mt-0.5">
                    {{ formatTime(notification.createdAt) }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 团队活动 -->
        <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/60 dark:border-gray-800 overflow-hidden">
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800">
            <h2 class="font-semibold text-gray-900 dark:text-white">团队动态</h2>
            <UButton
              size="xs"
              variant="ghost"
              color="neutral"
              icon="i-lucide-refresh-cw"
              :loading="loadingActivities"
              @click="refreshActivities"
            />
          </div>

          <!-- 加载状态 -->
          <div v-if="loadingActivities && activities.length === 0" class="flex items-center justify-center py-8">
            <UIcon name="i-lucide-loader-2" class="w-5 h-5 animate-spin text-gray-400" />
          </div>

          <!-- 空状态 -->
          <div v-else-if="activities.length === 0" class="text-center py-8">
            <UIcon name="i-lucide-activity" class="w-10 h-10 text-gray-300 mx-auto mb-2" />
            <p class="text-sm text-gray-500">暂无动态</p>
          </div>

          <!-- 活动列表 -->
          <div v-else class="divide-y divide-gray-100 dark:divide-gray-800 max-h-80 overflow-y-auto">
            <div 
              v-for="activity in activities.slice(0, 8)" 
              :key="activity.id"
              class="flex items-start gap-3 px-6 py-3"
            >
              <UAvatar 
                :src="activity.user.avatar || undefined"
                :alt="activity.user.name"
                size="xs"
                class="ring-2 ring-white dark:ring-gray-900 flex-shrink-0"
              />
              <div class="flex-1 min-w-0">
                <p class="text-sm text-gray-900 dark:text-white">
                  <span class="font-medium">{{ activity.user.name }}</span>
                  <span class="text-gray-500 dark:text-gray-400"> {{ getActivityTypeText(activity.type) }} </span>
                </p>
                <NuxtLink
                  v-if="activity.documentId"
                  :to="`/documents/${activity.documentId}`"
                  class="text-sm text-primary-600 dark:text-primary-400 hover:underline truncate block"
                >
                  {{ activity.documentTitle || '未命名文档' }}
                </NuxtLink>
                <p class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                  {{ formatTime(activity.createdAt) }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="mt-10">
      <h2 class="font-semibold text-gray-900 dark:text-white mb-4">快捷操作</h2>
      <div class="flex flex-wrap gap-3">
        <UButton color="primary" size="md" class="shadow-sm shadow-primary-500/20" to="/content">
          <UIcon name="i-lucide-files" class="w-4 h-4 mr-2" />
          文档
        </UButton>
        <UButton variant="outline" color="neutral" size="md" to="/nav-menus">
          <UIcon name="i-lucide-menu" class="w-4 h-4 mr-2" />
          导航菜单
        </UButton>
        <UButton variant="outline" color="neutral" size="md" to="/settings/locales">
          <UIcon name="i-lucide-settings" class="w-4 h-4 mr-2" />
          系统设置
        </UButton>
      </div>
    </div>
  </div>
</template>
