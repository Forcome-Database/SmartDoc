<script setup lang="ts">
/**
 * 全局加载指示器组件
 * 显示页面级别的加载状态
 * 
 * @requirements 11.3
 */
import { useGlobalLoading } from '~/composables/useLoading'

const { isLoading, loadingText } = useGlobalLoading()
</script>

<template>
  <Transition
    enter-active-class="transition-opacity duration-200"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition-opacity duration-150"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="isLoading"
      class="fixed inset-0 z-50 flex items-center justify-center bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm"
    >
      <div class="flex flex-col items-center gap-4 animate-fade-in">
        <!-- 加载动画 -->
        <div class="relative">
          <div class="w-12 h-12 rounded-full border-4 border-gray-200 dark:border-gray-700" />
          <div class="absolute inset-0 w-12 h-12 rounded-full border-4 border-primary-500 border-t-transparent animate-spin" />
        </div>
        
        <!-- 加载文本 -->
        <p v-if="loadingText" class="text-sm text-gray-600 dark:text-gray-400">
          {{ loadingText }}
        </p>
      </div>
    </div>
  </Transition>
</template>
