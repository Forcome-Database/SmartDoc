<script setup lang="ts">
/**
 * 文档锁定遮罩组件
 * 当文档被其他用户锁定时显示
 * 
 * Requirements: 13.3, 13.7
 */
import type { LockUser } from '~/composables/useEditLock'

const props = defineProps<{
  /** 锁持有者信息 */
  lockedBy: LockUser
  /** 锁过期时间 */
  expiresAt?: Date
}>()

const emit = defineEmits<{
  /** 刷新页面 */
  'refresh': []
}>()

// 计算剩余时间
const remainingTime = ref('')

// 更新剩余时间
const updateRemainingTime = () => {
  if (!props.expiresAt) {
    remainingTime.value = ''
    return
  }

  const now = new Date()
  const expires = new Date(props.expiresAt)
  const diff = expires.getTime() - now.getTime()

  if (diff <= 0) {
    remainingTime.value = '锁即将释放'
    return
  }

  const minutes = Math.floor(diff / 60000)
  const seconds = Math.floor((diff % 60000) / 1000)

  if (minutes > 0) {
    remainingTime.value = `约 ${minutes} 分钟后可编辑`
  } else {
    remainingTime.value = `约 ${seconds} 秒后可编辑`
  }
}

// 定时更新剩余时间
let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  updateRemainingTime()
  timer = setInterval(updateRemainingTime, 1000)
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<template>
  <div class="absolute inset-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm z-10 flex items-center justify-center">
    <div class="text-center p-6 max-w-md">
      <!-- 锁定图标 -->
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
        <UIcon name="i-lucide-lock" class="w-8 h-8 text-amber-600 dark:text-amber-400" />
      </div>

      <!-- 锁持有者信息 -->
      <div class="flex items-center justify-center gap-2 mb-3">
        <UAvatar
          :src="lockedBy.avatar || undefined"
          :alt="lockedBy.name"
          size="sm"
        />
        <span class="font-medium text-gray-900 dark:text-white">
          {{ lockedBy.name }}
        </span>
      </div>

      <!-- 提示文本 -->
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
        文档正在被编辑
      </h3>
      <p class="text-gray-500 dark:text-gray-400 mb-4">
        {{ lockedBy.name }} 正在编辑此文档，请等待编辑完成后再进行修改。
      </p>

      <!-- 剩余时间 -->
      <p v-if="remainingTime" class="text-sm text-gray-400 mb-4">
        {{ remainingTime }}
      </p>

      <!-- 操作按钮 -->
      <div class="flex items-center justify-center gap-3">
        <UButton
          variant="soft"
          color="neutral"
          icon="i-lucide-refresh-cw"
          @click="emit('refresh')"
        >
          刷新状态
        </UButton>
      </div>
    </div>
  </div>
</template>
