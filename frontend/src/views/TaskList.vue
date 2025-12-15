<template>
  <div class="task-list-page p-6">
    <!-- 页面标题和操作栏 -->
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">任务列表</h1>
      <a-space>
        <a-button type="primary" @click="handleRefresh">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
        <a-button @click="handleExport" :loading="exporting">
          <template #icon><ExportOutlined /></template>
          导出
        </a-button>
      </a-space>
    </div>

    <!-- 筛选器 -->
    <a-card class="mb-4">
      <a-form layout="inline" :model="filters">
        <a-form-item label="任务ID/文件名">
          <a-input
            v-model:value="filters.search"
            placeholder="搜索任务ID或文件名"
            style="width: 200px"
            allow-clear
            @pressEnter="handleSearch"
          >
            <template #prefix><SearchOutlined /></template>
          </a-input>
        </a-form-item>

        <a-form-item label="状态">
          <a-select
            v-model:value="filters.status"
            placeholder="全部状态"
            style="width: 150px"
            allow-clear
            @change="handleSearch"
          >
            <a-select-option
              v-for="(label, value) in TASK_STATUS_LABELS"
              :key="value"
              :value="value"
            >
              {{ label }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="规则">
          <a-select
            v-model:value="filters.rule_id"
            placeholder="全部规则"
            style="width: 200px"
            allow-clear
            show-search
            :filter-option="filterRuleOption"
            @change="handleSearch"
          >
            <a-select-option
              v-for="rule in rules"
              :key="rule.id"
              :value="rule.id"
            >
              {{ rule.name }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="时间范围">
          <a-range-picker
            v-model:value="filters.date_range"
            :placeholder="['开始日期', '结束日期']"
            format="YYYY-MM-DD"
            @change="handleSearch"
          />
        </a-form-item>

        <a-form-item>
          <a-space>
            <a-button type="primary" @click="handleSearch">
              <template #icon><SearchOutlined /></template>
              查询
            </a-button>
            <a-button @click="handleReset">重置</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 任务列表表格 -->
    <a-card>
      <a-table
        :columns="columns"
        :data-source="tasks"
        :loading="loading"
        :pagination="pagination"
        :row-key="record => record.id"
        :scroll="{ x: 1600 }"
        @change="handleTableChange"
      >
        <!-- 任务ID列 -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'id'">
            <a-button type="link" @click="handleViewDetail(record)">
              {{ record.id }}
            </a-button>
          </template>

          <!-- 文件名列 -->
          <template v-else-if="column.key === 'file_name'">
            <a-tooltip :title="record.file_name">
              <span>{{ truncate(record.file_name, 30) }}</span>
            </a-tooltip>
          </template>

          <!-- 规则版本列 -->
          <template v-else-if="column.key === 'rule_version'">
            <div>
              <div class="text-sm">{{ record.rule_name || '-' }}</div>
              <div class="text-xs text-gray-500">{{ record.rule_version }}</div>
            </div>
          </template>

          <!-- 置信度列 -->
          <template v-else-if="column.key === 'confidence'">
            <ConfidenceBadge :score="record.avg_confidence" />
          </template>

          <!-- 状态列 -->
          <template v-else-if="column.key === 'status'">
            <StatusTag :status="record.status" />
          </template>

          <!-- 流程状态列 -->
          <template v-else-if="column.key === 'flow_status'">
            <FlowStatusIndicator :flow-status="record.flow_status" />
          </template>

          <!-- 耗时列 -->
          <template v-else-if="column.key === 'duration'">
            <span>{{ record.duration_seconds ? `${record.duration_seconds}s` : '-' }}</span>
          </template>

          <!-- 创建时间列 -->
          <template v-else-if="column.key === 'created_at'">
            <a-tooltip :title="formatDateTime(record.created_at)">
              <span>{{ formatRelativeTime(record.created_at) }}</span>
            </a-tooltip>
          </template>

          <!-- 操作列 -->
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-button type="link" size="small" @click="handleViewDetail(record)">
                详情
              </a-button>
              <a-button
                v-if="canRetry(record.status)"
                type="link"
                size="small"
                @click="handleRetry(record)"
              >
                重试
              </a-button>
              <a-button
                v-if="canRepush(record.status)"
                type="link"
                size="small"
                @click="handleRepush(record)"
              >
                重推
              </a-button>
              <a-button
                v-if="canCancel(record.status)"
                type="link"
                size="small"
                @click="handleCancel(record)"
              >
                取消
              </a-button>
              <a-popconfirm
                v-if="canDelete(record.status)"
                title="确定要删除这个任务吗？"
                @confirm="handleDelete(record)"
              >
                <a-button type="link" size="small" danger>
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 任务详情对话框 -->
    <TaskDetailDialog
      v-model:visible="detailVisible"
      :task-id="selectedTaskId"
      @refresh="handleRefresh"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import {
  ReloadOutlined,
  ExportOutlined,
  SearchOutlined
} from '@ant-design/icons-vue'
import { taskAPI } from '@/api/task'
import { ruleAPI } from '@/api/rule'
import { TASK_STATUS, TASK_STATUS_LABELS } from '@/utils/constants'
import { formatDateTime, formatRelativeTime, formatDuration, truncate } from '@/utils/format'
import StatusTag from '@/components/Task/StatusTag.vue'
import ConfidenceBadge from '@/components/Task/ConfidenceBadge.vue'
import TaskDetailDialog from '@/components/Task/TaskDetailDialog.vue'
import FlowStatusIndicator from '@/components/Task/FlowStatusIndicator.vue'

const router = useRouter()

// 数据状态
const loading = ref(false)
const exporting = ref(false)
const tasks = ref([])
const rules = ref([])
const detailVisible = ref(false)
const selectedTaskId = ref(null)

// 筛选器
const filters = reactive({
  search: '',
  status: undefined,
  rule_id: undefined,
  date_range: null
})

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total) => `共 ${total} 条记录`,
  pageSizeOptions: ['10', '20', '50', '100']
})

