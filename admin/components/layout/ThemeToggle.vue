<script setup lang="ts">
/**
 * 主题切换组件
 * 支持 light/dark/system 三种模式
 * 
 * Requirements: 8.2
 */
import { useTheme, type ThemeMode } from '~/composables/useTheme'

const { themeMode, resolvedTheme, setThemeMode, toggleTheme, initTheme } = useTheme()

// 主题配置
const themeOptions: { value: ThemeMode; icon: string; label: string }[] = [
  { value: 'light', icon: 'i-lucide-sun', label: '浅色' },
  { value: 'dark', icon: 'i-lucide-moon', label: '深色' },
  { value: 'system', icon: 'i-lucide-monitor', label: '跟随系统' },
]

// 当前显示的图标
const currentIcon = computed(() => {
  if (themeMode.value === 'system') {
    return 'i-lucide-monitor'
  }
  return themeMode.value === 'dark' ? 'i-lucide-moon' : 'i-lucide-sun'
})

// 当前显示的标签
const currentLabel = computed(() => {
  const option = themeOptions.find(o => o.value === themeMode.value)
  return option?.label || '主题'
})

// 初始化主题
onMounted(() => {
  initTheme()
})

// 下拉菜单项
const menuItems = computed(() => [
  themeOptions.map(option => ({
    label: option.label,
    icon: option.icon,
    click: () => setThemeMode(option.value),
  }))
])
</script>

<template>
  <UDropdownMenu :items="menuItems">
    <UTooltip :text="currentLabel">
      <UButton
        variant="ghost"
        color="neutral"
        size="sm"
        :icon="currentIcon"
        @click.stop="toggleTheme"
      />
    </UTooltip>
  </UDropdownMenu>
</template>
