<script setup lang="ts">
/**
 * Git 同步状态指示器
 * 显示在头部，展示当前 Git 同步状态
 * 
 * Requirements: 5.5
 */
import { getSyncStatusDisplay } from '~/composables/usePublish'

const { syncStatus, isLoading, fetchStatus, push } = useGitSyncStatus()

// 状态显示
const statusDisplay = computed(() => getSyncStatusDisplay(syncStatus.value.syncStatus))

// 是否显示推送按钮
const showPushButton = computed(() => {
  return syncStatus.value.syncStatus === 'ahead' && syncStatus.value.ahead > 0
})

// 推送中状态
const isPushing = ref(false)

// 执行推送
const handlePush = async () => {
  isPushing.value = true
  await push()
  isPushing.value = false
}
</script>

<template>
  <UPopover>
    <UButton
      variant="ghost"
      size="sm"
      :color="statusDisplay.color"
      :loading="isLoading"
    >
      <UIcon :name="statusDisplay.icon" class="w-4 h-4" />
      <span class="hidden sm:inline ml-1.5">{{ statusDisplay.label }}</span>
      <UBadge
        v-if="syncStatus.ahead > 0"
        :color="statusDisplay.color"
        variant="solid"
        size="xs"
        class="ml-1"
      >
        {{ syncStatus.ahead }}
      </UBadge>
    </UButton>

    <template #content>
      <div class="p-3 w-64">
        <div class="font-medium mb-2">Git 同步状态</div>
        
        <div class="space-y-2 text-sm">
          <div class="flex items-center justify-between">
            <span class="text-gray-500">状态</span>
            <UBadge :color="statusDisplay.color" variant="subtle" size="xs">
              {{ statusDisplay.label }}
            </UBadge>
          </div>
          
          <div v-if="syncStatus.ahead > 0" class="flex items-center justify-between">
            <span class="text-gray-500">待推送提交</span>
            <span class="font-medium">{{ syncStatus.ahead }}</span>
          </div>
          
          <div v-if="syncStatus.behind > 0" class="flex items-center justify-between">
            <span class="text-gray-500">待拉取提交</span>
            <span class="font-medium">{{ syncStatus.behind }}</span>
          </div>
          
          <div class="flex items-center justify-between">
            <span class="text-gray-500">本地更改</span>
            <span class="font-medium">{{ syncStatus.hasLocalChanges ? '有' : '无' }}</span>
          </div>
        </div>

        <div class="mt-3 pt-3 border-t dark:border-gray-700 flex gap-2">
          <UButton
            variant="ghost"
            size="xs"
            icon="i-lucide-refresh-cw"
            :loading="isLoading"
            @click="fetchStatus"
          >
            刷新
          </UButton>
          
          <UButton
            v-if="showPushButton"
            color="primary"
            size="xs"
            icon="i-lucide-upload"
            :loading="isPushing"
            @click="handlePush"
          >
            推送
          </UButton>
        </div>
      </div>
    </template>
  </UPopover>
</template>
