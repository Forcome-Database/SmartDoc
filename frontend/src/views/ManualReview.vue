<template>
  <div class="manual-review">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>人工审核</h2>
      <span class="subtitle">待审核任务列表</span>
    </div>

    <!-- 搜索和筛选区域 -->
    <a-card class="filter-card">
      <a-form layout="inline" :model="filterForm">
        <a-form-item label="关键词">
          <a-input
            v-model:value="filterForm.keyword"
            placeholder="任务ID/文件名"
            allow-clear
            style="width: 180px"
            @pressEnter="handleSearch"
          />
        </a-form-item>
        
        <a-form-item label="规则">
          <a-select
            v-model:value="filterForm.rule_id"
            placeholder="选择规则"
            allow-clear
            style="width: 160px"
            :options="ruleOptions"
          />
        </a-form-item>
        
        <a-form-item label="置信度">
          <a-select
            v-model:value="filterForm.confidence_range"
            placeholder="置信度范围"
            allow-clear
            style="width: 140px"
          >
            <a-select-option value="high">高 (≥90%)</a-select-option>
            <a-select-option value="medium">中 (70%-90%)</a-select-option>
            <a-select-option value="low">低 (&lt;70%)</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item label="创建时间">
          <a-range-picker
            v-model:value="filterForm.dateRange"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </a-form-item>
        
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="handleSearch">
              <template #icon><SearchOutlined /></template>
              搜索
            </a-button>
            <a-button @click="handleReset">
              <template #icon><ReloadOutlined /></template>
              重置
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 批量操作栏 -->
    <div class="batch-actions" v-if="selectedRowKeys.length > 0">
      <a-space>
        <span>已选择 {{ selectedRowKeys.length }} 项</span>
        <a-button type="primary" @click="handleBatchApprove" :loading="batchLoading">
          <template #icon><CheckOutlined /></template>
          批量通过
        </a-button>
        <a-button danger @click="showBatchRejectModal" :loading="batchLoading">
          <template #icon><CloseOutlined /></template>
          批量驳回
        </a-button>
        <a-button @click="clearSelection">取消选择</a-button>
      </a-space>
    </div>

    <!-- 任务列表 -->
    <a-card class="list-card">
      <a-table
        :columns="columns"
        :data-source="taskList"
        :loading="loading"
        :pagination="pagination"
        :row-selection="rowSelection"
        :row-key="record => record.id"
        @change="handleTableChange"
      >
        <!-- 任务ID -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'id'">
            <a-tooltip :title="record.id">
              <span class="task-id">{{ record.id.substring(0, 8) }}...</span>
            </a-tooltip>
          </template>

          <!-- 文件名 -->
          <template v-else-if="column.key === 'file_name'">
            <div class="file-info">
              <FileTextOutlined class="file-icon" />
              <span class="file-name" :title="record.file_name">
                {{ record.file_name }}
              </span>
            </div>
          </template>

          <!-- 规则名称 -->
          <template v-else-if="column.key === 'rule_name'">
            <a-tag color="blue">{{ record.rule_name || '未知规则' }}</a-tag>
          </template>

          <!-- 页数 -->
          <template v-else-if="column.key === 'page_count'">
            <span>{{ record.page_count }} 页</span>
          </template>

          <!-- 平均置信度 -->
          <template v-else-if="column.key === 'avg_confidence'">
            <ConfidenceBadge :confidence="record.avg_confidence" />
          </template>

          <!-- 审核原因 -->
          <template v-else-if="column.key === 'audit_reasons'">
            <template v-if="record.audit_reasons && record.audit_reasons.length > 0">
              <a-tooltip>
                <template #title>
                  <ul class="reason-tooltip-list">
                    <li v-for="(reason, idx) in record.audit_reasons" :key="idx">
                      {{ formatAuditReason(reason) }}
                    </li>
                  </ul>
                </template>
                <div class="audit-reasons-cell">
                  <WarningOutlined class="warning-icon" />
                  <span class="reason-text">{{ formatAuditReason(record.audit_reasons[0]) }}</span>
                  <a-tag v-if="record.audit_reasons.length > 1" size="small" color="orange">
                    +{{ record.audit_reasons.length - 1 }}
                  </a-tag>
                </div>
              </a-tooltip>
            </template>
            <span v-else class="no-reason">-</span>
          </template>

          <!-- 状态 -->
          <template v-else-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>

          <!-- 创建时间 -->
          <template v-else-if="column.key === 'created_at'">
            <span>{{ formatDateTime(record.created_at) }}</span>
          </template>

          <!-- 操作 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="goToReview(record)">
                <template #icon><EyeOutlined /></template>
                审核
              </a-button>
              <a-button type="link" size="small" @click="handleQuickApprove(record)">
                <template #icon><CheckOutlined /></template>
                通过
              </a-button>
              <a-button type="link" danger size="small" @click="showRejectModal(record)">
                <template #icon><CloseOutlined /></template>
                驳回
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 驳回对话框 -->
    <a-modal
      v-model:open="rejectModalVisible"
      :title="isBatchReject ? '批量驳回任务' : '驳回任务'"
      @ok="handleReject"
      @cancel="rejectModalVisible = false"
      :confirm-loading="rejectLoading"
    >
      <a-form :label-col="{ span: 6 }">
        <a-form-item label="驳回原因" required>
          <a-textarea
            v-model:value="rejectReason"
            :rows="4"
            placeholder="请输入驳回原因"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  SearchOutlined,
  ReloadOutlined,
  CheckOutlined,
  CloseOutlined,
  EyeOutlined,
  FileTextOutlined,
  WarningOutlined
} from '@ant-design/icons-vue'
import { auditAPI } from '@/api/audit'
import { ruleAPI } from '@/api/rule'
import ConfidenceBadge from '@/components/Task/ConfidenceBadge.vue'
import dayjs from 'dayjs'

