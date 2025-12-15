<template>
  <a-card title="异常分布" :bordered="false" class="exception-chart-card">
    <template #extra>
      <a-space>
        <a-tooltip title="点击扇区可查看该类异常的详细任务列表">
          <InfoCircleOutlined />
        </a-tooltip>
      </a-space>
    </template>
    
    <a-spin :spinning="loading">
      <div v-if="!loading && chartData.length === 0" class="empty-state">
        <a-empty description="暂无异常数据" />
      </div>
      
      <div v-else class="chart-container">
        <v-chart
          ref="chartRef"
          :option="chartOption"
          :style="{ height: chartHeight }"
          autoresize
          @click="handleChartClick"
        />
        
        <!-- 异常统计列表 -->
        <div class="exception-list">
          <div
            v-for="item in sortedExceptions"
            :key="item.type"
            class="exception-item"
            @click="handleExceptionClick(item)"
          >
            <div class="exception-info">
              <span
                class="exception-color"
                :style="{ backgroundColor: item.color }"
              />
              <span class="exception-name">{{ item.name }}</span>
            </div>
            <div class="exception-stats">
              <span class="exception-count">{{ item.count }}</span>
              <span class="exception-percent">{{ item.percent }}%</span>
            </div>
          </div>
        </div>
      </div>
    </a-spin>
  </a-card>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { InfoCircleOutlined } from '@ant-design/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent
} from 'echarts/components'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent
])

/**
 * 异常分布饼图组件
 * 显示各类异常的占比
 */
const props = defineProps({
  // 异常数据
  data: {
    type: Array,
    default: () => []
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false
  },
  // 图表高度
  chartHeight: {
    type: String,
    default: '300px'
  }
})

const emit = defineEmits(['exception-click'])

const router = useRouter()
const chartRef = ref(null)

// 异常类型颜色映射
const exceptionColors = {
  'ocr_empty': '#ff4d4f',                    // OCR识别空 - 红色
  'required_field_missing': '#ff7a45',       // 必填校验失败 - 橙红色
  'format_validation_failed': '#ffa940',     // 格式校验失败 - 橙色
  'llm_inconsistent': '#faad14',             // LLM不一致 - 黄色
  'downstream_error': '#a0d911',             // 下游接口错误 - 黄绿色
  'processing_timeout': '#13c2c2',           // 处理超时 - 青色
  'other': '#d9d9d9'                         // 其他 - 灰色
}

// 异常类型名称映射（后端已返回label，这里作为备用）
const exceptionNames = {
  'ocr_empty': 'OCR识别空',
  'required_field_missing': '必填校验失败',
  'format_validation_failed': '格式校验失败',
  'llm_inconsistent': 'LLM不一致',
  'downstream_error': '下游接口错误',
  'processing_timeout': '处理超时',
  'other': '其他异常'
}

// 处理后的图表数据
const chartData = computed(() => {
  const data = Array.isArray(props.data) ? props.data : []
  const total = data.reduce((sum, item) => sum + (item.count || 0), 0)
  
  return data.map(item => ({
    ...item,
    // 优先使用后端返回的label，否则使用映射表
    name: item.label || exceptionNames[item.type] || item.type,
    value: item.count || 0,
    // 优先使用后端返回的percentage，否则计算
    percent: item.percentage !== undefined ? item.percentage : (total > 0 ? ((item.count / total) * 100).toFixed(1) : 0),
    color: exceptionColors[item.type] || exceptionColors.other
  }))
})

// 排序后的异常列表（按数量降序）
const sortedExceptions = computed(() => {
  return [...chartData.value].sort((a, b) => b.value - a.value)
})

// ECharts 配置
const chartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: (params) => {
      return `
        <div style="font-weight: 600; margin-bottom: 4px;">${params.name}</div>
        <div style="display: flex; justify-content: space-between; gap: 20px;">
          <span>数量：</span>
          <span style="font-weight: 600;">${params.value}</span>
        </div>
        <div style="display: flex; justify-content: space-between; gap: 20px;">
          <span>占比：</span>
          <span style="font-weight: 600;">${params.percent}%</span>
        </div>
      `
    }
  },
  legend: {
    show: false
  },
  series: [
    {
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 8,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: true,
        formatter: '{b}\n{d}%',
        fontSize: 12
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold'
        },
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      data: chartData.value.map(item => ({
        name: item.name,
        value: item.value,
        itemStyle: {
          color: item.color
        },
        type: item.type
      }))
    }
  ]
}))

// 处理图表点击事件
const handleChartClick = (params) => {
  if (params.componentType === 'series') {
    const exceptionType = params.data.type
    handleExceptionClick({ type: exceptionType })
  }
}

// 处理异常项点击事件
const handleExceptionClick = (item) => {
  // 触发事件，让父组件处理
  emit('exception-click', item)
  
  // 或者直接跳转到任务列表
  router.push({
    name: 'TaskList',
    query: {
      exception_type: item.type
    }
  })
}

// 监听数据变化，刷新图表
watch(() => props.data, () => {
  if (chartRef.value) {
    chartRef.value.resize()
  }
}, { deep: true })
</script>

<style scoped>
.exception-chart-card {
  height: 100%;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.chart-container {
  display: flex;
  gap: 24px;
  align-items: center;
}

.exception-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 200px;
}

.exception-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.exception-item:hover {
  background-color: #f5f5f5;
}

.exception-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.exception-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.exception-name {
  font-size: 13px;
  color: rgba(0, 0, 0, 0.85);
}

.exception-stats {
  display: flex;
  align-items: center;
  gap: 12px;
}

.exception-count {
  font-size: 16px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.85);
}

.exception-percent {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

/* 响应式布局 */
@media (max-width: 768px) {
  .chart-container {
    flex-direction: column;
  }
  
  .exception-list {
    width: 100%;
  }
}
</style>
