/**
 * 视频扩展
 * 支持视频上传和播放
 */
import { Node, mergeAttributes } from '@tiptap/core'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import VideoView from '../VideoView.vue'

export interface VideoOptions {
  /**
   * 允许的视频类型
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
   * HTML 属性
   */
  HTMLAttributes: Record<string, any>
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    video: {
      /**
       * 设置视频
       */
      setVideo: (options: { src: string; title?: string }) => ReturnType
      /**
       * 上传视频
       */
      uploadVideo: (file: File) => ReturnType
      /**
       * 打开视频选择器
       */
      openVideoPicker: () => ReturnType
    }
  }
}

/**
 * 默认上传函数
 */
async function defaultUploadFn(file: File): Promise<string> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch('/api/upload?type=video', {
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
 * 视频节点扩展
 */
export const Video = Node.create<VideoOptions>({
  name: 'video',
  group: 'block',
  atom: true,
  draggable: true,

  addOptions() {
    return {
      allowedMimeTypes: ['video/mp4', 'video/webm', 'video/ogg', 'video/quicktime'],
      maxFileSize: 100 * 1024 * 1024, // 100MB
      uploadFn: defaultUploadFn,
      HTMLAttributes: {},
    }
  },

  addAttributes() {
    return {
      src: {
        default: null,
      },
      title: {
        default: null,
      },
      width: {
        default: '100%',
      },
      height: {
        default: 'auto',
      },
      controls: {
        default: true,
      },
      autoplay: {
        default: false,
      },
      loop: {
        default: false,
      },
      muted: {
        default: false,
      },
      poster: {
        default: null,
      },
      uploading: {
        default: false,
      },
      uploadProgress: {
        default: 0,
      },
    }
  },

  parseHTML() {
    return [
      {
        tag: 'video[src]',
      },
      {
        tag: 'div[data-video]',
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'div',
      mergeAttributes(this.options.HTMLAttributes, { 'data-video': '' }),
      [
        'video',
        mergeAttributes(HTMLAttributes, {
          controls: HTMLAttributes.controls,
          autoplay: HTMLAttributes.autoplay,
          loop: HTMLAttributes.loop,
          muted: HTMLAttributes.muted,
        }),
      ],
    ]
  },

  addNodeView() {
    return VueNodeViewRenderer(VideoView)
  },

  addCommands() {
    return {
      setVideo:
        (options) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs: options,
          })
        },
      uploadVideo:
        (file: File) =>
        ({ commands, editor }) => {
          const { allowedMimeTypes, maxFileSize, uploadFn } = this.options

          // 验证文件类型
          if (!allowedMimeTypes.includes(file.type)) {
            console.error(`不支持的视频格式: ${file.type}`)
            return false
          }

          // 验证文件大小
          if (file.size > maxFileSize) {
            const maxSizeMB = maxFileSize / (1024 * 1024)
            console.error(`视频大小超过限制 (最大 ${maxSizeMB}MB)`)
            return false
          }

          // 创建临时 URL 用于预览
          const tempUrl = URL.createObjectURL(file)

          // 插入上传中的视频节点
          commands.insertContent({
            type: this.name,
            attrs: {
              src: tempUrl,
              title: file.name,
              uploading: true,
              uploadProgress: 0,
            },
          })

          // 异步上传
          uploadFn(file)
            .then((url) => {
              // 查找并更新视频节点
              const { doc, tr } = editor.state
              let foundPos: number | null = null

              doc.descendants((node, pos) => {
                if (
                  node.type.name === 'video' &&
                  node.attrs.src === tempUrl
                ) {
                  foundPos = pos
                  return false
                }
                return true
              })

              if (foundPos !== null) {
                const newTr = tr.setNodeMarkup(foundPos, undefined, {
                  src: url,
                  title: file.name,
                  uploading: false,
                  uploadProgress: 100,
                })
                editor.view.dispatch(newTr)
              }

              URL.revokeObjectURL(tempUrl)
            })
            .catch((error) => {
              console.error('视频上传失败:', error)
              // 移除失败的视频节点
              const { doc, tr } = editor.state
              let foundPos: number | null = null

              doc.descendants((node, pos) => {
                if (
                  node.type.name === 'video' &&
                  node.attrs.src === tempUrl
                ) {
                  foundPos = pos
                  return false
                }
                return true
              })

              if (foundPos !== null) {
                const newTr = tr.delete(foundPos, foundPos + 1)
                editor.view.dispatch(newTr)
              }

              URL.revokeObjectURL(tempUrl)
            })

          return true
        },
      openVideoPicker:
        () =>
        ({ commands }) => {
          const input = document.createElement('input')
          input.type = 'file'
          input.accept = this.options.allowedMimeTypes.join(',')
          input.onchange = () => {
            const file = input.files?.[0]
            if (file) {
              commands.uploadVideo(file)
            }
          }
          input.click()
          return true
        },
    }
  },
})

export default Video
