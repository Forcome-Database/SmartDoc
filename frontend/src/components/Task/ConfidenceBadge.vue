<template>
  <a-tooltip :title="`置信度: ${displayScore}`">
    <a-badge
      :color="badgeColor"
      :text="badgeText"
      class="confidence-badge"
    />
  </a-tooltip>
</template>

<script setup>
import { computed } from 'vue'
import { CONFIDENCE_LEVELS } from '@/utils/constants'

const props = defineProps({
  score: {
    type: Number,
    default: null
  }
})

/**
 * 显示的分数（格式化）
 */
const displayScore = computed(() => {
  if (props.score === null || props.score === undefined) return '-'
  return `${props.score.toFixed(1)}%`
})

/**
 * 获取置信度等级
 */
const confidenceLevel = computed(() => {
  if (props.score === null || props.score === undefined) {
    return { label: '-', color: 'default' }
  }

  if (props.score >= CONFIDENCE_LEVELS.HIGH.min) {
    return CONFIDENCE_LEVELS.HIGH
  } else if (props.score >= CONFIDENCE_LEVELS.MEDIUM.min) {
    return CONFIDENCE_LEVELS.MEDIUM
  } else {
    return CONFIDENCE_LEVELS.LOW
  }
})

/**
 * 徽章颜色
 */
const badgeColor = computed(() => {
  const colorMap = {
    success: '#52c41a',
    warning: '#faad14',
    error: '#ff4d4f',
    default: '#d9d9d9'
  }
  return colorMap[confidenceLevel.value.color] || colorMap.default
})

/**
 * 徽章文本
 */
const badgeText = computed(() => {
  if (props.score === null || props.score === undefined) {
    return '未知'
  }
  return `${confidenceLevel.value.label} (${displayScore.value})`
})
</script>

<style scoped>
.confidence-badge {
  cursor: help;
}

:deep(.ant-badge-status-text) {
  font-size: 12px;
  font-weight: 500;
}
</style>
