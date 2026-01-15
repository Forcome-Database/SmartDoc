/**
 * 加载状态管理 Composable
 * 提供全局和局部加载状态管理
 * 
 * @requirements 11.3
 */

export interface LoadingState {
  /** 是否正在加载 */
  isLoading: Ref<boolean>
  /** 加载文本 */
  loadingText: Ref<string>
  /** 开始加载 */
  start: (text?: string) => void
  /** 结束加载 */
  stop: () => void
  /** 包装异步函数，自动管理加载状态 */
  wrap: <T>(fn: () => Promise<T>, text?: string) => Promise<T>
}

// 全局加载状态
const globalLoading = ref(false)
const globalLoadingText = ref('')

/**
 * 全局加载状态 Composable
 * 用于页面级别的加载指示器
 */
export function useGlobalLoading(): LoadingState {
  const start = (text = '加载中...') => {
    globalLoading.value = true
    globalLoadingText.value = text
  }

  const stop = () => {
    globalLoading.value = false
    globalLoadingText.value = ''
  }

  const wrap = async <T>(fn: () => Promise<T>, text?: string): Promise<T> => {
    start(text)
    try {
      return await fn()
    } finally {
      stop()
    }
  }

  return {
    isLoading: globalLoading,
    loadingText: globalLoadingText,
    start,
    stop,
    wrap,
  }
}

/**
 * 局部加载状态 Composable
 * 用于组件级别的加载状态管理
 */
export function useLoading(initialText = '加载中...'): LoadingState {
  const isLoading = ref(false)
  const loadingText = ref(initialText)

  const start = (text?: string) => {
    isLoading.value = true
    if (text) {
      loadingText.value = text
    }
  }

  const stop = () => {
    isLoading.value = false
  }

  const wrap = async <T>(fn: () => Promise<T>, text?: string): Promise<T> => {
    start(text)
    try {
      return await fn()
    } finally {
      stop()
    }
  }

  return {
    isLoading,
    loadingText,
    start,
    stop,
    wrap,
  }
}

/**
 * 按钮加载状态 Composable
 * 用于管理多个按钮的加载状态
 */
export function useButtonLoading() {
  const loadingStates = reactive<Record<string, boolean>>({})

  /**
   * 检查按钮是否正在加载
   */
  const isLoading = (key: string): boolean => {
    return loadingStates[key] ?? false
  }

  /**
   * 设置按钮加载状态
   */
  const setLoading = (key: string, loading: boolean) => {
    loadingStates[key] = loading
  }

  /**
   * 包装异步函数，自动管理按钮加载状态
   */
  const wrap = async <T>(key: string, fn: () => Promise<T>): Promise<T> => {
    setLoading(key, true)
    try {
      return await fn()
    } finally {
      setLoading(key, false)
    }
  }

  /**
   * 创建按钮加载状态的响应式引用
   */
  const createRef = (key: string): ComputedRef<boolean> => {
    return computed(() => loadingStates[key] ?? false)
  }

  return {
    loadingStates,
    isLoading,
    setLoading,
    wrap,
    createRef,
  }
}

/**
 * 异步操作状态 Composable
 * 提供完整的异步操作状态管理（加载、错误、数据）
 */
export function useAsyncState<T>(
  initialValue: T,
  options?: {
    immediate?: boolean
    onError?: (error: unknown) => void
  }
) {
  const data = ref<T>(initialValue) as Ref<T>
  const isLoading = ref(false)
  const error = ref<Error | null>(null)
  const isReady = ref(false)

  /**
   * 执行异步操作
   */
  const execute = async (fn: () => Promise<T>): Promise<T | null> => {
    isLoading.value = true
    error.value = null

    try {
      const result = await fn()
      data.value = result
      isReady.value = true
      return result
    } catch (e) {
      error.value = e instanceof Error ? e : new Error(String(e))
      options?.onError?.(e)
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 重置状态
   */
  const reset = () => {
    data.value = initialValue
    isLoading.value = false
    error.value = null
    isReady.value = false
  }

  return {
    data,
    isLoading,
    error,
    isReady,
    execute,
    reset,
  }
}
