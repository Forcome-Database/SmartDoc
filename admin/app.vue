<script setup lang="ts">
/**
 * 应用根组件
 * 提供全局布局和状态管理
 */
import { useTheme } from '~/composables/useTheme'

const { initTheme } = useTheme()

// 初始化主题
onMounted(() => {
  initTheme()
})
</script>

<template>
  <UApp>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
    
    <!-- 全局加载指示器 -->
    <GlobalLoading />
  </UApp>
</template>
