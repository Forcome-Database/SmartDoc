<template>
  <a-tag :color="statusColor">
    <template #icon>
      <component :is="statusIcon" v-if="statusIcon" />
    </template>
    {{ statusLabel }}
  </a-tag>
</template>

<script setup>
import { computed } from 'vue'
import {
  ClockCircleOutlined,
  SyncOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  CloudUploadOutlined,
  CloudOutlined
} from '@ant-design/icons-vue'
import { TASK_STATUS, TASK_STATUS_LABELS, TASK_STATUS_COLORS } from '@/utils/constants'

const props = defineProps({
  status: {
    type: String,
    required: true
  }
})

/**
 * 状态标签文本
 */
const statusLabel = computed(() => {
  return TASK_STATUS_LABELS[props.status] || props.status
})

/**
 * 状态标签颜色
 */
const statusColor = computed(() => {
  return TASK_STATUS_COLORS[props.status] || 'default'
})

/**
 * 状态图标
 */
const statusIcon = computed(() => {
  const iconMap = {
    [TASK_STATUS.QUEUED]: ClockCircleOutlined,
    [TASK_STATUS.PROCESSING]: SyncOutlined,
    [TASK_STATUS.PENDING_AUDIT]: ExclamationCircleOutlined,
    [TASK_STATUS.COMPLETED]: CheckCircleOutlined,
    [TASK_STATUS.REJECTED]: CloseCircleOutlined,
    [TASK_STATUS.PUSHING]: CloudUploadOutlined,
    [TASK_STATUS.PUSH_SUCCESS]: CloudOutlined,
    [TASK_STATUS.PUSH_FAILED]: CloseCircleOutlined
  }
  return iconMap[props.status]
})
</script>

<style scoped>
/* 自定义样式（如需要） */
</style>
