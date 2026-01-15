/**
 * 文档在线状态 Composable
 * 实现查看者心跳和更新通知
 * 
 * Requirements: 13.6, 13.7
 */
import { useIntervalFn } from '@vueuse/core'

export interface Watcher {
  id: string
  name: string
  avatar?: string | null
  lastSeenAt: Date
  needsRefresh: boolean
}

export interface UseDocumentPresenceOptions {
  /** 心跳间隔（毫秒），默认 10 秒 */
  heartbeatInterval?: number
  /** 文档更新时的回调 */
  onDocumentUpdated?: (newVersion: number) => void
  /** 是否自动启动 */
  autoStart?: boolean
}

export interface UseDocumentPresenceReturn {
  /** 当前查看者列表 */
  watchers: Ref<Watcher[]>
  /** 当前文档版本 */
  currentVersion: Ref<number>
  /** 是否需要刷新 */
  needsRefresh: Ref<boolean>
  /** 文档最后更新时间 */
  documentUpdatedAt: Ref<Date | null>
  /** 是否正在加载 */
  loading: Ref<boolean>
  /** 错误信息 */
  error: Ref<string | null>
  /** 启动心跳 */
  start: () => void
  /** 停止心跳 */
  stop: () => void
  /** 手动刷新 */
  refresh: () => Promise<void>
  /** 标记已查看当前版本 */
  markVersionSeen: (version: number) => void
}

/**
 * 文档在线状态 Composable
 * @param documentId 文档 ID（响应式）
 * @param options 配置选项
 */
export function useDocumentPresence(
  documentId: MaybeRef<string>,
  options: UseDocumentPresenceOptions = {}
): UseDocumentPresenceReturn {
  const {
    heartbeatInterval = 10 * 1000, // 10 秒
    onDocumentUpdated,
    autoStart = true,
  } = options

  // 状态
  const watchers = ref<Watcher[]>([])
  const currentVersion = ref(1)
  const needsRefresh = ref(false)
  const documentUpdatedAt = ref<Date | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 本地记录的已查看版本
  const localVersionSeen = ref<number | null>(null)

  // 获取文档 ID
  const getDocumentId = () => toValue(documentId)

  // 发送心跳
  const sendHeartbeat = async () => {
    const docId = getDocumentId()
    if (!docId) return

    try {
      const response = await $fetch<{
        watchers: Watcher[]
        currentVersion: number
        documentUpdatedAt: string
        needsRefresh: boolean
      }>(`/api/documents/${docId}/watchers`, {
        method: 'POST',
        body: {
          versionSeen: localVersionSeen.value,
        },
      })

      watchers.value = response.watchers.map(w => ({
        ...w,
        lastSeenAt: new Date(w.lastSeenAt),
      }))
      
      const prevVersion = currentVersion.value
      currentVersion.value = response.currentVersion
      documentUpdatedAt.value = response.documentUpdatedAt 
        ? new Date(response.documentUpdatedAt) 
        : null
      needsRefresh.value = response.needsRefresh

      // 如果版本更新了，触发回调
      if (prevVersion < response.currentVersion && onDocumentUpdated) {
        onDocumentUpdated(response.currentVersion)
      }

      error.value = null
    } catch (e: any) {
      error.value = e.message || '获取在线状态失败'
      console.error('Presence heartbeat error:', e)
    }
  }

  // 刷新（获取最新状态）
  const refresh = async () => {
    loading.value = true
    await sendHeartbeat()
    loading.value = false
  }

  // 标记已查看版本
  const markVersionSeen = (version: number) => {
    localVersionSeen.value = version
    needsRefresh.value = false
  }

  // 心跳定时器
  const { pause: stop, resume: start, isActive } = useIntervalFn(
    sendHeartbeat,
    heartbeatInterval,
    { immediate: false }
  )

  // 监听文档 ID 变化
  watch(
    () => getDocumentId(),
    async (newId, oldId) => {
      if (newId !== oldId) {
        // 重置状态
        watchers.value = []
        currentVersion.value = 1
        needsRefresh.value = false
        localVersionSeen.value = null
        error.value = null

        if (newId && isActive.value) {
          // 立即发送心跳
          await sendHeartbeat()
        }
      }
    }
  )

  // 自动启动
  if (autoStart) {
    onMounted(() => {
      start()
      // 立即发送一次心跳
      sendHeartbeat()
    })
  }

  // 组件卸载时停止
  onUnmounted(() => {
    stop()
  })

  return {
    watchers,
    currentVersion,
    needsRefresh,
    documentUpdatedAt,
    loading,
    error,
    start,
    stop,
    refresh,
    markVersionSeen,
  }
}
