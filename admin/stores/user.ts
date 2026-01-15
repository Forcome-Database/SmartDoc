/**
 * 用户状态管理
 * 管理用户信息、权限检查和登录状态
 * 
 * Requirements: 1.6, 12.5
 */
import type { UserRole } from '~/types'

// 用户会话信息类型
export interface SessionUser {
  id: string
  name: string
  avatar?: string | null
  email?: string | null
  role: UserRole
  department?: string | null
  dingtalkId: string
  createdAt?: Date | string
  updatedAt?: Date | string
}

// 角色权限层级
const ROLE_HIERARCHY: Record<UserRole, number> = {
  admin: 3,
  editor: 2,
  viewer: 1,
}

export const useUserStore = defineStore('user', () => {
  // 状态
  const user = ref<SessionUser | null>(null)
  const isLoading = ref(false)
  const isInitialized = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const isLoggedIn = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isEditor = computed(() => user.value?.role === 'editor' || user.value?.role === 'admin')
  const canEdit = computed(() => hasRole('editor'))
  const canManage = computed(() => hasRole('admin'))

  // 用户显示名称
  const displayName = computed(() => user.value?.name || '未知用户')

  // 用户头像 URL
  const avatarUrl = computed(() => user.value?.avatar || undefined)

  /**
   * 获取用户信息
   */
  const fetchUser = async (): Promise<SessionUser | null> => {
    if (isLoading.value) return user.value

    isLoading.value = true
    error.value = null

    try {
      const data = await $fetch<SessionUser | null>('/api/auth/session')
      user.value = data
      return data
    } catch (err: any) {
      console.error('Failed to fetch user:', err)
      error.value = err.message || '获取用户信息失败'
      user.value = null
      return null
    } finally {
      isLoading.value = false
      isInitialized.value = true
    }
  }

  /**
   * 初始化用户状态
   * 在应用启动时调用
   */
  const initialize = async () => {
    if (isInitialized.value) return user.value
    return fetchUser()
  }

  /**
   * 检查用户是否具有指定角色或更高权限
   */
  const hasRole = (role: UserRole): boolean => {
    if (!user.value) return false
    return ROLE_HIERARCHY[user.value.role] >= ROLE_HIERARCHY[role]
  }

  /**
   * 检查用户是否具有指定的精确角色
   */
  const hasExactRole = (role: UserRole): boolean => {
    return user.value?.role === role
  }

  /**
   * 检查用户是否可以执行某个操作
   */
  const can = (action: 'view' | 'edit' | 'delete' | 'manage'): boolean => {
    if (!user.value) return false

    switch (action) {
      case 'view':
        return hasRole('viewer')
      case 'edit':
        return hasRole('editor')
      case 'delete':
        return hasRole('editor')
      case 'manage':
        return hasRole('admin')
      default:
        return false
    }
  }

  /**
   * 登出
   */
  const logout = async () => {
    isLoading.value = true
    error.value = null

    try {
      await $fetch('/api/auth/logout', { method: 'POST' })
      user.value = null
      // 重定向到登录页
      await navigateTo('/login')
    } catch (err: any) {
      console.error('Logout failed:', err)
      error.value = err.message || '登出失败'
      // 即使失败也清除本地状态并跳转
      user.value = null
      await navigateTo('/login')
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 刷新用户信息
   */
  const refresh = async () => {
    return fetchUser()
  }

  /**
   * 清除错误
   */
  const clearError = () => {
    error.value = null
  }

  return {
    // 状态
    user,
    isLoading,
    isInitialized,
    error,

    // 计算属性
    isLoggedIn,
    isAdmin,
    isEditor,
    canEdit,
    canManage,
    displayName,
    avatarUrl,

    // 方法
    fetchUser,
    initialize,
    hasRole,
    hasExactRole,
    can,
    logout,
    refresh,
    clearError,
  }
})
