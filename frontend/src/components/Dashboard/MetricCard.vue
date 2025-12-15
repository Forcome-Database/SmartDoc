<template>
  <a-card 
    :class="['metric-card', { 'metric-card-warning': isWarning }]"
    :bordered="false"
  >
    <div class="metric-content">
      <div class="metric-header">
        <span class="metric-title">{{ title }}</span>
        <a-tooltip v-if="tooltip" :title="tooltip">
          <InfoCircleOutlined class="metric-info-icon" />
        </a-tooltip>
      </div>
      
      <div class="metric-value-container">
        <span class="metric-value">{{ formattedValue }}</span>
        <span v-if="unit" class="metric-unit">{{ unit }}</span>
      </div>
      
      <div v-if="trend !== undefined" class="metric-trend">
        <span :class="['trend-text', trendClass]">
          <component :is="trendIcon" class="trend-icon" />
          {{ trendText }}
        </span>
        <span class="trend-label">{{ trendLabel }}</span>
      </div>
      
      <div v-if="description" class="metric-description">
        {{ description }}
      </div>
    </div>
  </a-card>
</template>

<script setup>
import { computed } from 'vue'
import { 
  InfoCircleOutlined, 
  ArrowUpOutlined, 
  ArrowDownOutlined,
  MinusOutlined 
} from '@ant-design/icons-vue'

/**
 * 指标卡片组件
 * 显示单个指标的名称、数值、趋势和描述
 */
const props = defineProps({
  // 指标标题
  title: {
    type: String,
    required: true
  },
  // 指标数值
  value: {
    type: [Number, String],
    required: true
  },
  // 单位
  unit: {
    type: String,
    default: ''
  },
  // 趋势值（百分比，正数表示上升，负数表示下降）
  trend: {
    type: Number,
    default: undefined
  },
  // 趋势标签（如"较昨日"）
  trendLabel: {
    type: String,
    default: '较昨日'
  },
  // 描述文本
  description: {
    type: String,
    default: ''
  },
  // 提示信息
  tooltip: {
    type: String,
    default: ''
  },
  // 是否显示为警告样式（红色）
  isWarning: {
    type: Boolean,
    default: false
  },
  // 数值格式化函数
  formatter: {
    type: Function,
    default: null
  }
})

// 格式化数值
const formattedValue = computed(() => {
  if (props.formatter) {
    return props.formatter(props.value)
  }
  
  // 默认格式化：添加千分位分隔符
  if (typeof props.value === 'number') {
    return props.value.toLocaleString('zh-CN')
  }
  
  return props.value
})

// 趋势文本
const trendText = computed(() => {
  if (props.trend === undefined) return ''
  
  const absValue = Math.abs(props.trend)
  return `${absValue.toFixed(1)}%`
})

// 趋势样式类
const trendClass = computed(() => {
  if (props.trend === undefined) return ''
  
  if (props.trend > 0) return 'trend-up'
  if (props.trend < 0) return 'trend-down'
  return 'trend-neutral'
})

// 趋势图标
const trendIcon = computed(() => {
  if (props.trend === undefined) return null
  
  if (props.trend > 0) return ArrowUpOutlined
  if (props.trend < 0) return ArrowDownOutlined
  return MinusOutlined
})
</script>

<style scoped>
.metric-card {
  height: 100%;
  transition: all 0.3s ease;
}

.metric-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.metric-card-warning {
  border-left: 4px solid #ff4d4f;
}

.metric-card-warning .metric-value {
  color: #ff4d4f;
}

.metric-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.metric-title {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.65);
  font-weight: 500;
}

.metric-info-icon {
  color: rgba(0, 0, 0, 0.45);
  cursor: help;
}

.metric-value-container {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.metric-value {
  font-size: 30px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.85);
  line-height: 1.2;
}

.metric-unit {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
  margin-left: 4px;
}

.metric-trend {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.trend-text {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
}

.trend-icon {
  font-size: 12px;
}

.trend-up {
  color: #52c41a;
}

.trend-down {
  color: #ff4d4f;
}

.trend-neutral {
  color: rgba(0, 0, 0, 0.45);
}

.trend-label {
  color: rgba(0, 0, 0, 0.45);
}

.metric-description {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin-top: 4px;
}
</style>
