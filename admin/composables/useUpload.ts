/**
 * 文件上传 Composable
 * 提供文件上传功能，支持进度跟踪和错误处理
 */

export type FileType = 'image' | 'video' | 'document'

export interface UploadOptions {
  /**
   * 文件类型限制
   */
  type?: FileType
  /**
   * 上传成功回调
   */
  onSuccess?: (result: UploadResult) => void
  /**
   * 上传失败回调
   */
  onError?: (error: Error) => void
  /**
   * 上传进度回调
   */
  onProgress?: (progress: number) => void
}

export interface UploadResult {
  url: string
  objectName: string
  filename: string
  mimeType: string
  size: number
  fileType: FileType
}

export interface UploadState {
  /**
   * 是否正在上传
   */
  uploading: boolean
  /**
   * 上传进度 (0-100)
   */
  progress: number
  /**
   * 错误信息
   */
  error: string | null
  /**
   * 上传结果
   */
  result: UploadResult | null
}

/**
 * 文件上传 Composable
 */
export function useUpload(options: UploadOptions = {}) {
  const { type, onSuccess, onError, onProgress } = options

  // 上传状态
  const state = reactive<UploadState>({
    uploading: false,
    progress: 0,
    error: null,
    result: null,
  })

  // Toast 通知
  const toast = useToast()

  /**
   * 重置状态
   */
  const reset = () => {
    state.uploading = false
    state.progress = 0
    state.error = null
    state.result = null
  }

  /**
   * 上传文件
   */
  const upload = async (file: File): Promise<UploadResult | null> => {
    reset()
    state.uploading = true

    try {
      // 创建 FormData
      const formData = new FormData()
      formData.append('file', file)

      // 构建 URL
      const url = type ? `/api/upload?type=${type}` : '/api/upload'

      // 使用 XMLHttpRequest 以支持进度跟踪
      const result = await new Promise<UploadResult>((resolve, reject) => {
        const xhr = new XMLHttpRequest()

        // 进度事件
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress = Math.round((event.loaded / event.total) * 100)
            state.progress = progress
            onProgress?.(progress)
          }
        })

        // 完成事件
        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const response = JSON.parse(xhr.responseText)
              if (response.success) {
                resolve(response.data)
              } else {
                reject(new Error(response.message || '上传失败'))
              }
            } catch {
              reject(new Error('解析响应失败'))
            }
          } else {
            try {
              const response = JSON.parse(xhr.responseText)
              reject(new Error(response.message || `上传失败 (${xhr.status})`))
            } catch {
              reject(new Error(`上传失败 (${xhr.status})`))
            }
          }
        })

        // 错误事件
        xhr.addEventListener('error', () => {
          reject(new Error('网络错误'))
        })

        // 中止事件
        xhr.addEventListener('abort', () => {
          reject(new Error('上传已取消'))
        })

        // 发送请求
        xhr.open('POST', url)
        xhr.send(formData)
      })

      state.result = result
      state.progress = 100
      onSuccess?.(result)

      toast.add({
        title: '上传成功',
        description: `文件 ${file.name} 已上传`,
        color: 'success',
      })

      return result
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '上传失败'
      state.error = errorMessage
      onError?.(error instanceof Error ? error : new Error(errorMessage))

      toast.add({
        title: '上传失败',
        description: errorMessage,
        color: 'error',
      })

      return null
    } finally {
      state.uploading = false
    }
  }

  /**
   * 打开文件选择器并上传
   */
  const openPicker = (accept?: string): Promise<UploadResult | null> => {
    return new Promise((resolve) => {
      const input = document.createElement('input')
      input.type = 'file'

      // 设置接受的文件类型
      if (accept) {
        input.accept = accept
      } else if (type === 'image') {
        input.accept = 'image/jpeg,image/png,image/gif,image/webp,image/svg+xml'
      } else if (type === 'video') {
        input.accept = 'video/mp4,video/webm,video/ogg,video/quicktime'
      } else if (type === 'document') {
        input.accept = '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.md'
      }

      input.onchange = async () => {
        const file = input.files?.[0]
        if (file) {
          const result = await upload(file)
          resolve(result)
        } else {
          resolve(null)
        }
      }

      input.click()
    })
  }

  /**
   * 上传图片
   */
  const uploadImage = (file: File) => {
    return upload(file)
  }

  /**
   * 上传视频
   */
  const uploadVideo = (file: File) => {
    return upload(file)
  }

  /**
   * 上传文档
   */
  const uploadDocument = (file: File) => {
    return upload(file)
  }

  return {
    // 状态
    uploading: computed(() => state.uploading),
    progress: computed(() => state.progress),
    error: computed(() => state.error),
    result: computed(() => state.result),

    // 方法
    upload,
    openPicker,
    uploadImage,
    uploadVideo,
    uploadDocument,
    reset,
  }
}

/**
 * 图片上传 Composable
 */
export function useImageUpload(options: Omit<UploadOptions, 'type'> = {}) {
  return useUpload({ ...options, type: 'image' })
}

/**
 * 视频上传 Composable
 */
export function useVideoUpload(options: Omit<UploadOptions, 'type'> = {}) {
  return useUpload({ ...options, type: 'video' })
}

/**
 * 文档上传 Composable
 */
export function useDocumentUpload(options: Omit<UploadOptions, 'type'> = {}) {
  return useUpload({ ...options, type: 'document' })
}

export default useUpload
