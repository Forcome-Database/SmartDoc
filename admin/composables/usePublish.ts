/**
 * 发布功能 Composable
 * 管理文档发布状态和操作
 * 
 * Requirements: 5.1, 5.3, 5.5, 5.6, 5.7
 */

export type PublishStatus = 'unpublished' | 'published' | 'has_changes' | 'publishing'

export interface PublishState {
  status: PublishStatus
  publishedVersion: number | null
  currentVersion: number
  isPublishing: boolean
  error: string | null
}

export interface SyncStatus {
  syncStatus: 'synced' | 'ahead' | 'behind' | 'diverged' | 'error'
  ahead: number
  behind: number
  hasLocalChanges: boolean
}

/**
 * 单文档发布 Composable
 */
export function useDocumentPublish(documentId: MaybeRef<string>) {
  const docId = toRef(documentId)
  const toast = useToast()

  const isPublishing = ref(false)
  const error = ref<string | null>(null)

  /**
   * 发布文档
   */
  const publish = async (): Promise<boolean> => {
    isPublishing.value = true
    error.value = null

    try {
      const result = await $fetch(`/api/documents/${docId.value}/publish`, {
        method: 'POST',
      })

      toast.add({
        title: '发布成功',
        description: `文档已发布到 ${result.publish?.filePath || 'docs 目录'}`,
        color: 'success',
      })

      return true
    } catch (e: any) {
      const errorMessage = e.data?.message || e.message || '发布失败'
      error.value = errorMessage
      
      toast.add({
        title: '发布失败',
        description: errorMessage,
        color: 'error',
      })

      return false
    } finally {
      isPublishing.value = false
    }
  }

  /**
   * 计算发布状态
   * 基于数据库字段判断，不依赖前端编辑状态
   */
  const getPublishStatus = (
    documentStatus: string,
    publishedVersion: number | null,
    currentVersion: number,
    hasUnpublishedChanges?: boolean
  ): PublishStatus => {
    // 从未发布过
    if (documentStatus === 'draft' || publishedVersion === null) {
      return 'unpublished'
    }
    // 有未发布的更改（数据库标记）
    if (hasUnpublishedChanges) {
      return 'has_changes'
    }
    // 版本号不一致（兼容旧逻辑）
    if (publishedVersion < currentVersion) {
      return 'has_changes'
    }
    return 'published'
  }

  return {
    isPublishing: readonly(isPublishing),
    error: readonly(error),
    publish,
    getPublishStatus,
  }
}

/**
 * 批量发布 Composable
 */
export function useBatchPublish() {
  const toast = useToast()

  const isPublishing = ref(false)
  const progress = ref(0)
  const error = ref<string | null>(null)

  /**
   * 批量发布文档
   */
  const publishBatch = async (documentIds: string[]): Promise<{
    success: boolean
    publishedCount: number
    failedCount: number
  }> => {
    if (documentIds.length === 0) {
      toast.add({
        title: '请选择文档',
        description: '请至少选择一个文档进行发布',
        color: 'warning',
      })
      return { success: false, publishedCount: 0, failedCount: 0 }
    }

    isPublishing.value = true
    progress.value = 0
    error.value = null

    try {
      const result = await $fetch('/api/publish/batch', {
        method: 'POST',
        body: { documentIds },
      })

      if (result.success) {
        toast.add({
          title: '批量发布完成',
          description: `成功发布 ${result.publishedCount} 个文档${result.failedCount > 0 ? `，${result.failedCount} 个失败` : ''}`,
          color: result.failedCount > 0 ? 'warning' : 'success',
        })
      } else {
        toast.add({
          title: '批量发布失败',
          description: `${result.failedCount} 个文档发布失败`,
          color: 'error',
        })
      }

      return {
        success: result.success,
        publishedCount: result.publishedCount,
        failedCount: result.failedCount,
      }
    } catch (e: any) {
      const errorMessage = e.data?.message || e.message || '批量发布失败'
      error.value = errorMessage

      toast.add({
        title: '批量发布失败',
        description: errorMessage,
        color: 'error',
      })

      return { success: false, publishedCount: 0, failedCount: documentIds.length }
    } finally {
      isPublishing.value = false
      progress.value = 100
    }
  }

  return {
    isPublishing: readonly(isPublishing),
    progress: readonly(progress),
    error: readonly(error),
    publishBatch,
  }
}