// 表格列配置
const columns = [
  {
    title: '任务ID',
    dataIndex: 'id',
    key: 'id',
    width: 280,
    fixed: 'left'
  },
  {
    title: '文件名',
    dataIndex: 'file_name',
    key: 'file_name',
    width: 200,
    ellipsis: true
  },
  {
    title: '页数',
    dataIndex: 'page_count',
    key: 'page_count',
    width: 80,
    align: 'center'
  },
  {
    title: '规则版本',
    key: 'rule_version',
    width: 150
  },
  {
    title: '置信度',
    key: 'confidence',
    width: 120,
    align: 'center'
  },
  {
    title: '状态',
    key: 'status',
    width: 120,
    align: 'center'
  },
  {
    title: '流程',
    key: 'flow_status',
    width: 180,
    align: 'center'
  },
  {
    title: '耗时',
    key: 'duration',
    width: 100,
    align: 'right'
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 180
  },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    fixed: 'right',
    align: 'center'
  }
]

/**
 * 加载任务列表
 */
async function loadTasks() {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      search: filters.search || undefined,
      status: filters.status || undefined,
      rule_id: filters.rule_id || undefined
    }

    // 处理日期范围
    if (filters.date_range && filters.date_range.length === 2) {
      params.start_date = filters.date_range[0].format('YYYY-MM-DD')
      params.end_date = filters.date_range[1].format('YYYY-MM-DD')
    }

    const response = await taskAPI.list(params)
    // 安全地访问响应数据
    if (response && response.items) {
      tasks.value = response.items || []
      pagination.total = response.total || 0
    } else {
      tasks.value = []
      pagination.total = 0
    }
  } catch (error) {
    message.error('加载任务列表失败：' + (error.message || '未知错误'))
    tasks.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

/**
 * 加载规则列表（用于筛选）
 */
async function loadRules() {
  try {
    const response = await ruleAPI.list({ page: 1, page_size: 1000 })
    // 安全地访问响应数据
    if (response && response.items) {
      rules.value = response.items || []
    } else {
      rules.value = []
    }
  } catch (error) {
    console.error('加载规则列表失败:', error)
    // 失败时设置为空数组，不影响页面其他功能
    rules.value = []
  }
}

/**
 * 规则选项过滤
 */
function filterRuleOption(input, option) {
  return option.children[0].children.toLowerCase().includes(input.toLowerCase())
}

/**
 * 处理搜索
 */
function handleSearch() {
  pagination.current = 1
  loadTasks()
}

/**
 * 处理重置
 */
function handleReset() {
  filters.search = ''
  filters.status = undefined
  filters.rule_id = undefined
  filters.date_range = null
  pagination.current = 1
  loadTasks()
}

/**
 * 处理刷新
 */
function handleRefresh() {
  loadTasks()
}

/**
 * 处理表格变化（分页、排序等）
 */
function handleTableChange(pag, filters, sorter) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadTasks()
}

