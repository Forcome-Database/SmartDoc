<script setup lang="ts">
/**
 * 协作者显示组件
 * 显示当前文档的协作者头像和锁定状态
 * 
 * Requirements: 13.1, 13.3, 13.7
 */
import type { LockStatus, LockUser, EditLockInfo } from '~/composables/useEditLock'

const props = defineProps<{
  /** 锁状态 */
  lockStatus: LockStatus
  /** 锁信息 */
  lock: EditLockInfo | null
  /** 锁持有者（如果被其他用户锁定） */
  lockedBy: LockUser | null
  /** 当前查看者列表 */
  watchers?: LockUser[]
  /** 当前用户 ID */
  currentUserId?: string
}>()

const emit = defineEmits<{
  /** 请求获取锁 */
  'acquire-lock': []
  /** 请求释放锁 */
  'release-lock': []
}>()

// 状态文本
const statusText = computed(() => {
  switch (props.lockStatus) {
    case 'acquiring':
      return '正在获取编辑权限...'
    case 'locked':
      return '正在编辑'
    case 'locked_by_other':
      return `${props.lockedBy?.name || '其他用户'} 正在编辑`
    case 'expired':
      return '编辑权限已过期'
    case 'error':
      return '获取编辑权限失败'
    default:
      return '只读模式'
  }
})

// 状态颜色
const statusColor = computed(() => {
  switch (props.lockStatus) {
    case 'locked':
      return 'success'
    case 'locked_by_other':
      return 'warning'
    case 'expired':
    case 'error':
      return 'error'
    default:
      return 'neutral'
  }
})

// 状态图标
const statusIcon = computed(() => {
  switch (props.lockStatus) {
    case 'acquiring':
      return 'i-lucide-loader-2'
    case 'locked':
      return 'i-lucide-pencil'
    case 'locked_by_other':
      return 'i-lucide-lock'
    case 'expired':
      return 'i-lucide-clock'
    case 'error':
      return 'i-lucide-alert-circle'
    default:
      return 'i-lucide-eye'
  }
})

// 是否显示获取锁按钮
const showAcquireButton = computed(() => {
  return props.lockStatus === 'idle' || 
         props.lockStatus === 'expired' || 
         props.lockStatus === 'error'
})

// 是否显示释放锁按钮
const showReleaseButton = computed(() => {
  return props.lockStatus === 'locked'
})

// 过滤掉当前用户的查看者列表
const otherWatchers = computed(() => {
  if (!props.watchers) return []
  return props.watchers.filter(w => w.id !== props.currentUserId)
})

// 锁持有者（排除当前用户）
const lockHolder = computed(() => {
  if (props.lockStatus === 'locked_by_other' && props.lockedBy) {
    return props.lockedBy
  }
  return null
})
</script>

<template>
  <div class="flex items-center gap-3">
    <!-- 查看者头像列表 -->
    <div v-if="otherWatchers.length > 0" class="flex items-center">
      <UAvatarGroup :max="3" size="xs">
        <UAvatar
          v-for="watcher in otherWatchers"
          :key="watcher.id"
          :src="watcher.avatar || undefined"
          :alt="watcher.name"
        />
      </UAvatarGroup>
      <span class="ml-2 text-xs text-gray-500">
        {{ otherWatchers.length }} 人正在查看
      </span>
    </div>

    <!-- 锁定状态指示器 -->
    <div class="flex items-center gap-2">
      <!-- 锁持有者头像（如果被其他用户锁定） -->
      <UTooltip v-if="lockHolder" :text="`${lockHolder.name} 正在编辑`">
        <UAvatar
          :src="lockHolder.avatar || undefined"
          :alt="lockHolder.name"
          size="xs"
          class="ring-2 ring-amber-400"
        />
      </UTooltip>

      <!-- 状态徽章 -->
      <UBadge
        :color="statusColor"
        variant="subtle"
        size="xs"
        class="flex items-center gap-1"
      >
        <UIcon
          :name="statusIcon"
          :class="['w-3 h-3', lockStatus === 'acquiring' ? 'animate-spin' : '']"
        />
        <span>{{ statusText }}</span>
      </UBadge>

      <!-- 获取锁按钮 -->
      <UButton
        v-if="showAcquireButton"
        size="xs"
        variant="soft"
        color="primary"
        icon="i-lucide-pencil"
        @click="emit('acquire-lock')"
      >
        开始编辑
      </UButton>

      <!-- 释放锁按钮 -->
      <UButton
        v-if="showReleaseButton"
        size="xs"
        variant="ghost"
        color="neutral"
        icon="i-lucide-unlock"
        @click="emit('release-lock')"
      >
        结束编辑
      </UButton>
    </div>
  </div>
</template>
