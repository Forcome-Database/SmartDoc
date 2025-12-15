<template>
  <div class="flow-status-indicator">
    <a-tooltip :title="getOcrTooltip">
      <div class="flow-step" :class="getOcrClass">
        <span class="step-icon">OCR</span>
      </div>
    </a-tooltip>
    <div class="flow-arrow">→</div>
    <a-tooltip :title="getPipelineTooltip">
      <div class="flow-step" :class="getPipelineClass">
        <span class="step-icon">管道</span>
      </div>
    </a-tooltip>
    <div class="flow-arrow">→</div>
    <a-tooltip :title="getPushTooltip">
      <div class="flow-step" :class="getPushClass">
        <span class="step-icon">推送</span>
      </div>
    </a-tooltip>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  flowStatus: {
    type: Object,
    default: null
  }
})

// 状态映射
const STATUS_MAP = {
  pending: { class: 'pending', label: '等待中' },
  processing: { class: 'processing', label: '处理中' },
  running: { class: 'processing', label: '执行中' },
  completed: { class: 'success', label: '已完成' },
  success: { class: 'success', label: '成功' },
  failed: { class: 'failed', label: '失败' },
  skipped: { class: 'skipped', label: '跳过' },
  pushing: { class: 'processing', label: '推送中' }
}

/**
 * 获取OCR步骤样式类
 */
const getOcrClass = computed(() => {
  if (!props.flowStatus) return 'pending'
  const status = props.flowStatus.ocr_status || 'pending'
  return STATUS_MAP[status]?.class || 'pending'
})

/**
 * 获取管道步骤样式类
 */
const getPipelineClass = computed(() => {
  if (!props.flowStatus) return 'pending'
  const status = props.flowStatus.pipeline_status
  if (!status) return 'pending'
  return STATUS_MAP[status]?.class || 'pending'
})

/**
 * 获取推送步骤样式类
 */
const getPushClass = computed(() => {
  if (!props.flowStatus) return 'pending'
  const status = props.flowStatus.push_status
  if (!status) return 'pending'
  return STATUS_MAP[status]?.class || 'pending'
})

/**
 * 获取OCR提示文本
 */
const getOcrTooltip = computed(() => {
  if (!props.flowStatus) return 'OCR: 等待中'
  const status = props.flowStatus.ocr_status || 'pending'
  return `OCR: ${STATUS_MAP[status]?.label || status}`
})

/**
 * 获取管道提示文本
 */
const getPipelineTooltip = computed(() => {
  if (!props.flowStatus) return '管道: 等待中'
  const status = props.flowStatus.pipeline_status
  if (!status) return '管道: 等待中'
  return `管道: ${STATUS_MAP[status]?.label || status}`
})

/**
 * 获取推送提示文本
 */
const getPushTooltip = computed(() => {
  if (!props.flowStatus) return '推送: 等待中'
  const status = props.flowStatus.push_status
  if (!status) return '推送: 等待中'
  return `推送: ${STATUS_MAP[status]?.label || status}`
})
</script>

<style scoped>
.flow-status-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.flow-step {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  cursor: default;
  transition: all 0.2s;
}

.flow-arrow {
  color: #d9d9d9;
  font-size: 10px;
}

/* 状态样式 */
.flow-step.pending {
  background-color: #f5f5f5;
  color: #999;
  border: 1px solid #d9d9d9;
}

.flow-step.processing {
  background-color: #e6f7ff;
  color: #1890ff;
  border: 1px solid #91d5ff;
  animation: pulse 1.5s infinite;
}

.flow-step.success {
  background-color: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.flow-step.failed {
  background-color: #fff2f0;
  color: #ff4d4f;
  border: 1px solid #ffccc7;
}

.flow-step.skipped {
  background-color: #fafafa;
  color: #bfbfbf;
  border: 1px dashed #d9d9d9;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
</style>
