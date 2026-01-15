/**
 * 活动动态 Composable
 * 获取最近的文档变更动态
 * 
 * Requirements: 13.11
 */

export type ActivityType = 
  | 'document_created'
  | 'document_updated'
  | 'document_published'
  | 'document_deleted'
  | 'comment_added'
  | 'version_created'

export interface ActivityUser {
  id: string
  name: string
  avatar?: string | null
}

export interface Activity {
  id: string
  type: ActivityType
  documentId?: string | null
  documentTitle?: string | null
  versionNum?: number | null
  commentId?: string | null
  metadata?: Record<string, any> | null
  createdAt: Date
  user: ActivityUser
}

export interface UseActivitiesOptions {
  /** 时间范围（天数），默认 7 天 */
  days?: number
  /** 每页数量 */
  limit?: number
  /** 用户 ID 过滤 */
  userId?: string
  /** 是否自动加载 */
  autoLoad?: boolean
}

export interface UseActivitiesReturn {
  /** 活动列表 */
  activities: Ref<Activity[]>
  /** 是否正在加载 */
  loading: Ref<boolean>
  /** 错误信息 */
  error: Ref<string | null>
  /** 是否还有更多 */
  hasMore: Ref<boolean>
  /** 加载活动 */
  load: () => Promise<void>
  /** 加载更多 */
  loadMore: () => Promise<void>
  /** 刷新 */
  refresh: () => Promise<void>
}

/**
 * 活动动态 Composable
 */
export function useActivities(
  options: UseActivitiesOptions = {}
): UseActivitiesReturn {
  const {
    days = 7,
    limit = 20,
    userId,
    autoLoad = true,
  } = options

  // 状态
  const activities = ref<Activity[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const hasMore = ref(true)
  const currentPage = ref(1)

  // 格式化活动
  const formatActivity = (a: any): Activity => ({
    ...a,
    createdAt: new Date(a.createdAt),
  })

  // 加载活动
  const load = async () => {
    loading.value = true
    error.value = null
    currentPage.value = 1

    try {
      const response = await $fetch<{
        activities: Activity[]
        pagination: { totalPages: number }
      }>('/api/activities', {
        query: {
          days,
          limit,
          userId,
          page: 1,
        },
      })

      activities.value = response.activities.map(formatActivity)
      hasMore.value = response.pagination.totalPages > 1
    } catch (e: any) {
      error.value = e.message || '加载活动失败'
      console.error('Load activities error:', e)
    } finally {
      loading.value = false
    }
  }

  // 加载更多
  const loadMore = async () => {
    if (loading.value || !hasMore.value) return

    loading.value = true
    currentPage.value++

    try {
      const response = await $fetch<{
        activities: Activity[]
        pagination: { totalPages: number; page: number }
      }>('/api/activities', {
        query: {
          days,
          limit,
          userId,
          page: currentPage.value,
        },
      })

      activities.value.push(...response.activities.map(formatActivity))
      hasMore.value = response.pagination.page < response.pagination.totalPages
    } catch (e: any) {
      error.value = e.message || '加载更多失败'
      currentPage.value--
      console.error('Load more activities error:', e)
    } finally {
      loading.value = false
    }
  }

  // 刷新
  const refresh = async () => {
    await load()
  }

  // 自动加载
  if (autoLoad) {
    onMounted(() => {
      load()
    })
  }

  return {
    activities,
    loading,
    error,
    hasMore,
    load,
    loadMore,
    refresh,
  }
}

/**
 * 获取活动类型的显示文本
 */
export function getActivityTypeText(type: ActivityType): string {
  const textMap: Record<ActivityType, string> = {
    document_created: '创建了文档',
    document_updated: '更新了文档',
    document_published: '发布了文档',
    document_deleted: '删除了文档',
    comment_added: '添加了评论',
    version_created: '创建了新版本',
  }
  return textMap[type] || type
}

/**
 * 获取活动类型的图标
 */
export function getActivityTypeIcon(type: ActivityType): string {
  const iconMap: Record<ActivityType, string> = {
    document_created: 'i-lucide-file-plus',
    document_updated: 'i-lucide-file-edit',
    document_published: 'i-lucide-upload-cloud',
    document_deleted: 'i-lucide-file-x',
    comment_added: 'i-lucide-message-square',
    version_created: 'i-lucide-git-branch',
  }
  return iconMap[type] || 'i-lucide-activity'
}
