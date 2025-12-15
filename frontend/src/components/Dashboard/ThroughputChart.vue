<template>
  <a-card title="任务吞吐趋势" :bordered="false" class="throughput-chart-card">
    <template #extra>
      <a-space>
        <a-tooltip title="点击柱状图可跳转到对应状态的任务列表">
          <InfoCircleOutlined />
        </a-tooltip>
      </a-space>
    </template>
    
    <a-spin :spinning="loading">
      <div v-if="!loading && chartData.length === 0" class="empty-state">
        <a-empty description="暂无数据" />
      </div>
      
      <v-chart
        v-else
        ref="chartRef"
        :option="chartOption"
        :style="{ height: chartHeight }"
        autoresize
        @click="handleChartClick"
      />
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
import { BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

/**
 * 任务吞吐趋势图组件
 * 显示每日任务数量的堆叠柱状图
 */
const props = defineProps({
  // 图表数据
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
    default: '350px'
  }
})

const emit = defineEmits(['refresh'])

const router = useRouter()
const chartRef = ref(null)

// 处理后的图表数据
const chartData = computed(() => props.data || [])

// 提取日期列表
const dates = computed(() => {
  if (!Array.isArray(chartData.value)) return []
  return chartData.value.map(item => item.date)
})

// 提取各状态的数据
const successData = computed(() => {
  if (!Array.isArray(chartData.value)) return []
  return chartData.value.map(item => item.success || item.completed || 0)
})

const pendingAuditData = computed(() => {
  if (!Array.isArray(chartData.value)) return []
  return chartData.value.map(item => item.pending_audit || 0)
})

const failedData = computed(() => {
  if (!Array.isArray(chartData.value)) return []
  return chartData.value.map(item => item.failed || 0)
})

const rejectedData = computed(() => {
  if (!Array.isArray(chartData.value)) return []
  return chartData.value.map(item => item.rejected || 0)
})

// ECharts 配置
const chartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    },
    formatter: (params) => {
      let result = `<div style="font-weight: 600; margin-bottom: 8px;">${params[0].axisValue}</div>`
      let total = 0
      
      params.forEach(item => {
        total += item.value
        result += `
          <div style="display: flex; justify-content: space-between; align-items: center; margin: 4px 0;">
            <span>
              ${item.marker}
              <span style="margin-left: 4px;">${item.seriesName}</span>
            </span>
            <span style="margin-left: 20px; font-weight: 600;">${item.value}</span>
          </div>
        `
      })
      
      result += `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px; padding-top: 8px; border-top: 1px solid #f0f0f0;">
          <span style="font-weight: 600;">总计</span>
          <span style="font-weight: 600;">${total}</span>
        </div>
      `
      
      return result
    }
  },
  legend: {
    data: ['成功', '待审核', '失败', '驳回'],
    bottom: 0,
    icon: 'roundRect'
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '50px',
    top: '20px',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: dates.value,
    axisLabel: {
      rotate: dates.value.length > 10 ? 45 : 0,
      interval: 0
    }
  },
  yAxis: {
    type: 'value',
    name: '任务数量',
    minInterval: 1
  },
  series: [
    {
      name: '成功',
      type: 'bar',
      stack: 'total',
      data: successData.value,
      itemStyle: {
        color: '#52c41a'
      },
      emphasis: {
        focus: 'series'
      }
    },
    {
      name: '待审核',
      type: 'bar',
      stack: 'total',
      data: pendingAuditData.value,
      itemStyle: {
        color: '#faad14'
      },
      emphasis: {
        focus: 'series'
      }
    },
    {
      name: '失败',
      type: 'bar',
      stack: 'total',
      data: failedData.value,
      itemStyle: {
        color: '#ff4d4f'
      },
      emphasis: {
        focus: 'series'
      }
    },
    {
      name: '驳回',
      type: 'bar',
      stack: 'total',
      data: rejectedData.value,
      itemStyle: {
        color: '#d9d9d9'
      },
      emphasis: {
        focus: 'series'
      }
    }
  ]
}))

// 处理图表点击事件
const handleChartClick = (params) => {
  if (params.componentType === 'series') {
    const date = params.name
    const statusMap = {
      '成功': 'completed',
      '待审核': 'pending_audit',
      '失败': 'failed',
      '驳回': 'rejected'
    }
    
    const status = statusMap[params.seriesName]
    
    // 跳转到任务列表页面，带上筛选条件
    router.push({
      name: 'TaskList',
      query: {
        status,
        date
      }
    })
  }
}

// 监听数据变化，刷新图表
watch(() => props.data, () => {
  if (chartRef.value) {
    chartRef.value.resize()
  }
}, { deep: true })
</script>

<style scoped>
.throughput-chart-card {
  height: 100%;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 350px;
}
</style>
