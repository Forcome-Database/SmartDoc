/**
 * 自动保存 Composable
 * 实现防抖保存逻辑和保存状态指示
 * 
 * Requirements: 3.7
 */
import { useDebounceFn } from '@vueuse/core'

export type SaveStatus = 'idle' | 'saving' | 'saved' | 'error' | 'unsaved'

export interface UseAutoSaveOptions {
  /** 防抖延迟时间（毫秒） */
  debounceMs?: number
  /** 保存成功后显示"已保存"状态的持续时间（毫秒） */
  savedDuration?: number
  /** 是否启用自动保存 */
  enabled?: boolean
}

export interface UseAutoSaveReturn {
  /** 当前保存状态 */
  status: Ref<SaveStatus>
  /** 是否有未保存的更改 */
  hasUnsavedChanges: Ref<boolean>
  /** 上次保存时间 */
  lastSavedAt: Ref<Date | null>
  /** 错误信息 */
  error: Ref<string | null>
  /** 标记内容已更改 */
  markChanged: () => void
  /** 手动触发保存 */
  save: () => Promise<void>
  /** 重置状态 */
  reset: () => void
  /** 状态文本（用于 UI 显示） */
  statusText: ComputedRef<string>
  /** 状态图标 */
  statusIcon: ComputedRef<string>
  /** 状态颜色 */
  statusColor: ComputedRef<string>
}

/**
 * 自动保存 Composable
 * @param saveFn 保存函数，返回 Promise
 * @param options 配置选项
 */
export function useAutoSave(
  saveFn: () => Promise<void>,
  options: UseAutoSaveOptions = {}
): UseAutoSaveReturn {
  const {
    debounceMs = 2000,
    savedDuration = 3000,
    enabled = true,
  } = options

  // 状态
  const status = ref<SaveStatus>('idle')
  const hasUnsavedChanges = ref(false)
  const lastSavedAt = ref<Date | null>(null)
  const error = ref<string | null>(null)

  // 保存成功后重置状态的定时器
  let savedTimer: ReturnType<typeof setTimeout> | null = null

  // 清除定时器
  const clearSavedTimer = () => {
    if (savedTimer) {
      clearTimeout(savedTimer)
      savedTimer = null
    }
  }

  // 执行保存
  const doSave = async () => {
    if (!enabled || !hasUnsavedChanges.value) return

    clearSavedTimer()
    status.value = 'saving'
    error.value = null

    try {
      await saveFn()
      status.value = 'saved'
      hasUnsavedChanges.value = false
      lastSavedAt.value = new Date()

      // 一段时间后重置为 idle 状态
      savedTimer = setTimeout(() => {
        if (status.value === 'saved') {
          status.value = 'idle'
        }
      }, savedDuration)
    } catch (e) {
      status.value = 'error'
      error.value = e instanceof Error ? e.message : '保存失败'
      console.error('Auto save error:', e)
    }
  }

  // 防抖保存
  const debouncedSave = useDebounceFn(doSave, debounceMs)

  // 取消防抖保存
  const cancelDebouncedSave = () => {
    if (typeof debouncedSave.cancel === 'function') {
      debouncedSave.cancel()
    }
  }

  // 标记内容已更改
  const markChanged = () => {
    if (!enabled) return
    
    hasUnsavedChanges.value = true
    status.value = 'unsaved'
    error.value = null
    
    // 触发防抖保存
    debouncedSave()
  }

  // 手动保存（立即执行，不防抖，强制保存）
  const save = async () => {
    // 取消待执行的防抖保存
    cancelDebouncedSave()
    
    // 强制执行保存，不检查 hasUnsavedChanges
    clearSavedTimer()
    status.value = 'saving'
    error.value = null

    try {
      await saveFn()
      status.value = 'saved'
      hasUnsavedChanges.value = false
      lastSavedAt.value = new Date()

      // 一段时间后重置为 idle 状态
      savedTimer = setTimeout(() => {
        if (status.value === 'saved') {
          status.value = 'idle'
        }
      }, savedDuration)
    } catch (e) {
      status.value = 'error'
      error.value = e instanceof Error ? e.message : '保存失败'
      console.error('Manual save error:', e)
      throw e
    }
  }

  // 重置状态
  const reset = () => {
    clearSavedTimer()
    cancelDebouncedSave()
    status.value = 'idle'
    hasUnsavedChanges.value = false
    lastSavedAt.value = null
    error.value = null
  }

  // 状态文本
  const statusText = computed(() => {
    switch (status.value) {
      case 'saving':
        return '保存中...'
      case 'saved':
        return '已保存'
      case 'error':
        return error.value || '保存失败'
      case 'unsaved':
        return '未保存'
      default:
        return ''
    }
  })

  // 状态图标
  const statusIcon = computed(() => {
    switch (status.value) {
      case 'saving':
        return 'i-lucide-loader-2'
      case 'saved':
        return 'i-lucide-check'
      case 'error':
        return 'i-lucide-alert-circle'
      case 'unsaved':
        return 'i-lucide-circle'
      default:
        return ''
    }
  })

  // 状态颜色
  const statusColor = computed(() => {
    switch (status.value) {
      case 'saving':
        return 'text-gray-500'
      case 'saved':
        return 'text-emerald-500'
      case 'error':
        return 'text-red-500'
      case 'unsaved':
        return 'text-amber-500'
      default:
        return 'text-gray-400'
    }
  })

  // 组件卸载时清理
  onUnmounted(() => {
    clearSavedTimer()
    cancelDebouncedSave()
  })

  // 页面离开前提示
  if (import.meta.client) {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges.value) {
        e.preventDefault()
        e.returnValue = '您有未保存的更改，确定要离开吗？'
        return e.returnValue
      }
    }

    onMounted(() => {
      window.addEventListener('beforeunload', handleBeforeUnload)
    })

    onUnmounted(() => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
    })
  }

  return {
    status,
    hasUnsavedChanges,
    lastSavedAt,
    error,
    markChanged,
    save,
    reset,
    statusText,
    statusIcon,
    statusColor,
  }
}
