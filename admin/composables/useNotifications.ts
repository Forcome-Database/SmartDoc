/**
 * 通知 Composable
 * 管理用户通知的获取和状态更新
 * 
 * Requirements: 13.10
 */
import { useIntervalFn } from '@vueuse/core'

export type NotificationType = 'mention' | 'comment' | 'document_update' | 'system'

export interface NotificationUser {
  id: string
  name: string
  avatar?: string | null
}

export interface Notification {
  id: string
  type: NotificationType
  title: string
  content?: string | null
  documentId?: string | null
  documentTitle?: string | null
  commentId?: string | null
  isRead: boolean
  readAt?: Date | null
  createdAt: Date
  fromUser?: NotificationUser | null
}

export interface UseNotificationsOptions {
  /** 轮询间隔（毫秒），默认 30 秒 */
  pollInterval?: number
  /** 是否自动轮询 */
  autoPoll?: boolean
  /** 是否自动加载 */
  autoLoad?: boolean
}

export interface UseNotificationsReturn {
  /** 通知列表 */
  notifications: Ref<Notification[]>
  /** 未读数量 */
  unreadCount: Ref<number>
  /** 是否正在加载 */
  loading: Ref<boolean>
  /** 错误信息 */
  error: Ref<string | null>
  /** 加载通知 */
  load: (options?: { unreadOnly?: boolean }) => Promise<void>
  /** 标记为已读 */
  markAsRead: (id: string) => Promise<boolean>
  /** 标记所有为已读 */
  markAllAsRead: () => Promise<boolean>
  /** 开始轮询 */
  startPolling: () => void
  /** 停止轮询 */
  stopPolling: () => void
}

/**
 * 通知 Composable
 */
export function useNotifications(
  options: UseNotificationsOptions = {}
): UseNotificationsReturn {
  const {
    pollInterval = 30 * 1000,
    autoPoll = true,
    autoLoad = true,
  } = options

  // 状态
  const notifications = ref<Notification[]>([])
  const unreadCount = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 格式化通知
  const formatNotification = (n: any): Notification => ({
    ...n,
    createdAt: new Date(n.createdAt),
    readAt: n.readAt ? new Date(n.readAt) : null,
  })

  // 加载通知
  const load = async (opts?: { unreadOnly?: boolean }) => {
    loading.value = true
    error.value = null

    try {
      const response = await $fetch<{
        notifications: Notification[]
        unreadCount: number
      }>('/api/notifications', {
        query: {
          unreadOnly: opts?.unreadOnly ? 'true' : undefined,
          limit: 50,
        },
      })

      notifications.value = response.notifications.map(formatNotification)
      unreadCount.value = response.unreadCount
    } catch (e: any) {
      error.value = e.message || '加载通知失败'
      console.error('Load notifications error:', e)
    } finally {
      loading.value = false
    }
  }

  // 标记为已读
  const markAsRead = async (id: string): Promise<boolean> => {
    try {
      await $fetch(`/api/notifications/${id}`, {
        method: 'PATCH',
        body: { isRead: true },
      })

      // 更新本地状态
      const index = notifications.value.findIndex(n => n.id === id)
      if (index !== -1 && !notifications.value[index].isRead) {
        notifications.value[index].isRead = true
        notifications.value[index].readAt = new Date()
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }

      return true
    } catch (e: any) {
      error.value = e.message || '标记已读失败'
      console.error('Mark as read error:', e)
      return false
    }
  }

  // 标记所有为已读
  const markAllAsRead = async (): Promise<boolean> => {
    try {
      await $fetch('/api/notifications/read-all', {
        method: 'POST',
      })

      // 更新本地状态
      const now = new Date()
      notifications.value.forEach(n => {
        if (!n.isRead) {
          n.isRead = true
          n.readAt = now
        }
      })
      unreadCount.value = 0

      return true
    } catch (e: any) {
      error.value = e.message || '标记全部已读失败'
      console.error('Mark all as read error:', e)
      return false
    }
  }

  // 轮询定时器
  const { pause: stopPolling, resume: startPolling } = useIntervalFn(
    () => load(),
    pollInterval,
    { immediate: false }
  )

  // 自动加载和轮询
  if (autoLoad) {
    onMounted(() => {
      load()
      if (autoPoll) {
        startPolling()
      }
    })
  }

  // 组件卸载时停止轮询
  onUnmounted(() => {
    stopPolling()
  })

  return {
    notifications,
    unreadCount,
    loading,
    error,
    load,
    markAsRead,
    markAllAsRead,
    startPolling,
    stopPolling,
  }
}
