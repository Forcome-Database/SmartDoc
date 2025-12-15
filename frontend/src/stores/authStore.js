/**
 * 认证Store
 * 管理用户登录状态、Token和用户信息
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  // ==================== State ====================
  
  /**
   * 当前登录用户信息
   */
  const user = ref(null)
  
  /**
   * 访问令牌
   */
  const token = ref(localStorage.getItem('access_token') || null)
  
  /**
   * 是否已认证
   */
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  
  /**
   * 用户角色
   */
  const userRole = computed(() => user.value?.role || null)
  
  /**
   * 是否为管理员
   */
  const isAdmin = computed(() => userRole.value === 'admin')
  
  /**
   * 是否为规则架构师
   */
  const isArchitect = computed(() => userRole.value === 'architect')
  
  /**
   * 是否为审核员
   */
  const isAuditor = computed(() => userRole.value === 'auditor')
  
  /**
   * 是否为访客
   */
  const isVisitor = computed(() => userRole.value === 'visitor')

  // ==================== Actions ====================
  
  /**
   * 设置访问令牌
   * @param {string} newToken - 新的访问令牌
   */
  function setToken(newToken) {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('access_token', newToken)
    } else {
      localStorage.removeItem('access_token')
    }
  }

  /**
   * 设置用户信息
   * @param {object} userData - 用户数据
   */
  function setUser(userData) {
    user.value = userData
    // 同时保存到localStorage，用于页面刷新时恢复
    if (userData) {
      localStorage.setItem('user_info', JSON.stringify(userData))
    } else {
      localStorage.removeItem('user_info')
    }
  }

  /**
   * 登出
   * 清除所有认证信息
   */
  async function logout() {
    try {
      // 调用后端登出API（可选）
      await authAPI.logout()
    } catch (error) {
      console.error('登出API调用失败:', error)
      // 即使API调用失败，也继续清除本地数据
    } finally {
      // 清除本地状态
      user.value = null
      token.value = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_info')
    }
  }
  
  /**
   * 初始化认证状态
   * 从localStorage恢复用户信息
   */
  function initAuth() {
    const savedToken = localStorage.getItem('access_token')
    const savedUser = localStorage.getItem('user_info')
    
    if (savedToken) {
      token.value = savedToken
    }
    
    if (savedUser) {
      try {
        user.value = JSON.parse(savedUser)
      } catch (error) {
        console.error('解析用户信息失败:', error)
        localStorage.removeItem('user_info')
      }
    }
  }
  
  /**
   * 检查用户是否有指定角色
   * @param {string|string[]} roles - 角色或角色数组
   * @returns {boolean} 是否有权限
   */
  function hasRole(roles) {
    if (!userRole.value) return false
    
    if (Array.isArray(roles)) {
      return roles.includes(userRole.value)
    }
    
    return userRole.value === roles
  }
  
  /**
   * 检查用户是否有访问指定路由的权限
   * @param {object} route - 路由对象
   * @returns {boolean} 是否有权限
   */
  function canAccessRoute(route) {
    // 如果路由没有角色限制，则允许访问
    if (!route.meta?.roles) return true
    
    // 检查用户角色是否在允许的角色列表中
    return hasRole(route.meta.roles)
  }

  // ==================== Return ====================
  
  return {
    // State
    user,
    token,
    isAuthenticated,
    userRole,
    isAdmin,
    isArchitect,
    isAuditor,
    isVisitor,
    
    // Actions
    setToken,
    setUser,
    logout,
    initAuth,
    hasRole,
    canAccessRoute
  }
})
