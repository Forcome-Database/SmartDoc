/**
 * 编辑锁 Composable
 * 实现锁获取、续期、释放逻辑
 * 
 * Requirements: 13.2, 13.4, 13.5
 */
import { useIntervalFn } from '@vueuse/core'

export type LockStatus = 'idle' | 'acquiring' | 'locked' | 'locked_by_other' | 'error' | 'expired'

export interface LockUser {
  id: string
  name: string
  avatar?: string | null
}

export interface EditLockInfo {
  id: string
  documentId: string
  userId: string
  acquiredAt: Date
  expiresAt: Date
  user: LockUser
}

export interface UseEditLockOptions {
  /** 心跳间隔（毫秒），默认 2 分钟 */
  heartbeatInterval?: number
  /** 是否自动获取锁 */
  autoAcquire?: boolean
  /** 锁获取失败时的回调 */
  onLockFailed?: (lockedBy: LockUser) => void
  /** 锁过期时的回调 */
  onLockExpired?: () => void
  /** 锁获取成功时的回调 */
  onLockAcquired?: () => void
}

export interface UseEditLockReturn {
  /** 当前锁状态 */
  status: Ref<LockStatus>
  /** 锁信息 */
  lock: Ref<EditLockInfo | null>
  /** 锁持有者（如果被其他用户锁定） */
  lockedBy: Ref<LockUser | null>
  /** 是否可以编辑 */
  canEdit: ComputedRef<boolean>
  /** 错误信息 */
  error: Ref<string | null>
  /** 获取锁 */
  acquire: () => Promise<boolean>
  /** 释放锁 */
  release: () => Promise<void>
  /** 续期锁 */
  renew: () => Promise<boolean>
  /** 重置状态 */
  reset: () => void
}

/**
 * 编辑锁 Composable
 * @param documentId 文档 ID（响应式）
 * @param options 配置选项
 */
export function useEditLock(
  documentId: MaybeRef<string>,
  options: UseEditLockOptions = {}
): UseEditLockReturn {
  const {
    heartbeatInterval = 2 * 60 * 1000, // 2 分钟
    autoAcquire = false,
    onLockFailed,
    onLockExpired,
    onLockAcquired,
  } = options

  // 状态
  const status = ref<LockStatus>('idle')
  const lock = ref<EditLockInfo | null>(null)
  const lockedBy = ref<LockUser | null>(null)
  const error = ref<string | null>(null)

  // 计算属性
  const canEdit = computed(() => status.value === 'locked')

  // 获取文档 ID
  const getDocumentId = () => toValue(documentId)

  // 获取锁
  const acquire = async (): Promise<boolean> => {
    const docId = getDocumentId()
    if (!docId) {
      error.value = '文档 ID 无效'
      return false
    }

    status.value = 'acquiring'
    error.value = null
    lockedBy.value = null

    try {
      const response = await $fetch<{
        success: boolean
        lock: EditLockInfo
        renewed: boolean
      }>(`/api/documents/${docId}/lock`, {
        method: 'POST',
      })

      if (response.success) {
        lock.value = {
          ...response.lock,
          acquiredAt: new Date(response.lock.acquiredAt),
          expiresAt: new Date(response.lock.expiresAt),
        }
        status.value = 'locked'
        onLockAcquired?.()
        return true
      }

      return false
    } catch (e: any) {
      if (e.statusCode === 409) {
        // 被其他用户锁定
        status.value = 'locked_by_other'
        lockedBy.value = e.data?.lockedBy || null
        error.value = e.message || '文档被其他用户锁定'
        onLockFailed?.(lockedBy.value!)
      } else {
        status.value = 'error'
        error.value = e.message || '获取编辑锁失败'
      }
      return false
    }
  }

  // 续期锁
  const renew = async (): Promise<boolean> => {
    const docId = getDocumentId()
    if (!docId || status.value !== 'locked') {
      return false
    }

    try {
      const response = await $fetch<{
        success: boolean
        lock: EditLockInfo
      }>(`/api/documents/${docId}/lock`, {
        method: 'PATCH',
      })

      if (response.success) {
        lock.value = {
          ...response.lock,
          acquiredAt: new Date(response.lock.acquiredAt),
          expiresAt: new Date(response.lock.expiresAt),
        }
        return true
      }

      return false
    } catch (e: any) {
      if (e.statusCode === 410 || e.statusCode === 404) {
        // 锁已过期或不存在
        status.value = 'expired'
        lock.value = null
        error.value = '编辑锁已过期'
        onLockExpired?.()
      } else {
        console.error('Lock renewal error:', e)
      }
      return false
    }
  }

  // 释放锁
  const release = async (): Promise<void> => {
    const docId = getDocumentId()
    if (!docId) return

    // 停止心跳
    stopHeartbeat()

    try {
      await $fetch(`/api/documents/${docId}/lock`, {
        method: 'DELETE',
      })
    } catch (e) {
      console.error('Lock release error:', e)
    } finally {
      lock.value = null
      status.value = 'idle'
      error.value = null
      lockedBy.value = null
    }
  }

  // 使用 Beacon API 释放锁（页面卸载时）
  const releaseWithBeacon = () => {
    const docId = getDocumentId()
    if (!docId || status.value !== 'locked') return

    // 使用 Beacon API 发送释放请求
    if (navigator.sendBeacon) {
      navigator.sendBeacon(`/api/documents/${docId}/lock/release`)
    }
  }

  // 重置状态
  const reset = () => {
    stopHeartbeat()
    lock.value = null
    status.value = 'idle'
    error.value = null
    lockedBy.value = null
  }

  // 心跳定时器
  const { pause: stopHeartbeat, resume: startHeartbeat } = useIntervalFn(
    async () => {
      if (status.value === 'locked') {
        await renew()
      }
    },
    heartbeatInterval,
    { immediate: false }
  )

  // 监听文档 ID 变化
  watch(
    () => getDocumentId(),
    async (newId, oldId) => {
      if (oldId && oldId !== newId) {
        // 文档 ID 变化，释放旧锁
        await release()
      }

      if (newId && autoAcquire) {
        // 自动获取新锁
        const success = await acquire()
        if (success) {
          startHeartbeat()
        }
      }
    },
    { immediate: autoAcquire }
  )

  // 监听锁状态，启动/停止心跳
  watch(status, (newStatus) => {
    if (newStatus === 'locked') {
      startHeartbeat()
    } else {
      stopHeartbeat()
    }
  })

  // 页面卸载时释放锁
  if (import.meta.client) {
    const handleBeforeUnload = () => {
      releaseWithBeacon()
    }

    const handleVisibilityChange = () => {
      // 页面隐藏时不释放锁，但可以在这里添加其他逻辑
      // 比如在页面长时间隐藏后释放锁
    }

    onMounted(() => {
      window.addEventListener('beforeunload', handleBeforeUnload)
      document.addEventListener('visibilitychange', handleVisibilityChange)
    })

    onUnmounted(() => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      // 组件卸载时释放锁
      release()
    })
  }

  return {
    status,
    lock,
    lockedBy,
    canEdit,
    error,
    acquire,
    release,
    renew,
    reset,
  }
}
