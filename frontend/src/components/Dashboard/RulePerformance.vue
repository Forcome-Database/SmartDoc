<template>
  <a-card title="规则效能 Top 10" :bordered="false" class="rule-performance-card">
    <template #extra>
      <a-tooltip title="按任务量降序排列，显示平均耗时和人工干预率">
        <InfoCircleOutlined />
      </a-tooltip>
    </template>
    
    <a-spin :spinning="loading">
      <div v-if="!loading && performanceData.length === 0" class="empty-state">
        <a-empty description="暂无数据" />
      </div>
      
      <a-table
        v-else
        :columns="columns"
        :data-source="performanceData"
        :pagination="false"
        :scroll="{ x: 'max-content' }"
        size="middle"
        class="performance-table"
      >
        <!-- 规则名称列 -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'rule_name'">
            <a @click="handleRuleClick(record)">
              {{ record.rule_name }}
            </a>
          </template>
          
          <!-- 任务量列 -->
          <template v-else-if="column.key === 'task_count'">
            <span class="task-count">
              {{ record.task_count.toLocaleString() }}
            </span>
          </template>
          
          <!-- 平均耗时列 -->
          <template v-else-if="column.key === 'avg_duration'">
            <span>{{ formatDuration(record.avg_duration) }}</span>
          </template>
          
          <!-- 人工干预率列 -->
          <template v-else-if="column.key === 'intervention_rate'">
            <a-tag :color="getInterventionRateColor(record.intervention_rate)">
              {{ record.intervention_rate.toFixed(1) }}%
            </a-tag>
          </template>
        </template>
      </a-table>
    </a-spin>
  </a-card>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { InfoCircleOutlined } from '@ant-design/icons-vue'

/**
 * 规则效能列表组件
 * 显示 Top 10 规则的任务量、平均耗时和人工干预率
 */
const props = defineProps({
  // 规则效能数据
  data: {
    type: Array,
    default: () => []
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false
  }
})

const router = useRouter()

// 表格列定义
const columns = [
  {
    title: '排名',
    key: 'rank',
    width: 60,
    align: 'center',
    customRender: ({ index }) => index + 1
  },
  {
    title: '规则名称',
    key: 'rule_name',
    dataIndex: 'rule_name',
    ellipsis: true
  },
  {
    title: '任务量',
    key: 'task_count',
    dataIndex: 'task_count',
    width: 100,
    align: 'right',
    sorter: (a, b) => a.task_count - b.task_count
  },
  {
    title: '平均耗时',
    key: 'avg_duration',
    dataIndex: 'avg_duration',
    width: 120,
    align: 'right',
    sorter: (a, b) => a.avg_duration - b.avg_duration
  },
  {
    title: '人工干预率',
    key: 'intervention_rate',
    dataIndex: 'intervention_rate',
    width: 120,
    align: 'center',
    sorter: (a, b) => a.intervention_rate - b.intervention_rate
  }
]

// 处理后的数据（添加 key）
const performanceData = computed(() => {
  return (props.data || []).map((item, index) => ({
    ...item,
    key: item.rule_id || index
  }))
})

/**
 * 格式化耗时
 * @param {number} seconds - 秒数
 * @returns {string} 格式化后的时间字符串
 */
const formatDuration = (seconds) => {
  if (!seconds) return '-'
  
  if (seconds < 60) {
    return `${seconds.toFixed(1)}秒`
  }
  
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  
  if (minutes < 60) {
    return `${minutes}分${remainingSeconds.toFixed(0)}秒`
  }
  
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  
  return `${hours}小时${remainingMinutes}分`
}

/**
 * 获取人工干预率的颜色
 * @param {number} rate - 干预率（百分比）
 * @returns {string} 颜色值
 */
const getInterventionRateColor = (rate) => {
  if (rate < 10) {
    return 'success' // 绿色：低干预率
  } else if (rate < 30) {
    return 'warning' // 黄色：中等干预率
  } else {
    return 'error' // 红色：高干预率
  }
}

/**
 * 处理规则名称点击事件
 * 跳转到该规则的任务列表
 */
const handleRuleClick = (record) => {
  router.push({
    name: 'TaskList',
    query: {
      rule_id: record.rule_id
    }
  })
}
</script>

<style scoped>
.rule-performance-card {
  height: 100%;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.performance-table :deep(.ant-table) {
  font-size: 13px;
}

.performance-table :deep(.ant-table-thead > tr > th) {
  background-color: #fafafa;
  font-weight: 600;
}

.performance-table :deep(.ant-table-tbody > tr:hover) {
  cursor: pointer;
}

.task-count {
  font-weight: 600;
  color: #1890ff;
}

.performance-table a {
  color: #1890ff;
  text-decoration: none;
}

.performance-table a:hover {
  text-decoration: underline;
}
</style>