/**
 * 人工审核列表页面
 * 显示所有待审核任务，支持搜索、筛选、批量操作
 */

const router = useRouter()

// 加载状态
const loading = ref(false)
const batchLoading = ref(false)
const rejectLoading = ref(false)

// 任务列表
const taskList = ref([])

// 规则选项
const ruleOptions = ref([])

// 筛选表单
const filterForm = reactive({
  keyword: '',
  rule_id: undefined,
  confidence_range: undefined,
  dateRange: []
})

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total) => `共 ${total} 条`
})

// 选中的行
const selectedRowKeys = ref([])
const selectedRows = ref([])

// 行选择配置
const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys, rows) => {
    selectedRowKeys.value = keys
    selectedRows.value = rows
  }
}))

// 驳回对话框
const rejectModalVisible = ref(false)
const rejectReason = ref('')
const currentRejectTask = ref(null)
const isBatchReject = ref(false)

// 表格列配置
const columns = [
  {
    title: '任务ID',
    key: 'id',
    width: 120
  },
  {
    title: '文件名',
    key: 'file_name',
    ellipsis: true,
    width: 180
  },
  {
    title: '规则',
    key: 'rule_name',
    width: 120
  },
  {
    title: '页数',
    key: 'page_count',
    width: 70,
    align: 'center'
  },
  {
    title: '置信度',
    key: 'avg_confidence',
    width: 90,
    align: 'center',
    sorter: true
  },
  {
    title: '审核原因',
    key: 'audit_reasons',
    width: 200,
    ellipsis: true
  },
  {
    title: '状态',
    key: 'status',
    width: 90,
    align: 'center'
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 150,
    sorter: true
  },
  {
    title: '操作',
    key: 'action',
    width: 180,
    fixed: 'right'
  }
]

/**
 * 加载任务列表
 */
