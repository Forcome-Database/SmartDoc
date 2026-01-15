/**
 * 评论 Composable
 * 管理文档评论的获取、添加、更新和删除
 * 
 * Requirements: 13.9
 */

export interface CommentAuthor {
  id: string
  name: string
  avatar?: string | null
}

export interface Comment {
  id: string
  documentId: string
  parentId?: string | null
  content: string
  mentions: string[]
  isResolved: boolean
  createdAt: Date
  updatedAt: Date
  author: CommentAuthor
  replies?: Comment[]
}

export interface UseCommentsOptions {
  /** 是否只显示未解决的评论 */
  unresolvedOnly?: boolean
  /** 是否自动加载 */
  autoLoad?: boolean
}

export interface UseCommentsReturn {
  /** 评论列表 */
  comments: Ref<Comment[]>
  /** 评论总数 */
  total: Ref<number>
  /** 是否正在加载 */
  loading: Ref<boolean>
  /** 错误信息 */
  error: Ref<string | null>
  /** 加载评论 */
  load: () => Promise<void>
  /** 添加评论 */
  add: (content: string, options?: { parentId?: string; mentions?: string[] }) => Promise<Comment | null>
  /** 更新评论 */
  update: (commentId: string, data: { content?: string; isResolved?: boolean }) => Promise<Comment | null>
  /** 删除评论 */
  remove: (commentId: string) => Promise<boolean>
  /** 标记为已解决 */
  resolve: (commentId: string) => Promise<boolean>
  /** 标记为未解决 */
  unresolve: (commentId: string) => Promise<boolean>
}

/**
 * 评论 Composable
 * @param documentId 文档 ID（响应式）
 * @param options 配置选项
 */
export function useComments(
  documentId: MaybeRef<string>,
  options: UseCommentsOptions = {}
): UseCommentsReturn {
  const {
    unresolvedOnly = false,
    autoLoad = true,
  } = options

  // 状态
  const comments = ref<Comment[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 获取文档 ID
  const getDocumentId = () => toValue(documentId)

  // 格式化评论日期
  const formatComment = (comment: any): Comment => ({
    ...comment,
    createdAt: new Date(comment.createdAt),
    updatedAt: new Date(comment.updatedAt),
    replies: comment.replies?.map(formatComment) || [],
  })

  // 加载评论
  const load = async () => {
    const docId = getDocumentId()
    if (!docId) return

    loading.value = true
    error.value = null

    try {
      const response = await $fetch<{
        comments: Comment[]
        total: number
      }>(`/api/documents/${docId}/comments`, {
        query: {
          unresolvedOnly: unresolvedOnly ? 'true' : undefined,
        },
      })

      comments.value = response.comments.map(formatComment)
      total.value = response.total
    } catch (e: any) {
      error.value = e.message || '加载评论失败'
      console.error('Load comments error:', e)
    } finally {
      loading.value = false
    }
  }

  // 添加评论
  const add = async (
    content: string,
    opts?: { parentId?: string; mentions?: string[] }
  ): Promise<Comment | null> => {
    const docId = getDocumentId()
    if (!docId) return null

    try {
      const response = await $fetch<{ comment: Comment }>(
        `/api/documents/${docId}/comments`,
        {
          method: 'POST',
          body: {
            content,
            parentId: opts?.parentId,
            mentions: opts?.mentions,
          },
        }
      )

      const newComment = formatComment(response.comment)

      // 如果是回复，添加到父评论的 replies 中
      if (opts?.parentId) {
        const parentIndex = comments.value.findIndex(c => c.id === opts.parentId)
        if (parentIndex !== -1) {
          if (!comments.value[parentIndex].replies) {
            comments.value[parentIndex].replies = []
          }
          comments.value[parentIndex].replies!.push(newComment)
        }
      } else {
        // 顶级评论，添加到列表开头
        comments.value.unshift(newComment)
        total.value++
      }

      return newComment
    } catch (e: any) {
      error.value = e.message || '添加评论失败'
      console.error('Add comment error:', e)
      return null
    }
  }

  // 更新评论
  const update = async (
    commentId: string,
    data: { content?: string; isResolved?: boolean }
  ): Promise<Comment | null> => {
    const docId = getDocumentId()
    if (!docId) return null

    try {
      const response = await $fetch<{ comment: Comment }>(
        `/api/documents/${docId}/comments/${commentId}`,
        {
          method: 'PATCH',
          body: data,
        }
      )

      const updatedComment = formatComment(response.comment)

      // 更新本地状态
      const updateInList = (list: Comment[]): boolean => {
        for (let i = 0; i < list.length; i++) {
          if (list[i].id === commentId) {
            list[i] = { ...list[i], ...updatedComment }
            return true
          }
          if (list[i].replies && updateInList(list[i].replies!)) {
            return true
          }
        }
        return false
      }

      updateInList(comments.value)

      return updatedComment
    } catch (e: any) {
      error.value = e.message || '更新评论失败'
      console.error('Update comment error:', e)
      return null
    }
  }

  // 删除评论
  const remove = async (commentId: string): Promise<boolean> => {
    const docId = getDocumentId()
    if (!docId) return false

    try {
      await $fetch(`/api/documents/${docId}/comments/${commentId}`, {
        method: 'DELETE',
      })

      // 从本地状态中移除
      const removeFromList = (list: Comment[]): boolean => {
        for (let i = 0; i < list.length; i++) {
          if (list[i].id === commentId) {
            list.splice(i, 1)
            return true
          }
          if (list[i].replies && removeFromList(list[i].replies!)) {
            return true
          }
        }
        return false
      }

      if (removeFromList(comments.value)) {
        total.value--
      }

      return true
    } catch (e: any) {
      error.value = e.message || '删除评论失败'
      console.error('Delete comment error:', e)
      return false
    }
  }

  // 标记为已解决
  const resolve = async (commentId: string): Promise<boolean> => {
    const result = await update(commentId, { isResolved: true })
    return result !== null
  }

  // 标记为未解决
  const unresolve = async (commentId: string): Promise<boolean> => {
    const result = await update(commentId, { isResolved: false })
    return result !== null
  }

  // 监听文档 ID 变化
  watch(
    () => getDocumentId(),
    (newId, oldId) => {
      if (newId !== oldId) {
        comments.value = []
        total.value = 0
        error.value = null
        if (newId && autoLoad) {
          load()
        }
      }
    }
  )

  // 自动加载
  if (autoLoad) {
    onMounted(() => {
      if (getDocumentId()) {
        load()
      }
    })
  }

  return {
    comments,
    total,
    loading,
    error,
    load,
    add,
    update,
    remove,
    resolve,
    unresolve,
  }
}
