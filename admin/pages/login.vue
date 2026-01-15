<script setup lang="ts">
/**
 * 登录页面
 * 支持钉钉 OAuth 登录
 * 
 * Requirements: 1.1, 12.1, 12.6
 */
definePageMeta({
  layout: 'blank',
})

const config = useRuntimeConfig()
const route = useRoute()

// 登录状态
const isLoading = ref(false)

// 获取 URL 中的错误信息
const errorMessage = computed(() => {
  const error = route.query.error
  return typeof error === 'string' ? decodeURIComponent(error) : null
})

// 钉钉登录 URL
const dingtalkLoginUrl = computed(() => {
  if (typeof window === 'undefined') return ''
  
  const redirectUri = `${window.location.origin}/api/auth/dingtalk`
  // 保存当前页面作为登录后的跳转目标
  const state = route.query.redirect || '/'
  
  const params = new URLSearchParams({
    client_id: config.public.dingtalkAppKey || '',
    redirect_uri: redirectUri,
    response_type: 'code',
    scope: 'openid corpid',
    prompt: 'consent',
    state: typeof state === 'string' ? state : '/',
  })
  return `https://login.dingtalk.com/oauth2/auth?${params}`
})

// 处理钉钉登录点击
const handleDingtalkLogin = () => {
  isLoading.value = true
  // 跳转到钉钉授权页面
  window.location.href = dingtalkLoginUrl.value
}

// 清除错误信息
const clearError = () => {
  const query = { ...route.query }
  delete query.error
  navigateTo({ path: '/login', query })
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900 px-4">
    <!-- 背景装饰 -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -right-40 w-80 h-80 bg-primary-500/10 rounded-full blur-3xl" />
      <div class="absolute -bottom-40 -left-40 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl" />
    </div>

    <div class="relative w-full max-w-md">
      <!-- 登录卡片 -->
      <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-xl shadow-gray-200/50 dark:shadow-none border border-gray-200/60 dark:border-gray-800 p-8">
        <!-- Logo 和标题 -->
        <div class="text-center mb-8">
          <div class="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-500 to-indigo-600 rounded-2xl shadow-lg shadow-primary-500/30 mb-6">
            <UIcon name="i-lucide-book-open" class="w-8 h-8 text-white" />
          </div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">FORCOME 知识库</h1>
          <p class="text-gray-500 dark:text-gray-400 mt-2">后台管理系统</p>
        </div>

        <div class="space-y-5">
          <!-- 错误提示 -->
          <div
            v-if="errorMessage"
            class="flex items-start gap-3 p-4 rounded-xl bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20"
          >
            <UIcon name="i-lucide-alert-circle" class="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
            <div class="flex-1">
              <p class="text-sm text-red-700 dark:text-red-400">{{ errorMessage }}</p>
            </div>
            <button @click="clearError" class="text-red-400 hover:text-red-500">
              <UIcon name="i-lucide-x" class="w-4 h-4" />
            </button>
          </div>

          <!-- 钉钉登录按钮 -->
          <UButton
            block
            size="xl"
            color="primary"
            :loading="isLoading"
            :disabled="isLoading"
            class="h-12 text-base font-medium shadow-lg shadow-primary-500/25 hover:shadow-xl hover:shadow-primary-500/30 transition-all duration-200"
            @click="handleDingtalkLogin"
          >
            <template #leading>
              <UIcon name="i-lucide-message-circle" class="w-5 h-5" />
            </template>
            {{ isLoading ? '正在跳转...' : '使用钉钉登录' }}
          </UButton>

          <!-- 分隔线 -->
          <div class="relative">
            <div class="absolute inset-0 flex items-center">
              <div class="w-full border-t border-gray-200 dark:border-gray-800" />
            </div>
            <div class="relative flex justify-center text-xs">
              <span class="px-3 bg-white dark:bg-gray-900 text-gray-400">企业账号登录</span>
            </div>
          </div>

          <!-- 提示信息 -->
          <p class="text-center text-sm text-gray-500 dark:text-gray-400">
            请使用企业钉钉账号登录
          </p>
        </div>
      </div>

      <!-- 底部信息 -->
      <p class="text-center text-xs text-gray-400 dark:text-gray-500 mt-6">
        登录即表示您同意我们的服务条款和隐私政策
      </p>
    </div>
  </div>
</template>
