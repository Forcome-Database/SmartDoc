/**
 * Nuxt UI 主题配置
 * 定义颜色、组件默认样式等
 * Mintlify 风格：简约大气，平滑过渡
 * 
 * Requirements: 8.2, 8.3, 8.7
 */
export default defineAppConfig({
  // Icon 配置 - TailwindCSS v4 需要配置 cssLayer
  icon: {
    mode: 'css',
    cssLayer: 'base',
  },
  ui: {
    // 颜色配置
    colors: {
      primary: 'indigo',
      secondary: 'sky',
      success: 'emerald',
      info: 'blue',
      warning: 'amber',
      error: 'rose',
      neutral: 'slate',
    },
    // Toast 通知配置
    toast: {
      defaultVariants: {
        color: 'neutral',
      },
    },
    // Toaster 容器配置
    toaster: {
      position: 'top-right' as const,
    },
  },
})