/**
 * 查看任务详情
 */
function handleViewDetail(record) {
  selectedTaskId.value = record.id
  detailVisible.value = true
}

/**
 * 跳转到审核页面
 */
function handleAudit(record) {
  router.push({
    name: 'AuditWorkbench',
    query: { taskId: record.id }
  })
}

/**
 * 导出任务列表
 */
async function handleExport() {
  exporting.value = true
  try {
    const params = {
      search: filters.search || undefined,
      status: filters.status || undefined,
      rule_id: filters.rule_id || undefined
    }

    // 处理日期范围
    if (filters.date_range && filters.date_range.length === 2) {
      params.start_date = filters.date_range[0].format('YYYY-MM-DD')
      params.end_date = filters.date_range[1].format('YYYY-MM-DD')
    }

    const blob = await taskAPI.export(params)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `tasks_${Date.now()}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    message.success('导出成功')
  } catch (error) {
    message.error('导出失败：' + (error.message || '未知错误'))
  } finally {
    exporting.value = false
  }
}

/**
 * 判断是否可以重试
 */
function canRetry(status) {
  return status === TASK_STATUS.FAILED || status === TASK_STATUS.REJECTED
}

/**
 * 判断是否可以重推
 */
function canRepush(status) {
  return status === TASK_STATUS.PUSH_FAILED
}

/**
 * 判断是否可以取消
 */
function canCancel(status) {
  return status === TASK_STATUS.QUEUED
}

/**
 * 判断是否可以删除
 */
function canDelete(status) {
  return [
    TASK_STATUS.FAILED,
    TASK_STATUS.REJECTED,
    TASK_STATUS.COMPLETED,
    TASK_STATUS.PUSH_SUCCESS,
    TASK_STATUS.PUSH_FAILED
  ].includes(status)
}

/**
 * 重试任务
 */
async function handleRetry(record) {
  try {
    await taskAPI.retry(record.id)
    message.success('任务已重新加入队列')
    loadTasks()
  } catch (error) {
    message.error('重试失败：' + (error.message || '未知错误'))
  }
}

/**
 * 重新推送任务
 */
async function handleRepush(record) {
  try {
    await taskAPI.repush(record.id)
    message.success('任务已重新加入推送队列')
    loadTasks()
  } catch (error) {
    message.error('重推失败：' + (error.message || '未知错误'))
  }
}

/**
 * 取消任务
 */
async function handleCancel(record) {
  try {
    await taskAPI.cancel(record.id)
    message.success('任务已取消')
    loadTasks()
  } catch (error) {
    message.error('取消失败：' + (error.message || '未知错误'))
  }
}

/**
 * 删除任务
 */
async function handleDelete(record) {
  try {
    await taskAPI.delete(record.id)
    message.success('任务已删除')
    loadTasks()
  } catch (error) {
    message.error('删除失败：' + (error.message || '未知错误'))
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadTasks()
  loadRules()
})
</script>

<style scoped>
.task-list-page {
  background-color: #f0f2f5;
  min-height: 100vh;
}

:deep(.ant-table) {
  font-size: 14px;
}

:deep(.ant-table-thead > tr > th) {
  background-color: #fafafa;
  font-weight: 600;
}
</style>
