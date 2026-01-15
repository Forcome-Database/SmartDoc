<script setup lang="ts">
/**
 * 活动动态组件
 * 显示最近的文档变更动态
 * 
 * Requirements: 13.11
 */
import { getActivityTypeText, getActivityTypeIcon } from '~/composables/useActivities'

const props = defineProps<{
  /** 时间范围（天数） */
  days?: number
  /** 显示数量 */
  limit?: number
}>()

const { activities, loading, error, hasMore, loadMore, refresh } = useActivities({
  days: props.days || 7,
  limit: props.limit || 10,
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
</script>

<template>
  <div class="activity-feed">
    <!-- 头部 -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="font-semibold text-gray-900 dark:text-white">最近动态</h3>
      <UButton
        size="xs"
        variant="ghost"
        color="neutral"
        icon="i-lucide-refresh-cw"
        :loading="loading"
        @click="refresh"
      />
    </div>

    <!-- 加载状态 -->
    <div v-if="loading && activities.length === 0" class="flex items-center justify-center py-8">
      <UIcon name="i-lucide-loader-2" class="w-6 h-6 animate-spin text-gray-400" />
    </div>

    <!-- 空状态 -->
    <div v-else-if="activities.length === 0" class="text-center py-8">
      <UIcon name="i-lucide-activity" class="w-12 h-12 text-gray-300 mx-auto mb-2" />
      <p class="text-gray-500">暂无动态</p>
    </div>

    <!-- 活动列表 -->
    <div v-else class="space-y-4">
      <div
        v-for="activity in activities"
        :key="activity.id"
        class="flex items-start gap-3"
      >
        <!-- 用户头像 -->
        <UAvatar
          :src="activity.user.avatar || undefined"
          :alt="activity.user.name"
          size="sm"
        />

        <!-- 活动内容 -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <span class="font-medium text-gray-900 dark:text-white text-sm">
              {{ activity.user.name }}
            </span>
            <span class="text-gray-500 text-sm">
              {{ getActivityTypeText(activity.type) }}
            </span>
          </div>

          <!-- 文档链接 -->
          <NuxtLink
            v-if="activity.documentId"
            :to="`/documents/${activity.documentId}`"
            class="text-sm text-primary-600 dark:text-primary-400 hover:underline truncate block"
          >
            {{ activity.documentTitle || '未命名文档' }}
          </NuxtLink>
          <span v-else-if="activity.documentTitle" class="text-sm text-gray-600 dark:text-gray-400 truncate block">
            {{ activity.documentTitle }}
          </span>

          <!-- 版本信息 -->
          <span v-if="activity.versionNum" class="text-xs text-gray-500">
            v{{ activity.versionNum }}
          </span>

          <!-- 时间 -->
          <span class="text-xs text-gray-400 block mt-0.5">
            {{ formatTime(activity.createdAt) }}
          </span>
        </div>

        <!-- 活动图标 -->
        <UIcon
          :name="getActivityTypeIcon(activity.type)"
          class="w-4 h-4 text-gray-400 flex-shrink-0"
        />
      </div>

      <!-- 加载更多 -->
      <div v-if="hasMore" class="text-center pt-2">
        <UButton
          size="xs"
          variant="ghost"
          color="neutral"
          :loading="loading"
          @click="loadMore"
        >
          加载更多
        </UButton>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="mt-2 text-sm text-red-500">
      {{ error }}
    </div>
  </div>
</template>
