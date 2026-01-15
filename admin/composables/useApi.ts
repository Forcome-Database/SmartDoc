/**
 * API 请求 Composable
 * 提供带重试机制和错误处理的 API 请求封装
 * 
 * @requirements 11.5
 */
import { useNotify } from './useNotify'
import { useGlobalLoading } from './useLoading'

// FetchError 类型定义
interface FetchError extends Error {
  response?: Response
  data?: {
    message?: string
    statusMessage?: string
  }
}

export interface ApiRequestOptions {
  /** HTTP 方法 */
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  /** 请求体 */
  body?: Record<string, any> | FormData
  /** 查询参数 */
  query?: Record<string, any>
  /** 请求头 */
  headers?: Record<string, string>
  /** 重试次数 */
  retries?: number
  /** 重试延迟（毫秒） */
  retryDelay?: number
  /** 是否在重试时显示通知 */
  showRetryNotification?: boolean
  /** 成功时的通知消息 */
  successMessage?: string
  /** 错误时的通知消息 */
  errorMessage?: string
  /** 是否显示加载状态 */
  showLoading?: boolean
  /** 加载文本 */
  loadingText?: string
}

export interface ApiResponse<T> {
  /** 响应数据 */
  data: T | null
  /** 错误信息 */
  error: Error | null
  /** 是否成功 */
  success: boolean
}

/**
 * 判断是否为可重试的错误
 */
const isRetryableError = (error: FetchError): boolean => {
  // 网络错误
  if (!error.response) {
    return true
  }
  
  // 服务器错误（5xx）
  const status = error.response.status
  if (status >= 500 && status < 600) {
    return true
  }
  
  // 请求超时
  if (status === 408 || status === 429) {
    return true
  }
  
  return false
}

/**
 * 延迟函数
 */
const delay = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * API 请求 Composable
 * 提供统一的 API 请求接口，支持重试、错误处理和通知
 */
export function useApi() {
  const notify = useNotify()
  const globalLoading = useGlobalLoading()

  /**
   * 发起 API 请求
   */
  const request = async <T>(
    url: string,
    options: ApiRequestOptions = {}
  ): Promise<ApiResponse<T>> => {
    const {
      retries = 2,
      retryDelay = 1000,
      showRetryNotification = true,
      successMessage,
      errorMessage,
      showLoading = false,
      loadingText,
      method = 'GET',
      body,
      query,
      headers,
    } = options

    let lastError: Error | null = null
    let attempt = 0

    // 显示加载状态
    if (showLoading) {
      globalLoading.start(loadingText)
    }

    try {
      while (attempt <= retries) {
        try {
          const data = await $fetch<T>(url, {
            method,
            body,
            query,
            headers,
          })
          
          // 成功通知
          if (successMessage) {
            notify.success(successMessage)
          }
          
          return {
            data,
            error: null,
            success: true,
          }
        } catch (e) {
          lastError = e instanceof Error ? e : new Error(String(e))
          
          // 检查是否可重试
          const fetchError = e as FetchError
          if (attempt < retries && isRetryableError(fetchError)) {
            attempt++
            
            // 显示重试通知
            if (showRetryNotification) {
              notify.warning({
                title: '请求失败，正在重试...',
                description: `第 ${attempt} 次重试`,
                duration: retryDelay,
              })
            }
            
            // 等待后重试
            await delay(retryDelay * attempt) // 指数退避
          } else {
            break
          }
        }
      }

      // 所有重试都失败
      const message = errorMessage || getErrorMessage(lastError)
      notify.error(message)
      
      return {
        data: null,
        error: lastError,
        success: false,
      }
    } finally {
      // 停止加载状态
      if (showLoading) {
        globalLoading.stop()
      }
    }
  }

  /**
   * GET 请求
   */
  const get = <T>(url: string, options?: ApiRequestOptions) => {
    return request<T>(url, { ...options, method: 'GET' })
  }

  /**
   * POST 请求
   */
  const post = <T>(url: string, body?: Record<string, any>, options?: ApiRequestOptions) => {
    return request<T>(url, { ...options, method: 'POST', body })
  }

  /**
   * PATCH 请求
   */
  const patch = <T>(url: string, body?: Record<string, any>, options?: ApiRequestOptions) => {
    return request<T>(url, { ...options, method: 'PATCH', body })
  }

  /**
   * PUT 请求
   */
  const put = <T>(url: string, body?: Record<string, any>, options?: ApiRequestOptions) => {
    return request<T>(url, { ...options, method: 'PUT', body })
  }

  /**
   * DELETE 请求
   */
  const del = <T>(url: string, options?: ApiRequestOptions) => {
    return request<T>(url, { ...options, method: 'DELETE' })
  }

  return {
    request,
    get,
    post,
    patch,
    put,
    del,
  }
}

