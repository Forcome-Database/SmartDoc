/**
 * 图片上传扩展
 * 支持拖拽上传和粘贴上传
 */
import { Extension } from '@tiptap/core'
import { Plugin, PluginKey } from '@tiptap/pm/state'
import type { EditorView } from '@tiptap/pm/view'

export interface ImageUploadOptions {
  /**
   * 允许的图片类型
   */
  allowedMimeTypes: string[]
  /**
   * 最大文件大小（字节）
   */
  maxFileSize: number
  /**
   * 上传函数
   */
  uploadFn: (file: File) => Promise<string>
  /**
   * 上传开始回调
   */
  onUploadStart?: () => void
  /**
   * 上传成功回调
   */
  onUploadSuccess?: (url: string) => void
  /**
   * 上传失败回调
   */
  onUploadError?: (error: Error) => void
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    imageUpload: {
      /**
       * 上传图片
       */
      uploadImage: (file: File) => ReturnType
      /**
       * 打开图片选择器
       */
      openImagePicker: () => ReturnType
    }
  }
}

/**
 * 默认上传函数
 */
async function defaultUploadFn(file: File): Promise<string> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch('/api/upload?type=image', {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || '上传失败')
  }

  const result = await response.json()
  return result.data.url
}

/**
 * 验证文件
 */
function validateFile(
  file: File,
  allowedMimeTypes: string[],
  maxFileSize: number
): { valid: boolean; error?: string } {
  if (!allowedMimeTypes.includes(file.type)) {
    return { valid: false, error: `不支持的图片格式: ${file.type}` }
  }

  if (file.size > maxFileSize) {
    const maxSizeMB = maxFileSize / (1024 * 1024)
    return { valid: false, error: `图片大小超过限制 (最大 ${maxSizeMB}MB)` }
  }

  return { valid: true }
}

/**
 * 处理文件上传
 */
async function handleFileUpload(
  view: EditorView,
  file: File,
  pos: number | null,
  options: ImageUploadOptions
): Promise<void> {
  const { allowedMimeTypes, maxFileSize, uploadFn, onUploadStart, onUploadSuccess, onUploadError } = options

  // 验证文件
  const validation = validateFile(file, allowedMimeTypes, maxFileSize)
  if (!validation.valid) {
    onUploadError?.(new Error(validation.error))
    return
  }

  // 创建占位符
  const placeholderId = `image-upload-${Date.now()}`
  const placeholderUrl = URL.createObjectURL(file)

  // 插入占位图片
  const { schema } = view.state
  const imageNode = schema.nodes.image?.create({
    src: placeholderUrl,
    alt: file.name,
    title: '上传中...',
    'data-placeholder-id': placeholderId,
  })

  if (!imageNode) {
    onUploadError?.(new Error('编辑器不支持图片节点'))
    return
  }

  // 确定插入位置
  const insertPos = pos ?? view.state.selection.from
  const tr = view.state.tr.insert(insertPos, imageNode)
  view.dispatch(tr)

  onUploadStart?.()

  try {
    // 上传文件
    const url = await uploadFn(file)

    // 查找并替换占位图片
    const { doc } = view.state
    let foundPos: number | null = null

    doc.descendants((node, nodePos) => {
      if (
        node.type.name === 'image' &&
        node.attrs['data-placeholder-id'] === placeholderId
      ) {
        foundPos = nodePos
        return false
      }
      return true
    })

    if (foundPos !== null) {
      const newTr = view.state.tr.setNodeMarkup(foundPos, undefined, {
        src: url,
        alt: file.name,
        title: file.name,
      })
      view.dispatch(newTr)
    }

    // 释放 blob URL
    URL.revokeObjectURL(placeholderUrl)

    onUploadSuccess?.(url)
  } catch (error) {
    // 上传失败，移除占位图片
    const { doc } = view.state
    let foundPos: number | null = null

    doc.descendants((node, nodePos) => {
      if (
        node.type.name === 'image' &&
        node.attrs['data-placeholder-id'] === placeholderId
      ) {
        foundPos = nodePos
        return false
      }
      return true
    })

    if (foundPos !== null) {
      const newTr = view.state.tr.delete(foundPos, foundPos + 1)
      view.dispatch(newTr)
    }

    // 释放 blob URL
    URL.revokeObjectURL(placeholderUrl)

    onUploadError?.(error instanceof Error ? error : new Error('上传失败'))
  }
}

/**
 * 图片上传扩展
 */
export const ImageUpload = Extension.create<ImageUploadOptions>({
  name: 'imageUpload',

  addOptions() {
    return {
      allowedMimeTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'],
      maxFileSize: 10 * 1024 * 1024, // 10MB
      uploadFn: defaultUploadFn,
      onUploadStart: undefined,
      onUploadSuccess: undefined,
      onUploadError: undefined,
    }
  },

  addCommands() {
    return {
      uploadImage:
        (file: File) =>
        ({ view }) => {
          handleFileUpload(view, file, null, this.options)
          return true
        },
      openImagePicker:
        () =>
        ({ view }) => {
          const input = document.createElement('input')
          input.type = 'file'
          input.accept = this.options.allowedMimeTypes.join(',')
          input.onchange = () => {
            const file = input.files?.[0]
            if (file) {
              handleFileUpload(view, file, null, this.options)
            }
          }
          input.click()
          return true
        },
    }
  },

  addProseMirrorPlugins() {
    const options = this.options

    return [
      new Plugin({
        key: new PluginKey('imageUpload'),
        props: {
          // 处理拖拽
          handleDrop(view, event, _slice, moved) {
            // 如果是移动操作，不处理
            if (moved) return false

            const files = event.dataTransfer?.files
            if (!files || files.length === 0) return false

            // 过滤图片文件
            const imageFiles = Array.from(files).filter((file) =>
              options.allowedMimeTypes.includes(file.type)
            )

            if (imageFiles.length === 0) return false

            event.preventDefault()

            // 获取拖拽位置
            const coordinates = view.posAtCoords({
              left: event.clientX,
              top: event.clientY,
            })
            const pos = coordinates?.pos ?? null

            // 上传所有图片
            imageFiles.forEach((file) => {
              handleFileUpload(view, file, pos, options)
            })

            return true
          },

          // 处理粘贴
          handlePaste(view, event) {
            const items = event.clipboardData?.items
            if (!items) return false

            // 查找图片文件
            const imageItems = Array.from(items).filter(
              (item) =>
                item.kind === 'file' &&
                options.allowedMimeTypes.includes(item.type)
            )

            if (imageItems.length === 0) return false

            event.preventDefault()

            // 上传所有图片
            imageItems.forEach((item) => {
              const file = item.getAsFile()
              if (file) {
                handleFileUpload(view, file, null, options)
              }
            })

            return true
          },
        },
      }),
    ]
  },
})

export default ImageUpload