async function loadTaskList() {
  loading.value = true
  
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      keyword: filterForm.keyword || undefined,
      rule_id: filterForm.rule_id || undefined,
      confidence_range: filterForm.confidence_range || undefined,
      start_date: filterForm.dateRange?.[0] || undefined,
      end_date: filterForm.dateRange?.[1] || undefined
    }
    
    const response = await auditAPI.getPendingTasks(params)
    taskList.value = response.items || []
    pagination.total = response.total || 0
  } catch (error) {
    message.error('加载任务列表失败')
    console.error('Load task list error:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 加载规则列表
 */
async function loadRuleOptions() {
  try {
    const response = await ruleAPI.list({ page: 1, page_size: 100 })
    ruleOptions.value = (response.items || []).map(rule => ({
      label: rule.name,
      value: rule.id
    }))
  } catch (error) {
    console.error('Load rule options error:', error)
  }
}

/**
 * 搜索
 */
function handleSearch() {
  pagination.current = 1
  loadTaskList()
}

/**
 * 重置筛选
 */
function handleReset() {
  filterForm.keyword = ''
  filterForm.rule_id = undefined
  filterForm.confidence_range = undefined
  filterForm.dateRange = []
  pagination.current = 1
  loadTaskList()
}

/**
 * 表格变化（分页、排序）
 */
function handleTableChange(pag, filters, sorter) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadTaskList()
}

/**
 * 清除选择
 */
function clearSelection() {
  selectedRowKeys.value = []
  selectedRows.value = []
}

/**
 * 进入审核详情页
 */
function goToReview(record) {
  router.push({
    path: '/audit/detail',
    query: { taskId: record.id }
  })
}

/**
 * 快速通过
 */
async function handleQuickApprove(record) {
  Modal.confirm({
    title: '确认通过',
    content: `确定要通过任务 "${record.file_name}" 吗？`,
    onOk: async () => {
      try {
        await auditAPI.submitAudit(record.id, {
          action: 'approve',
          data: record.extracted_data
        })
        message.success('审核通过')
        loadTaskList()
      } catch (error) {
        message.error('操作失败')
        console.error('Quick approve error:', error)
      }
    }
  })
}

/**
 * 显示驳回对话框
 */
function showRejectModal(record) {
  currentRejectTask.value = record
  isBatchReject.value = false
  rejectReason.value = ''
  rejectModalVisible.value = true
}

/**
 * 显示批量驳回对话框
 */
function showBatchRejectModal() {
  isBatchReject.value = true
  rejectReason.value = ''
  rejectModalVisible.value = true
}

/**
 * 执行驳回
 */
async function handleReject() {
  if (!rejectReason.value.trim()) {
    message.warning('请输入驳回原因')
    return
  }
  
  rejectLoading.value = true
  
  try {
    if (isBatchReject.value) {
      // 批量驳回
      const promises = selectedRowKeys.value.map(taskId =>
        auditAPI.submitAudit(taskId, {
          action: 'reject',
          reason: rejectReason.value
        })
      )
      await Promise.all(promises)
      message.success(`已驳回 ${selectedRowKeys.value.length} 个任务`)
      clearSelection()
    } else {
      // 单个驳回
      await auditAPI.submitAudit(currentRejectTask.value.id, {
        action: 'reject',
        reason: rejectReason.value
      })
      message.success('任务已驳回')
    }
    
    rejectModalVisible.value = false
    loadTaskList()
  } catch (error) {
    message.error('驳回失败')
    console.error('Reject error:', error)
  } finally {
    rejectLoading.value = false
  }
}

/**
 * 批量通过
 */
async function handleBatchApprove() {
  Modal.confirm({
    title: '批量通过',
    content: `确定要通过选中的 ${selectedRowKeys.value.length} 个任务吗？`,
    onOk: async () => {
      batchLoading.value = true
      
      try {
        const promises = selectedRows.value.map(task =>
          auditAPI.submitAudit(task.id, {
            action: 'approve',
            data: task.extracted_data
          })
        )
        await Promise.all(promises)
        message.success(`已通过 ${selectedRowKeys.value.length} 个任务`)
        clearSelection()
        loadTaskList()
      } catch (error) {
        message.error('批量通过失败')
        console.error('Batch approve error:', error)
      } finally {
        batchLoading.value = false
      }
    }
  })
}

/**
 * 获取状态颜色
 */
function getStatusColor(status) {
  const colorMap = {
    pending_audit: 'orange',
    completed: 'green',
    rejected: 'red'
  }
  return colorMap[status] || 'default'
}

/**
 * 获取状态文本
 */
function getStatusText(status) {
  const textMap = {
    pending_audit: '待审核',
    completed: '已完成',
    rejected: '已驳回'
  }
  return textMap[status] || status
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateStr) {
  if (!dateStr) return '-'
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

/**
 * 格式化审核原因
 * 支持字符串和对象两种格式
 */
function formatAuditReason(reason) {
  if (!reason) return '-'
  
  // 如果是字符串，直接返回
  if (typeof reason === 'string') {
    return reason
  }
  
  // 如果是对象，提取message或组合字段信息
  if (typeof reason === 'object') {
    if (reason.message) {
      return reason.field ? `${reason.field}: ${reason.message}` : reason.message
    }
    if (reason.reason) {
      return reason.reason
    }
    // 根据type生成描述
    if (reason.type === 'validation_error') {
      return `校验失败: ${reason.field || '未知字段'}`
    }
    if (reason.type === 'confidence_low') {
      return `置信度低: ${reason.field || '未知字段'}`
    }
    // 默认返回JSON字符串
    return JSON.stringify(reason)
  }
  
  return String(reason)
}

// 初始化
onMounted(() => {
  loadTaskList()
  loadRuleOptions()
})
</script>

<style scoped>
.manual-review {
  padding: 24px;
  background: #f0f2f5;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  display: inline;
}

.page-header .subtitle {
  margin-left: 12px;
  color: #666;
  font-size: 14px;
}

.filter-card {
  margin-bottom: 16px;
}

.batch-actions {
  padding: 12px 16px;
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 4px;
  margin-bottom: 16px;
}

.list-card {
  margin-bottom: 24px;
}

.task-id {
  font-family: monospace;
  color: #1890ff;
  cursor: pointer;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  color: #1890ff;
}

.file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.audit-reasons-cell {
  display: flex;
  align-items: center;
  gap: 4px;
}

.warning-icon {
  color: #faad14;
  flex-shrink: 0;
}

.reason-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #666;
  font-size: 13px;
}

.no-reason {
  color: #999;
}

.reason-tooltip-list {
  margin: 0;
  padding-left: 16px;
}

.reason-tooltip-list li {
  margin-bottom: 4px;
}

.reason-tooltip-list li:last-child {
  margin-bottom: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .manual-review {
    padding: 16px;
  }
  
  .filter-card :deep(.ant-form-item) {
    margin-bottom: 12px;
  }
}
</style>