/**
 * Git 同步状态 Composable
 */
export function useGitSyncStatus() {
  const syncStatus = ref<SyncStatus>({
    syncStatus: 'synced',
    ahead: 0,
    behind: 0,
    hasLocalChanges: false,
  })
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  /**
   * 获取同步状态
   */
  const fetchStatus = async () => {
    isLoading.value = true
    error.value = null

    try {
      const result = await $fetch('/api/publish/status')
      syncStatus.value = {
        syncStatus: result.syncStatus,
        ahead: result.ahead,
        behind: result.behind,
        hasLocalChanges: result.hasLocalChanges,
      }
    } catch (e: any) {
      error.value = e.data?.message || e.message || '获取状态失败'
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 推送到远程
   */
  const push = async (): Promise<boolean> => {
    const toast = useToast()

    try {
      await $fetch('/api/publish/push', { method: 'POST' })
      
      toast.add({
        title: '推送成功',
        description: '已推送到远程仓库',
        color: 'success',
      })

      // 刷新状态
      await fetchStatus()
      return true
    } catch (e: any) {
      toast.add({
        title: '推送失败',
        description: e.data?.message || e.message || '推送失败',
        color: 'error',
      })
      return false
    }
  }

  // 定期刷新状态（每 30 秒）
  let intervalId: ReturnType<typeof setInterval> | null = null

  const startPolling = () => {
    if (intervalId) return
    fetchStatus()
    intervalId = setInterval(fetchStatus, 30000)
  }

  const stopPolling = () => {
    if (intervalId) {
      clearInterval(intervalId)
      intervalId = null
    }
  }

  onMounted(() => {
    startPolling()
  })

  onUnmounted(() => {
    stopPolling()
  })

  return {
    syncStatus: readonly(syncStatus),
    isLoading: readonly(isLoading),
    error: readonly(error),
    fetchStatus,
    push,
    startPolling,
    stopPolling,
  }
}

/**
 * 获取发布状态的显示信息
 */
export function getPublishStatusDisplay(status: PublishStatus): {
  label: string
  color: string
  icon: string
} {
  switch (status) {
    case 'unpublished':
      return {
        label: '未发布',
        color: 'neutral',
        icon: 'i-lucide-file-x',
      }
    case 'published':
      return {
        label: '已发布',
        color: 'success',
        icon: 'i-lucide-check-circle',
      }
    case 'has_changes':
      return {
        label: '有更改',
        color: 'warning',
        icon: 'i-lucide-alert-circle',
      }
    case 'publishing':
      return {
        label: '发布中',
        color: 'primary',
        icon: 'i-lucide-loader-2',
      }
    default:
      return {
        label: '未知',
        color: 'neutral',
        icon: 'i-lucide-help-circle',
      }
  }
}

/**
 * 获取同步状态的显示信息
 */
export function getSyncStatusDisplay(status: SyncStatus['syncStatus']): {
  label: string
  color: string
  icon: string
} {
  switch (status) {
    case 'synced':
      return {
        label: '已同步',
        color: 'success',
        icon: 'i-lucide-check-circle',
      }
    case 'ahead':
      return {
        label: '待推送',
        color: 'warning',
        icon: 'i-lucide-arrow-up-circle',
      }
    case 'behind':
      return {
        label: '待拉取',
        color: 'info',
        icon: 'i-lucide-arrow-down-circle',
      }
    case 'diverged':
      return {
        label: '有冲突',
        color: 'error',
        icon: 'i-lucide-git-branch',
      }
    case 'error':
      return {
        label: '状态异常',
        color: 'error',
        icon: 'i-lucide-alert-triangle',
      }
    default:
      return {
        label: '未知',
        color: 'neutral',
        icon: 'i-lucide-help-circle',
      }
  }
}