/**
 * 从错误对象中提取错误消息
 */
export function getErrorMessage(error: unknown, fallback = '操作失败，请稍后重试'): string {
  if (!error) {
    return fallback
  }

  if (typeof error === 'string') {
    return error
  }

  if (error instanceof Error) {
    // 处理 FetchError
    const fetchError = error as FetchError
    if (fetchError.data?.message) {
      return fetchError.data.message
    }
    if (fetchError.data?.statusMessage) {
      return fetchError.data.statusMessage
    }
    return error.message || fallback
  }

  if (typeof error === 'object') {
    const errorObj = error as Record<string, any>
    if (errorObj.data?.message) {
      return errorObj.data.message
    }
    if (errorObj.message) {
      return errorObj.message
    }
    if (errorObj.statusMessage) {
      return errorObj.statusMessage
    }
  }

  return fallback
}

/**
 * 网络错误处理 Composable
 * 提供统一的错误处理和用户输入保留
 */
export function useNetworkErrorHandler() {
  const notify = useNotify()
  
  // 保存的用户输入
  const savedInputs = reactive<Record<string, any>>({})

  /**
   * 保存用户输入
   */
  const saveInput = (key: string, value: any) => {
    savedInputs[key] = JSON.parse(JSON.stringify(value))
  }

  /**
   * 获取保存的输入
   */
  const getSavedInput = <T>(key: string): T | undefined => {
    return savedInputs[key] as T | undefined
  }

  /**
   * 清除保存的输入
   */
  const clearSavedInput = (key: string) => {
    delete savedInputs[key]
  }

  /**
   * 清除所有保存的输入
   */
  const clearAllSavedInputs = () => {
    Object.keys(savedInputs).forEach(key => {
      delete savedInputs[key]
    })
  }

  /**
   * 处理网络错误
   */
  const handleNetworkError = (
    error: unknown,
    options?: {
      /** 输入保存的 key */
      inputKey?: string
      /** 要保存的输入值 */
      inputValue?: any
      /** 重试回调 */
      onRetry?: () => void
      /** 自定义错误消息 */
      errorMessage?: string
    }
  ) => {
    const message = getErrorMessage(error, options?.errorMessage)
    
    // 保存用户输入
    if (options?.inputKey && options?.inputValue !== undefined) {
      saveInput(options.inputKey, options.inputValue)
    }

    // 显示错误通知
    if (options?.onRetry) {
      notify.error({
        title: message,
        description: '您的输入已保存，可以点击重试',
        duration: 0, // 不自动关闭
        actions: [
          {
            label: '重试',
            onClick: options.onRetry,
          },
        ],
      })
    } else {
      notify.error(message)
    }
  }

  /**
   * 包装异步操作，自动处理错误和保存输入
   */
  const wrapWithErrorHandling = async <T>(
    fn: () => Promise<T>,
    options?: {
      inputKey?: string
      inputValue?: any
      onRetry?: () => void
      errorMessage?: string
      successMessage?: string
    }
  ): Promise<T | null> => {
    try {
      const result = await fn()
      
      // 成功后清除保存的输入
      if (options?.inputKey) {
        clearSavedInput(options.inputKey)
      }
      
      // 显示成功通知
      if (options?.successMessage) {
        notify.success(options.successMessage)
      }
      
      return result
    } catch (error) {
      handleNetworkError(error, options)
      return null
    }
  }

  return {
    savedInputs,
    saveInput,
    getSavedInput,
    clearSavedInput,
    clearAllSavedInputs,
    handleNetworkError,
    wrapWithErrorHandling,
  }
}
