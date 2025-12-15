<template>
  <div class="dashboard-container">
    <!-- 时间范围筛选器 -->
    <div class="dashboard-header">
      <h2 class="dashboard-title">数据概览</h2>
      <a-radio-group
        v-model:value="timeRange"
        button-style="solid"
        @change="handleTimeRangeChange"
      >
        <a-radio-button value="today">今日</a-radio-button>
        <a-radio-button value="7days">近7天</a-radio-button>
        <a-radio-button value="30days">近30天</a-radio-button>
      </a-radio-group>
    </div>

    <!-- 核心指标卡片 -->
    <div class="metrics-grid">
      <MetricCard
        title="总接单量"
        :value="metrics.total_tasks"
        unit="个"
        :trend="metrics.total_tasks_trend"
        tooltip="统计时间范围内的任务总数"
      />
      
      <MetricCard
        title="累计页数"
        :value="metrics.total_pages"
        unit="页"
        :trend="metrics.total_pages_trend"
        tooltip="所有任务实际消耗的OCR页数总和"
      />
      
      <MetricCard
        title="处理中"
        :value="metrics.processing_tasks"
        :trend="metrics.processing_tasks_trend"
        tooltip="当前正在处理的任务数量"
      />
      
      <MetricCard
        title="待审核"
        :value="metrics.pending_audit_tasks"
        :trend="metrics.pending_audit_tasks_trend"
        tooltip="等待人工审核的任务数量"
      />
      
      <MetricCard
        title="推送异常"
        :value="metrics.push_failed_tasks"
        :is-warning="metrics.push_failed_tasks > 0"
        tooltip="推送失败的任务数量"
      />
      
      <MetricCard
        title="平均直通率"
        :value="metrics.stp_rate || 0"
        unit="%"
        :formatter="(val) => (val || 0).toFixed(1)"
        :trend="metrics.stp_rate_trend"
        tooltip="无需人工干预且成功推送的任务占比"
      />
      
      <MetricCard
        title="算力节省"
        :value="formatCostSaving(metrics.cost_saving)"
        :description="metrics.cost_saving_desc"
        tooltip="通过哈希秒传节省的处理时间"
      />
      
      <MetricCard
        title="LLM消耗"
        :value="formatLLMCost(metrics.llm_cost)"
        :description="metrics.llm_tokens_desc"
        tooltip="LLM Token消耗和预估费用"
      />
    </div>

    <!-- 图表区域 -->
    <a-row :gutter="[16, 16]" class="charts-section">
      <!-- 任务吞吐趋势图 -->
      <a-col :xs="24" :lg="16">
        <ThroughputChart
          :data="throughputData"
          :loading="loadingThroughput"
        />
      </a-col>
      
      <!-- 异常分布饼图 -->
      <a-col :xs="24" :lg="8">
        <ExceptionChart
          :data="exceptionData"
          :loading="loadingExceptions"
          @exception-click="handleExceptionClick"
        />
      </a-col>
    </a-row>

    <!-- 规则效能列表 -->
    <div class="rule-performance-section">
      <RulePerformance
        :data="rulePerformanceData"
        :loading="loadingRulePerformance"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import { dashboardAPI } from '@/api/dashboard'
import MetricCard from '@/components/Dashboard/MetricCard.vue'
import ThroughputChart from '@/components/Dashboard/ThroughputChart.vue'
import ExceptionChart from '@/components/Dashboard/ExceptionChart.vue'
import RulePerformance from '@/components/Dashboard/RulePerformance.vue'

/**
 * 仪表盘主页面
 * 显示系统核心指标、趋势图表和规则效能
 */

// 时间范围
const timeRange = ref('7days')

// 核心指标数据
const metrics = ref({
  total_tasks: 0,
  total_tasks_trend: 0,
  total_pages: 0,
  total_pages_trend: 0,
  processing_tasks: 0,
  processing_tasks_trend: 0,
  pending_audit_tasks: 0,
  pending_audit_tasks_trend: 0,
  push_failed_tasks: 0,
  stp_rate: 0,
  stp_rate_trend: 0,
  cost_saving: {
    saved_hours: 0,
    instant_tasks: 0,
    instant_pages: 0
  },
  cost_saving_desc: '',
  llm_cost: {
    total_tokens: 0,
    estimated_cost: 0
  },
  llm_tokens_desc: ''
})

// 任务吞吐数据
const throughputData = ref([])
const loadingThroughput = ref(false)

// 异常分布数据
const exceptionData = ref([])
const loadingExceptions = ref(false)

// 规则效能数据
const rulePerformanceData = ref([])
const loadingRulePerformance = ref(false)

/**
 * 格式化算力节省信息
 */
const formatCostSaving = (saving) => {
  if (!saving || typeof saving.saved_hours !== 'number') return '0小时'
  
  const hours = saving.saved_hours
  if (hours < 1) {
    return `${(hours * 60).toFixed(0)}分钟`
  }
  return `${hours.toFixed(1)}小时`
}

