/**
 * 通知系统 Composable
 * 封装 Nuxt UI Toast，提供便捷的通知方法
 * 
 * @requirements 11.1, 11.2
 */

export interface NotifyOptions {
  /** 通知标题 */
  title?: string
  /** 通知描述 */
  description?: string
  /** 持续时间（毫秒），0 表示不自动关闭 */
  duration?: number
  /** 是否可关闭 */
  closable?: boolean
  /** 操作按钮 */
  actions?: Array<{
    label: string
    onClick: () => void
    color?: string
  }>
}

export interface NotifyReturn {
  /** 显示成功通知 */
  success: (options: NotifyOptions | string) => void
  /** 显示错误通知 */
  error: (options: NotifyOptions | string) => void
  /** 显示警告通知 */
  warning: (options: NotifyOptions | string) => void
  /** 显示信息通知 */
  info: (options: NotifyOptions | string) => void
  /** 显示加载中通知，返回更新和关闭方法 */
  loading: (options: NotifyOptions | string) => {
    update: (newOptions: NotifyOptions) => void
    close: () => void
    toSuccess: (options: NotifyOptions | string) => void
    toError: (options: NotifyOptions | string) => void
  }
  /** 清除所有通知 */
  clear: () => void
  /** 处理 API 错误并显示通知 */
  handleError: (error: unknown, fallbackMessage?: string) => void
}

/**
 * 通知系统 Composable
 * 提供统一的通知接口，支持成功、错误、警告、信息和加载状态
 */
export function useNotify(): NotifyReturn {
  const toast = useToast()

  /**
   * 规范化选项
   */
  const normalizeOptions = (options: NotifyOptions | string): NotifyOptions => {
    if (typeof options === 'string') {
      return { title: options }
    }
    return options
  }

  /**
   * 显示成功通知
   */
  const success = (options: NotifyOptions | string) => {
    const opts = normalizeOptions(options)
    toast.add({
      title: opts.title || '操作成功',
      description: opts.description,
      color: 'success',
      duration: opts.duration ?? 3000,
      close: opts.closable !== false,
      actions: opts.actions?.map(action => ({
        label: action.label,
        onClick: action.onClick,
        color: action.color as any,
      })),
    })
  }

  /**
   * 显示错误通知
   */
  const error = (options: NotifyOptions | string) => {
    const opts = normalizeOptions(options)
    toast.add({
      title: opts.title || '操作失败',
      description: opts.description,
      color: 'error',
      duration: opts.duration ?? 5000, // 错误通知显示更长时间
      close: opts.closable !== false,
      actions: opts.actions?.map(action => ({
        label: action.label,
        onClick: action.onClick,
        color: action.color as any,
      })),
    })
  }

  /**
   * 显示警告通知
   */
  const warning = (options: NotifyOptions | string) => {
    const opts = normalizeOptions(options)
    toast.add({
      title: opts.title || '警告',
      description: opts.description,
      color: 'warning',
      duration: opts.duration ?? 4000,
      close: opts.closable !== false,
      actions: opts.actions?.map(action => ({
        label: action.label,
        onClick: action.onClick,
        color: action.color as any,
      })),
    })
  }

  /**
   * 显示信息通知
   */
  const info = (options: NotifyOptions | string) => {
    const opts = normalizeOptions(options)
    toast.add({
      title: opts.title || '提示',
      description: opts.description,
      color: 'info',
      duration: opts.duration ?? 3000,
      close: opts.closable !== false,
      actions: opts.actions?.map(action => ({
        label: action.label,
        onClick: action.onClick,
        color: action.color as any,
      })),
    })
  }

  /**
   * 显示加载中通知
   * 返回更新和关闭方法，用于异步操作
   */
  const loading = (options: NotifyOptions | string) => {
    const opts = normalizeOptions(options)
    const id = Date.now()
    
    toast.add({
      id,
      title: opts.title || '处理中...',
      description: opts.description,
      color: 'neutral',
      duration: 0, // 不自动关闭
      close: false, // 不显示关闭按钮
    })

    return {
      /** 更新通知内容 */
      update: (newOptions: NotifyOptions) => {
        const newOpts = normalizeOptions(newOptions)
        toast.update(id, {
          title: newOpts.title,
          description: newOpts.description,
        })
      },
      /** 关闭通知 */
      close: () => {
        toast.remove(id)
      },
      /** 转换为成功通知 */
      toSuccess: (successOptions: NotifyOptions | string) => {
        toast.remove(id)
        success(successOptions)
      },
      /** 转换为错误通知 */
      toError: (errorOptions: NotifyOptions | string) => {
        toast.remove(id)
        error(errorOptions)
      },
    }
  }

  /**
   * 清除所有通知
   */
  const clear = () => {
    toast.clear()
  }

  /**
   * 处理 API 错误并显示通知
   * 自动提取错误信息
   */
  const handleError = (err: unknown, fallbackMessage = '操作失败，请稍后重试') => {
    let message = fallbackMessage
    let description: string | undefined

    if (err instanceof Error) {
      message = err.message || fallbackMessage
    } else if (typeof err === 'object' && err !== null) {
      // 处理 Nuxt/H3 错误格式
      const errorObj = err as Record<string, any>
      if (errorObj.data?.message) {
        message = errorObj.data.message
      } else if (errorObj.message) {
        message = errorObj.message
      }
      if (errorObj.data?.statusMessage) {
        description = errorObj.data.statusMessage
      }
    } else if (typeof err === 'string') {
      message = err
    }

    error({
      title: message,
      description,
    })
  }

  return {
    success,
    error,
    warning,
    info,
    loading,
    clear,
    handleError,
  }
}
