<template>
  <a-modal
    v-model:open="visible"
    title="任务详情"
    width="1200px"
    :footer="null"
    @cancel="handleClose"
  >
    <a-spin :spinning="loading">
      <div v-if="task" class="task-detail">
        <!-- 基本信息 -->
        <a-descriptions title="基本信息" :column="2" bordered class="mb-4">
          <a-descriptions-item label="任务ID">
            {{ task.id }}
          </a-descriptions-item>
          <a-descriptions-item label="状态">
            <StatusTag :status="task.status" />
          </a-descriptions-item>
          <a-descriptions-item label="文件名">
            {{ task.file_name }}
          </a-descriptions-item>
          <a-descriptions-item label="页数">
            {{ task.page_count }}
          </a-descriptions-item>
          <a-descriptions-item label="规则名称">
            {{ task.rule_name || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="规则版本">
            {{ task.rule_version }}
          </a-descriptions-item>
          <a-descriptions-item label="是否秒传">
            <a-tag :color="task.is_instant ? 'success' : 'default'">
              {{ task.is_instant ? '是' : '否' }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="平均置信度">
            <ConfidenceBadge :score="computedAvgConfidence" />
          </a-descriptions-item>
          <a-descriptions-item label="创建时间">
            {{ formatDateTime(task.created_at) }}
          </a-descriptions-item>
          <a-descriptions-item label="开始时间">
            {{ formatDateTime(task.started_at) }}
          </a-descriptions-item>
          <a-descriptions-item label="完成时间">
            {{ formatDateTime(task.completed_at) }}
          </a-descriptions-item>
          <a-descriptions-item label="处理耗时">
            {{ computedDuration }}
          </a-descriptions-item>
        </a-descriptions>

        <!-- 审核信息（如果有） -->
        <a-descriptions
          v-if="task.audit_reasons && task.audit_reasons.length > 0"
          title="审核信息"
          :column="1"
          bordered
          class="mb-4"
        >
          <a-descriptions-item label="审核原因">
            <a-space direction="vertical">
              <a-tag
                v-for="(reason, index) in task.audit_reasons"
                :key="index"
                color="warning"
              >
                {{ formatAuditReason(reason) }}
              </a-tag>
            </a-space>
          </a-descriptions-item>
          <a-descriptions-item v-if="task.auditor_name" label="审核人">
            {{ task.auditor_name }}
          </a-descriptions-item>
          <a-descriptions-item v-if="task.audited_at" label="审核时间">
            {{ formatDateTime(task.audited_at) }}
          </a-descriptions-item>
        </a-descriptions>

        <!-- LLM信息（如果有） -->
        <a-descriptions
          v-if="task.llm_token_count > 0"
          title="LLM信息"
          :column="2"
          bordered
          class="mb-4"
        >
          <a-descriptions-item label="Token消耗">
            {{ formatNumber(task.llm_token_count) }}
          </a-descriptions-item>
          <a-descriptions-item label="预估费用">
            ¥{{ task.llm_cost ? task.llm_cost.toFixed(4) : '0.0000' }}
          </a-descriptions-item>
        </a-descriptions>

        <!-- 流程状态概览 -->
        <div v-if="task.flow_status" class="flow-overview mb-4">
          <a-card size="small" title="处理流程">
            <div class="flow-steps">
              <div class="flow-step-item" :class="getFlowStepClass(task.flow_status.ocr_status)">
                <div class="step-icon">
                  <CheckCircleOutlined v-if="task.flow_status.ocr_status === 'completed'" />
                  <LoadingOutlined v-else-if="task.flow_status.ocr_status === 'processing'" spin />
                  <CloseCircleOutlined v-else-if="task.flow_status.ocr_status === 'failed'" />
                  <ClockCircleOutlined v-else />
                </div>
                <div class="step-label">OCR识别</div>
                <div class="step-status">{{ getFlowStatusLabel(task.flow_status.ocr_status) }}</div>
              </div>
              <div class="step-connector" :class="{ active: task.flow_status.ocr_status === 'completed' }"></div>
              <div class="flow-step-item" :class="getFlowStepClass(task.flow_status.pipeline_status)">
                <div class="step-icon">
                  <CheckCircleOutlined v-if="task.flow_status.pipeline_status === 'success'" />
                  <LoadingOutlined v-else-if="task.flow_status.pipeline_status === 'running'" spin />
                  <CloseCircleOutlined v-else-if="task.flow_status.pipeline_status === 'failed'" />
                  <MinusCircleOutlined v-else-if="task.flow_status.pipeline_status === 'skipped'" />
                  <ClockCircleOutlined v-else />
                </div>
                <div class="step-label">数据管道</div>
                <div class="step-status">{{ getFlowStatusLabel(task.flow_status.pipeline_status) }}</div>
              </div>
              <div class="step-connector" :class="{ active: ['success', 'skipped'].includes(task.flow_status.pipeline_status) }"></div>
              <div class="flow-step-item" :class="getFlowStepClass(task.flow_status.push_status)">
                <div class="step-icon">
                  <CheckCircleOutlined v-if="task.flow_status.push_status === 'success'" />
                  <LoadingOutlined v-else-if="task.flow_status.push_status === 'pushing'" spin />
                  <CloseCircleOutlined v-else-if="task.flow_status.push_status === 'failed'" />
                  <MinusCircleOutlined v-else-if="task.flow_status.push_status === 'skipped'" />
                  <ClockCircleOutlined v-else />
                </div>
                <div class="step-label">推送下游</div>
                <div class="step-status">{{ getFlowStatusLabel(task.flow_status.push_status) }}</div>
              </div>
            </div>
          </a-card>
        </div>

        <!-- 标签页：OCR结果、提取结果、管道执行、推送日志、状态时间线 -->
        <a-tabs v-model:activeKey="activeTab">
          <!-- OCR结果 -->
          <a-tab-pane key="ocr" tab="OCR结果">
            <div v-if="task.ocr_text" class="ocr-text-container">
              <a-typography-paragraph
                :copyable="{ text: task.ocr_text }"
                class="whitespace-pre-wrap"
              >
                {{ task.ocr_text }}
              </a-typography-paragraph>
            </div>
            <a-empty v-else description="暂无OCR结果" />
          </a-tab-pane>

          <!-- 提取结果 -->
          <a-tab-pane key="extracted" tab="提取结果">
            <div v-if="originalExtractedData && Object.keys(originalExtractedData).length > 0" class="extracted-data-container">
              <!-- 工具栏 -->
              <div class="flex justify-end mb-3">
                <a-button size="small" @click="copyExtractedData">
                  <template #icon><CopyOutlined /></template>
                  复制全部
                </a-button>
              </div>
              <!-- 提取字段列表 -->
              <div class="extracted-fields">
                <div
                  v-for="(value, key) in originalExtractedData"
                  :key="key"
                  class="extracted-field-item"
                >
                  <div class="field-header">
                    <span class="field-key">{{ key }}</span>
                    <div class="field-actions">
                      <ConfidenceBadge
                        v-if="task.confidence_scores && task.confidence_scores[key]"
                        :score="task.confidence_scores[key]"
                        class="mr-2"
                      />
                      <a-button type="text" size="small" @click="copyFieldValue(key, value)">
                        <template #icon><CopyOutlined /></template>
                      </a-button>
                    </div>
                  </div>
                  <div class="field-value" :class="getValueClass(value)">
                    <!-- 对象或数组：格式化JSON显示 -->
                    <template v-if="isComplexValue(value)">
                      <pre class="json-value">{{ formatJSON(value) }}</pre>
                    </template>
                    <!-- 布尔值 -->
                    <template v-else-if="typeof value === 'boolean'">
                      <a-tag :color="value ? 'success' : 'default'">{{ value ? '是' : '否' }}</a-tag>
                    </template>
                    <!-- 数字 -->
                    <template v-else-if="typeof value === 'number'">
                      <span class="number-value">{{ formatNumberValue(value) }}</span>
                    </template>
                    <!-- 空值 -->
                    <template v-else-if="value === null || value === undefined || value === ''">
                      <span class="empty-value">-</span>
                    </template>
                    <!-- 长文本 -->
                    <template v-else-if="String(value).length > 100">
                      <a-typography-paragraph
                        :ellipsis="{ rows: 3, expandable: true, symbol: '展开' }"
                        :content="String(value)"
                        class="long-text-value"
                      />
                    </template>
                    <!-- 普通文本 -->
                    <template v-else>
                      <span class="text-value">{{ value }}</span>
                    </template>
                  </div>
                </div>
              </div>
            </div>
            <a-empty v-else description="暂无提取结果" />
          </a-tab-pane>

          <!-- 管道执行 -->
          <a-tab-pane key="pipeline" tab="管道执行">
            <div v-if="task.pipeline_executions && task.pipeline_executions.length > 0">
              <a-collapse v-model:activeKey="activePipelineExec">
                <a-collapse-panel
                  v-for="exec in task.pipeline_executions"
                  :key="exec.id"
                  :header="getPipelineExecHeader(exec)"
                >
                  <a-descriptions :column="2" bordered size="small">
                    <a-descriptions-item label="执行ID">
                      {{ exec.id }}
                    </a-descriptions-item>
                    <a-descriptions-item label="管道名称">
                      {{ exec.pipeline_name || exec.pipeline_id }}
                    </a-descriptions-item>
                    <a-descriptions-item label="状态">
                      <a-tag :color="getPipelineStatusColor(exec.status)">
                        {{ getPipelineStatusLabel(exec.status) }}
                      </a-tag>
                    </a-descriptions-item>
                    <a-descriptions-item label="重试次数">
                      {{ exec.retry_count }}
                    </a-descriptions-item>
                    <a-descriptions-item label="耗时">
                      {{ exec.duration_ms ? `${exec.duration_ms}ms` : '-' }}
                    </a-descriptions-item>
                    <a-descriptions-item label="开始时间">
                      {{ formatDateTime(exec.started_at) }}
                    </a-descriptions-item>
                    <a-descriptions-item v-if="exec.error_message" label="错误信息" :span="2">
                      <span class="text-red-500">{{ exec.error_message }}</span>
                    </a-descriptions-item>
                    <a-descriptions-item v-if="exec.stdout" label="标准输出" :span="2">
                      <pre class="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-32">{{ exec.stdout }}</pre>
                    </a-descriptions-item>
                    <a-descriptions-item v-if="exec.stderr" label="标准错误" :span="2">
                      <pre class="text-xs bg-red-50 p-2 rounded overflow-auto max-h-32 text-red-600">{{ exec.stderr }}</pre>
                    </a-descriptions-item>
                    <a-descriptions-item v-if="exec.output_data" label="输出数据" :span="2">
                      <pre class="text-xs bg-green-50 p-2 rounded overflow-auto max-h-40">{{ formatJSON(exec.output_data) }}</pre>
                    </a-descriptions-item>
                  </a-descriptions>
                </a-collapse-panel>
              </a-collapse>
            </div>
            <a-empty v-else description="暂无管道执行记录" />
          </a-tab-pane>

          <!-- 推送日志 -->
          <a-tab-pane key="push_logs" tab="推送日志">
            <div v-if="task.push_logs && task.push_logs.length > 0">
              <a-collapse v-model:activeKey="activePushLog">
                <a-collapse-panel
                  v-for="log in task.push_logs"
                  :key="log.id"
                  :header="getPushLogHeader(log)"
                >
                  <a-descriptions :column="1" bordered size="small">
                    <a-descriptions-item label="目标系统">
                      {{ log.webhook_name }}
                    </a-descriptions-item>
                    <a-descriptions-item label="HTTP状态">
                      <a-tag :color="log.http_status >= 200 && log.http_status < 300 ? 'success' : 'error'">
                        {{ log.http_status }}
                      </a-tag>
                    </a-descriptions-item>
                    <a-descriptions-item label="耗时">
                      {{ log.duration_ms }}ms
                    </a-descriptions-item>
                    <a-descriptions-item label="重试次数">
                      {{ log.retry_count }}
                    </a-descriptions-item>
                    <a-descriptions-item label="推送时间">
                      {{ formatDateTime(log.created_at) }}
                    </a-descriptions-item>
                    <a-descriptions-item label="请求体">
                      <pre class="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-40">{{ formatJSON(log.request_body) }}</pre>
                    </a-descriptions-item>
                    <a-descriptions-item label="响应体">
                      <pre class="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-40">{{ formatJSON(log.response_body) }}</pre>
                    </a-descriptions-item>
                  </a-descriptions>
                </a-collapse-panel>
              </a-collapse>
            </div>
            <a-empty v-else description="暂无推送日志" />
          </a-tab-pane>

          <!-- 状态时间线 -->
          <a-tab-pane key="timeline" tab="状态流转">
            <a-timeline mode="left">
              <a-timeline-item
                v-for="(event, index) in statusTimeline"
                :key="index"
                :color="getTimelineColor(event.status)"
              >
                <template #label>
                  {{ formatDateTime(event.timestamp) }}
                </template>
                <div>
                  <StatusTag :status="event.status" />
                  <div v-if="event.duration" class="text-xs text-gray-500 mt-1">
                    停留时长: {{ formatDuration(event.duration) }}
                  </div>
                </div>
              </a-timeline-item>
            </a-timeline>
          </a-tab-pane>
        </a-tabs>
      </div>
    </a-spin>
  </a-modal>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { 
  CopyOutlined, 
  CheckCircleOutlined, 
  CloseCircleOutlined, 
  ClockCircleOutlined,
  LoadingOutlined,
  MinusCircleOutlined
} from '@ant-design/icons-vue'
import { taskAPI } from '@/api/task'
import { TASK_STATUS, TASK_STATUS_LABELS } from '@/utils/constants'
import { formatDateTime, formatDuration, formatNumber } from '@/utils/format'
import StatusTag from './StatusTag.vue'
import ConfidenceBadge from './ConfidenceBadge.vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  taskId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'refresh'])

// 数据状态
const loading = ref(false)
const task = ref(null)
const activeTab = ref('ocr')
const activePushLog = ref([])
const activePipelineExec = ref([])

// 计算属性：对话框可见性
const visible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

/**
 * 计算原始提取数据
 * 优先从管道执行记录的 input_data.extracted_data 获取（OCR原始提取结果）
 * 如果没有管道执行记录，则使用 task.extracted_data
 */
const originalExtractedData = computed(() => {
  if (!task.value) return null
  
  // 如果有管道执行记录，从最早的执行记录中获取原始数据
  if (task.value.pipeline_executions && task.value.pipeline_executions.length > 0) {
    // 按创建时间排序，取最早的一条（原始输入数据）
    const sortedExecs = [...task.value.pipeline_executions].sort(
      (a, b) => new Date(a.created_at) - new Date(b.created_at)
    )
    const firstExec = sortedExecs[0]
    if (firstExec.input_data && firstExec.input_data.extracted_data) {
      return firstExec.input_data.extracted_data
    }
  }
  
  // 没有管道执行记录，直接使用 task.extracted_data
  return task.value.extracted_data
})

/**
 * 计算处理耗时
 */
const computedDuration = computed(() => {
  if (!task.value) return '-'
  
  // 如果有 duration_ms 字段直接使用
  if (task.value.duration_ms) {
    return formatDuration(task.value.duration_ms)
  }
  
  // 否则从 started_at 和 completed_at 计算
  if (task.value.started_at && task.value.completed_at) {
    const start = new Date(task.value.started_at)
    const end = new Date(task.value.completed_at)
    const durationMs = end - start
    return formatDuration(durationMs)
  }
  
  return '-'
})

/**
 * 计算平均置信度
 */
const computedAvgConfidence = computed(() => {
  if (!task.value) return null
  
  // 如果有 avg_confidence 字段直接使用
  if (task.value.avg_confidence !== null && task.value.avg_confidence !== undefined) {
    return task.value.avg_confidence
  }
  
  // 否则从 confidence_scores 计算
  if (task.value.confidence_scores && Object.keys(task.value.confidence_scores).length > 0) {
    const scores = Object.values(task.value.confidence_scores)
    const sum = scores.reduce((a, b) => a + b, 0)
    return sum / scores.length
  }
  
  return null
})

/**
 * 计算状态时间线
 */
const statusTimeline = computed(() => {
  if (!task.value) return []

  const timeline = []
  const t = task.value

  // 创建时间（排队）
  if (t.created_at) {
    timeline.push({
      status: TASK_STATUS.QUEUED,
      timestamp: t.created_at
    })
  }

  // 开始处理
  if (t.started_at) {
    timeline.push({
      status: TASK_STATUS.PROCESSING,
      timestamp: t.started_at,
      duration: t.created_at ? new Date(t.started_at) - new Date(t.created_at) : null
    })
  }

  // 待审核
  if (t.status === TASK_STATUS.PENDING_AUDIT || t.audited_at) {
    const pendingTime = t.audited_at || (t.status === TASK_STATUS.PENDING_AUDIT ? new Date() : null)
    if (pendingTime) {
      timeline.push({
        status: TASK_STATUS.PENDING_AUDIT,
        timestamp: pendingTime,
        duration: t.started_at ? new Date(pendingTime) - new Date(t.started_at) : null
      })
    }
  }

  // 完成/驳回
  if (t.completed_at) {
    const completedStatus = t.status === TASK_STATUS.REJECTED ? TASK_STATUS.REJECTED : TASK_STATUS.COMPLETED
    const prevTime = t.audited_at || t.started_at || t.created_at
    timeline.push({
      status: completedStatus,
      timestamp: t.completed_at,
      duration: prevTime ? new Date(t.completed_at) - new Date(prevTime) : null
    })
  }

  // 推送状态
  if ([TASK_STATUS.PUSHING, TASK_STATUS.PUSH_SUCCESS, TASK_STATUS.PUSH_FAILED].includes(t.status)) {
    timeline.push({
      status: t.status,
      timestamp: new Date()
    })
  }

  return timeline
})

/**
 * 加载任务详情
 */
async function loadTaskDetail() {
  if (!props.taskId) return

  loading.value = true
  try {
    const response = await taskAPI.get(props.taskId)
    // API 直接返回任务对象，不需要访问 response.data
    if (response && response.id) {
      task.value = response
    } else {
      task.value = null
      message.warning('未找到任务详情')
    }
  } catch (error) {
    message.error('加载任务详情失败：' + (error.message || '未知错误'))
    task.value = null
  } finally {
    loading.value = false
  }
}

/**
 * 格式化值（处理对象和数组）
 */
function formatValue(value) {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}

/**
 * 判断是否为复杂值（对象或数组）
 */
function isComplexValue(value) {
  return value !== null && typeof value === 'object'
}

/**
 * 获取值的样式类
 */
function getValueClass(value) {
  if (value === null || value === undefined || value === '') return 'empty'
  if (typeof value === 'boolean') return 'boolean'
  if (typeof value === 'number') return 'number'
  if (isComplexValue(value)) return 'complex'
  if (String(value).length > 100) return 'long-text'
  return 'text'
}

/**
 * 格式化数字值
 */
function formatNumberValue(value) {
  if (Number.isInteger(value)) {
    return value.toLocaleString()
  }
  return value.toLocaleString(undefined, { maximumFractionDigits: 4 })
}

/**
 * 复制提取的全部数据
 */
function copyExtractedData() {
  if (!originalExtractedData.value) return
  const text = JSON.stringify(originalExtractedData.value, null, 2)
  navigator.clipboard.writeText(text).then(() => {
    message.success('已复制全部提取数据')
  }).catch(() => {
    message.error('复制失败')
  })
}

/**
 * 复制单个字段值
 */
function copyFieldValue(key, value) {
  let text
  if (typeof value === 'object') {
    text = JSON.stringify(value, null, 2)
  } else {
    text = String(value ?? '')
  }
  navigator.clipboard.writeText(text).then(() => {
    message.success(`已复制 ${key}`)
  }).catch(() => {
    message.error('复制失败')
  })
}

/**
 * 格式化审核原因
 */
function formatAuditReason(reason) {
  if (!reason) return '-'
  // 如果是字符串直接返回
  if (typeof reason === 'string') return reason
  // 如果是对象，尝试获取常见字段
  if (typeof reason === 'object') {
    // 优先显示 reason、message、description 等字段
    return reason.reason || reason.message || reason.description || reason.field || JSON.stringify(reason)
  }
  return String(reason)
}

/**
 * 格式化JSON
 */
function formatJSON(json) {
  if (!json) return '-'
  if (typeof json === 'string') {
    try {
      return JSON.stringify(JSON.parse(json), null, 2)
    } catch {
      return json
    }
  }
  return JSON.stringify(json, null, 2)
}

/**
 * 获取推送日志标题
 */
function getPushLogHeader(log) {
  const statusText = log.http_status >= 200 && log.http_status < 300 ? '成功' : '失败'
  return `${log.webhook_name} - ${statusText} (${log.http_status})`
}

/**
 * 获取管道执行标题
 */
function getPipelineExecHeader(exec) {
  const statusLabels = {
    pending: '等待中',
    running: '执行中',
    success: '成功',
    failed: '失败'
  }
  const statusText = statusLabels[exec.status] || exec.status
  const duration = exec.duration_ms ? ` - ${exec.duration_ms}ms` : ''
  return `${exec.pipeline_name || '管道'} - ${statusText}${duration}`
}

/**
 * 获取管道状态颜色
 */
function getPipelineStatusColor(status) {
  const colorMap = {
    pending: 'default',
    running: 'processing',
    success: 'success',
    failed: 'error'
  }
  return colorMap[status] || 'default'
}

/**
 * 获取管道状态标签
 */
function getPipelineStatusLabel(status) {
  const labelMap = {
    pending: '等待中',
    running: '执行中',
    success: '成功',
    failed: '失败'
  }
  return labelMap[status] || status
}

/**
 * 获取流程步骤样式类
 */
function getFlowStepClass(status) {
  if (!status) return 'pending'
  const classMap = {
    pending: 'pending',
    processing: 'processing',
    running: 'processing',
    completed: 'success',
    success: 'success',
    failed: 'failed',
    skipped: 'skipped',
    pushing: 'processing'
  }
  return classMap[status] || 'pending'
}

/**
 * 获取流程状态标签
 */
function getFlowStatusLabel(status) {
  if (!status) return '等待中'
  const labelMap = {
    pending: '等待中',
    processing: '处理中',
    running: '执行中',
    completed: '已完成',
    success: '成功',
    failed: '失败',
    skipped: '跳过',
    pushing: '推送中'
  }
  return labelMap[status] || status
}

/**
 * 获取时间线颜色
 */
function getTimelineColor(status) {
  const colorMap = {
    [TASK_STATUS.QUEUED]: 'gray',
    [TASK_STATUS.PROCESSING]: 'blue',
    [TASK_STATUS.PENDING_AUDIT]: 'orange',
    [TASK_STATUS.COMPLETED]: 'green',
    [TASK_STATUS.REJECTED]: 'red',
    [TASK_STATUS.PUSHING]: 'blue',
    [TASK_STATUS.PUSH_SUCCESS]: 'green',
    [TASK_STATUS.PUSH_FAILED]: 'red'
  }
  return colorMap[status] || 'gray'
}

/**
 * 关闭对话框
 */
function handleClose() {
  visible.value = false
  task.value = null
  activeTab.value = 'ocr'
  activePushLog.value = []
  activePipelineExec.value = []
}

// 监听taskId变化，加载详情
watch(() => props.taskId, (newVal) => {
  if (newVal && props.visible) {
    loadTaskDetail()
  }
}, { immediate: true })

// 监听visible变化
watch(() => props.visible, (newVal) => {
  if (newVal && props.taskId) {
    loadTaskDetail()
  }
})
</script>

<style scoped>
.task-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.ocr-text-container {
  max-height: 400px;
  overflow-y: auto;
  padding: 16px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.extracted-data-container {
  max-height: 500px;
  overflow-y: auto;
  padding: 8px;
}

.extracted-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.extracted-field-item {
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  overflow: hidden;
  background: #fff;
}

.field-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
}

.field-key {
  font-weight: 600;
  color: #333;
  font-size: 13px;
}

.field-actions {
  display: flex;
  align-items: center;
}

.field-value {
  padding: 10px 12px;
  font-size: 14px;
  word-break: break-word;
}

.field-value.complex {
  padding: 0;
}

.json-value {
  margin: 0;
  padding: 12px;
  background: #f6f8fa;
  font-size: 12px;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  color: #24292e;
  max-height: 200px;
  overflow-y: auto;
}

.number-value {
  color: #1890ff;
  font-weight: 500;
  font-family: 'SFMono-Regular', Consolas, monospace;
}

.empty-value {
  color: #bfbfbf;
  font-style: italic;
}

.text-value {
  color: #333;
}

.long-text-value {
  margin: 0;
  color: #333;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 600;
  background-color: #fafafa;
}

:deep(.ant-collapse-header) {
  font-weight: 500;
}

:deep(.ant-typography-expand) {
  color: #1890ff;
}

/* 流程概览样式 */
.flow-overview {
  margin-bottom: 16px;
}

.flow-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px 0;
}

.flow-step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 100px;
}

.flow-step-item .step-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  margin-bottom: 8px;
}

.flow-step-item.pending .step-icon {
  background-color: #f5f5f5;
  color: #999;
  border: 2px solid #d9d9d9;
}

.flow-step-item.processing .step-icon {
  background-color: #e6f7ff;
  color: #1890ff;
  border: 2px solid #1890ff;
}

.flow-step-item.success .step-icon {
  background-color: #f6ffed;
  color: #52c41a;
  border: 2px solid #52c41a;
}

.flow-step-item.failed .step-icon {
  background-color: #fff2f0;
  color: #ff4d4f;
  border: 2px solid #ff4d4f;
}

.flow-step-item.skipped .step-icon {
  background-color: #fafafa;
  color: #bfbfbf;
  border: 2px dashed #d9d9d9;
}

.flow-step-item .step-label {
  font-size: 13px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.flow-step-item .step-status {
  font-size: 12px;
  color: #666;
}

.step-connector {
  width: 60px;
  height: 2px;
  background-color: #d9d9d9;
  margin: 0 8px;
  margin-bottom: 40px;
}

.step-connector.active {
  background-color: #52c41a;
}
</style>
