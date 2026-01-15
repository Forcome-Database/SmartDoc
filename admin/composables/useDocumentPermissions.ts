/**
 * 文档权限 Composable
 * 管理文档的权限设置
 * 
 * Requirements: 13.12
 */

export type PermissionLevel = 'view' | 'edit' | 'admin'
export type PermissionTargetType = 'user' | 'department'

export interface PermissionUser {
  id: string
  name: string
  avatar?: string | null
}

export interface DocumentPermission {
  id: string
  documentId: string
  targetType: PermissionTargetType
  targetId: string
  level: PermissionLevel
  createdAt: Date
  updatedAt: Date
  user?: PermissionUser | null
}

export interface UseDocumentPermissionsOptions {
  /** 是否自动加载 */
  autoLoad?: boolean
}

export interface UseDocumentPermissionsReturn {
  /** 权限列表 */
  permissions: Ref<DocumentPermission[]>
  /** 文档作者 ID */
  authorId: Ref<string | null>
  /** 是否正在加载 */
  loading: Ref<boolean>
  /** 错误信息 */
  error: Ref<string | null>
  /** 加载权限 */
  load: () => Promise<void>
  /** 添加权限 */
  add: (targetType: PermissionTargetType, targetId: string, level: PermissionLevel) => Promise<DocumentPermission | null>
  /** 删除权限 */
  remove: (permissionId: string) => Promise<boolean>
}

/**
 * 文档权限 Composable
 */
export function useDocumentPermissions(
  documentId: MaybeRef<string>,
  options: UseDocumentPermissionsOptions = {}
): UseDocumentPermissionsReturn {
  const {
    autoLoad = true,
  } = options

  // 状态
  const permissions = ref<DocumentPermission[]>([])
  const authorId = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 获取文档 ID
  const getDocumentId = () => toValue(documentId)

  // 格式化权限
  const formatPermission = (p: any): DocumentPermission => ({
    ...p,
    createdAt: new Date(p.createdAt),
    updatedAt: new Date(p.updatedAt),
  })

  // 加载权限
  const load = async () => {
    const docId = getDocumentId()
    if (!docId) return

    loading.value = true
    error.value = null

    try {
      const response = await $fetch<{
        permissions: DocumentPermission[]
        authorId: string
      }>(`/api/documents/${docId}/permissions`)

      permissions.value = response.permissions.map(formatPermission)
      authorId.value = response.authorId
    } catch (e: any) {
      error.value = e.message || '加载权限失败'
      console.error('Load permissions error:', e)
    } finally {
      loading.value = false
    }
  }

  // 添加权限
  const add = async (
    targetType: PermissionTargetType,
    targetId: string,
    level: PermissionLevel
  ): Promise<DocumentPermission | null> => {
    const docId = getDocumentId()
    if (!docId) return null

    try {
      const response = await $fetch<{
        permission: DocumentPermission
        updated: boolean
      }>(`/api/documents/${docId}/permissions`, {
        method: 'POST',
        body: {
          targetType,
          targetId,
          level,
        },
      })

      const newPermission = formatPermission(response.permission)

      if (response.updated) {
        // 更新现有权限
        const index = permissions.value.findIndex(
          p => p.targetType === targetType && p.targetId === targetId
        )
        if (index !== -1) {
          permissions.value[index] = newPermission
        }
      } else {
        // 添加新权限
        permissions.value.push(newPermission)
      }

      return newPermission
    } catch (e: any) {
      error.value = e.message || '添加权限失败'
      console.error('Add permission error:', e)
      return null
    }
  }

  // 删除权限
  const remove = async (permissionId: string): Promise<boolean> => {
    const docId = getDocumentId()
    if (!docId) return false

    try {
      await $fetch(`/api/documents/${docId}/permissions/${permissionId}`, {
        method: 'DELETE',
      })

      // 从本地状态中移除
      const index = permissions.value.findIndex(p => p.id === permissionId)
      if (index !== -1) {
        permissions.value.splice(index, 1)
      }

      return true
    } catch (e: any) {
      error.value = e.message || '删除权限失败'
      console.error('Delete permission error:', e)
      return false
    }
  }

  // 监听文档 ID 变化
  watch(
    () => getDocumentId(),
    (newId, oldId) => {
      if (newId !== oldId) {
        permissions.value = []
        authorId.value = null
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
    permissions,
    authorId,
    loading,
    error,
    load,
    add,
    remove,
  }
}

/**
 * 获取权限级别的显示文本
 */
export function getPermissionLevelText(level: PermissionLevel): string {
  const textMap: Record<PermissionLevel, string> = {
    view: '查看',
    edit: '编辑',
    admin: '管理',
  }
  return textMap[level] || level
}

/**
 * 获取权限级别的颜色
 */
export function getPermissionLevelColor(level: PermissionLevel): string {
  const colorMap: Record<PermissionLevel, string> = {
    view: 'neutral',
    edit: 'primary',
    admin: 'warning',
  }
  return colorMap[level] || 'neutral'
}