/**
 * 格式化LLM消耗信息
 */
const formatLLMCost = (cost) => {
  if (!cost || typeof cost.estimated_cost !== 'number') return '¥0'
  return `¥${cost.estimated_cost.toFixed(2)}`
}

/**
 * 加载核心指标数据
 */
const loadMetrics = async () => {
  try {
    const response = await dashboardAPI.getMetrics({
      time_range: timeRange.value
    })
    
    if (response.code === 200) {
      const data = response.data
      
      // 映射后端返回的字段名到前端使用的字段名
      metrics.value = {
        total_tasks: data.total_tasks || 0,
        total_tasks_trend: 0, // 后端暂未返回趋势数据
        total_pages: data.total_pages || 0,
        total_pages_trend: 0,
        processing_tasks: data.processing_count || 0,
        processing_tasks_trend: 0,
        pending_audit_tasks: data.pending_audit_count || 0,
        pending_audit_tasks_trend: 0,
        push_failed_tasks: data.push_failed_count || 0,
        stp_rate: data.straight_through_rate || 0,
        stp_rate_trend: 0,
        cost_saving: {
          saved_hours: data.cost_savings?.saved_hours || 0,
          instant_tasks: data.cost_savings?.instant_count || 0,
          instant_pages: data.cost_savings?.instant_pages || 0
        },
        cost_saving_desc: `${data.cost_savings?.instant_count || 0}个任务，${data.cost_savings?.instant_pages || 0}页`,
        llm_cost: {
          total_tokens: data.llm_consumption?.total_tokens || 0,
          estimated_cost: data.llm_consumption?.total_cost || 0
        },
        llm_tokens_desc: `${(data.llm_consumption?.total_tokens || 0).toLocaleString()} tokens`
      }
    }
  } catch (error) {
    console.error('加载指标数据失败:', error)
    message.error('加载指标数据失败')
  }
}

/**
 * 加载任务吞吐趋势数据
 */
const loadThroughput = async () => {
  loadingThroughput.value = true
  try {
    const response = await dashboardAPI.getThroughput({
      time_range: timeRange.value
    })
    
    if (response.code === 200) {
      // 后端返回的数据在 data.throughput 中
      const data = response.data
      throughputData.value = Array.isArray(data.throughput) ? data.throughput : []
    }
  } catch (error) {
    console.error('加载吞吐趋势失败:', error)
    message.error('加载吞吐趋势失败')
  } finally {
    loadingThroughput.value = false
  }
}

/**
 * 加载异常分布数据
 */
const loadExceptions = async () => {
  loadingExceptions.value = true
  try {
    const response = await dashboardAPI.getExceptions({
      time_range: timeRange.value
    })
    
    if (response.code === 200) {
      // 后端返回的数据在 data.exceptions 中
      const data = response.data
      exceptionData.value = Array.isArray(data.exceptions) ? data.exceptions : []
    }
  } catch (error) {
    console.error('加载异常分布失败:', error)
    message.error('加载异常分布失败')
  } finally {
    loadingExceptions.value = false
  }
}

/**
 * 加载规则效能数据
 */
const loadRulePerformance = async () => {
  loadingRulePerformance.value = true
  try {
    const response = await dashboardAPI.getRulePerformance({
      time_range: timeRange.value
    })
    
    if (response.code === 200) {
      // 后端返回的数据在 data.rules 中
      const data = response.data
      rulePerformanceData.value = Array.isArray(data.rules) ? data.rules : []
    }
  } catch (error) {
    console.error('加载规则效能失败:', error)
    message.error('加载规则效能失败')
  } finally {
    loadingRulePerformance.value = false
  }
}

/**
 * 加载所有数据
 */
const loadAllData = async () => {
  await Promise.all([
    loadMetrics(),
    loadThroughput(),
    loadExceptions(),
    loadRulePerformance()
  ])
}

/**
 * 处理时间范围变化
 */
const handleTimeRangeChange = () => {
  loadAllData()
}

/**
 * 处理异常点击事件
 */
const handleExceptionClick = (exception) => {
  console.log('异常点击:', exception)
  // 可以在这里添加额外的处理逻辑
}

// 组件挂载时加载数据
onMounted(() => {
  loadAllData()
})
</script>

<style scoped>
.dashboard-container {
  padding: 24px;
  background-color: #f0f2f5;
  min-height: calc(100vh - 64px);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 0 4px;
}

.dashboard-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.85);
}

/* 指标卡片网格 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

/* 图表区域 */
.charts-section {
  margin-bottom: 24px;
}

/* 规则效能区域 */
.rule-performance-section {
  margin-bottom: 24px;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .dashboard-container {
    padding: 16px;
  }
  
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .metrics-grid {
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
  }
}

@media (max-width: 576px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
