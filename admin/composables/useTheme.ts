/**
 * 主题管理 Composable
 * 提供主题切换、系统偏好检测、持久化功能
 * 
 * Requirements: 8.2
 */
import { ref, computed, readonly } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'system'
export type ResolvedTheme = 'light' | 'dark'

// 全局状态（在多个组件间共享）
const themeMode = ref<ThemeMode>('system')
const resolvedTheme = ref<ResolvedTheme>('light')
const isInitialized = ref(false)

export function useTheme() {
  /**
   * 检测系统主题偏好
   */
  const getSystemTheme = (): ResolvedTheme => {
    if (typeof window === 'undefined') return 'light'
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }

  /**
   * 应用主题到 DOM
   */
  const applyTheme = (theme: ResolvedTheme) => {
    if (typeof document === 'undefined') return
    
    const root = document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    resolvedTheme.value = theme
  }

  /**
   * 更新主题（根据当前模式）
   */
  const updateTheme = () => {
    if (themeMode.value === 'system') {
      applyTheme(getSystemTheme())
    } else {
      applyTheme(themeMode.value)
    }
  }

  /**
   * 设置主题模式
   */
  const setThemeMode = (mode: ThemeMode) => {
    themeMode.value = mode
    
    // 持久化到 localStorage
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('theme-mode', mode)
    }
    
    updateTheme()
  }

  /**
   * 快速切换主题（在 light 和 dark 之间）
   */
  const toggleTheme = () => {
    if (themeMode.value === 'system') {
      // 如果是系统模式，切换到与当前相反的固定模式
      setThemeMode(resolvedTheme.value === 'dark' ? 'light' : 'dark')
    } else {
      setThemeMode(themeMode.value === 'dark' ? 'light' : 'dark')
    }
  }

  /**
   * 初始化主题
   */
  const initTheme = () => {
    if (isInitialized.value) return
    if (typeof window === 'undefined') return
    
    // 从 localStorage 恢复主题设置
    const savedMode = localStorage.getItem('theme-mode') as ThemeMode | null
    if (savedMode && (savedMode === 'light' || savedMode === 'dark' || savedMode === 'system')) {
      themeMode.value = savedMode
    }
    
    updateTheme()
    
    // 监听系统主题变化
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = () => {
      if (themeMode.value === 'system') {
        updateTheme()
      }
    }
    
    mediaQuery.addEventListener('change', handleChange)
    
    isInitialized.value = true
    
    // 返回清理函数
    return () => {
      mediaQuery.removeEventListener('change', handleChange)
    }
  }

  // 计算属性
  const isDark = computed(() => resolvedTheme.value === 'dark')
  const isLight = computed(() => resolvedTheme.value === 'light')
  const isSystemMode = computed(() => themeMode.value === 'system')

  return {
    // 状态
    themeMode: readonly(themeMode),
    resolvedTheme: readonly(resolvedTheme),
    
    // 计算属性
    isDark,
    isLight,
    isSystemMode,
    
    // 方法
    setThemeMode,
    toggleTheme,
    initTheme,
    getSystemTheme,
  }
}
