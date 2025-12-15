<template>
  <div class="audit-logs">
    <!-- 筛选区域 -->
    <a-card :bordered="false" class="mb-4">
      <a-form layout="inline" :model="filters">
        <a-form-item label="时间范围">
          <a-range-picker
            v-model:value="dateRange"
            :format="dateFormat"
            :placeholder="['开始日期', '结束日期']"
            style="width: 280px"
            @change="handleDateChange"
          />
        </a-form-item>

        <a-form-item label="操作类型">
          <a-select
            v-model:value="filters.action_type"
            placeholder="全部"
            style="width: 150px"
            allow-clear
            @change="handleSearch"
          >
            <a-select-option value="">全部</a-select-option>
            <a-select-option value="login">登录</a-select-option>
            <a-select-option value="logout">登出</a-select-option>
            <a-select-option value="create">创建</a-select-option>
            <a-select-option value="update">更新</a-select-option>
            <a-select-option value="delete">删除</a-select-option>
            <a-select-option value="publish">发布</a-select-option>
            <a-select-option value="audit">审核</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="资源类型">
          <a-select
            v-model:value="filters.resource_type"
            placeholder="全部"
            style="width: 150px"
            allow-clear
            @change="handleSearch"
          >
            <a-select-option value="">全部</a-select-option>
            <a-select-option value="user">用户</a-select-option>
            <a-select-option value="rule">规则</a-select-option>
            <a-select-option value="task">任务</a-select-option>
            <a-select-option value="webhook">Webhook</a-select-option>
            <a-select-option value="system">系统配置</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="用户">
          <a-input
            v-model:value="filters.user_id"
            placeholder="用户ID或用户名"
            style="width: 180px"
            allow-clear
            @pressEnter="handleSearch"
          />
        </a-form-item>

        <a-form-item>
          <a-space>
            <a-button type="primary" @click="handleSearch">
              <SearchOutlined />
              查询
            </a-button>
            <a-button @click="handleReset">
              <ReloadOutlined />
              重置
            </a-button>
            <a-button @click="handleExport" :loading="exporting">
              <DownloadOutlined />
              导出
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 日志列表 -->
    <a-card :bordered="false">
      <a-table
        :columns="columns"
        :data-source="logs"
        :loading="loading"
        :pagination="pagination"
        :scroll="{ x: 1200 }"
        @change="handleTableChange"
        row-key="id"
      >
        <!-- 操作类型 -->
        <template #action_type="{ record }">
          <a-tag :color="getActionTypeColor(record.action_type)">
            {{ getActionTypeText(record.action_type) }}
          </a-tag>
        </template>

        <!-- 资源类型 -->
        <template #resource_type="{ record }">
          <a-tag>{{ getResourceTypeText(record.resource_type) }}</a-tag>
        </template>

        <!-- 用户信息 -->
        <template #user="{ record }">
          <div>
            <div class="font-medium">{{ record.username || record.user_id }}</div>
            <div class="text-xs text-gray-400">{{ record.user_id }}</div>
          </div>
        </template>

        <!-- 变更内容 -->
        <template #changes="{ record }">
          <a-button 
            v-if="record.changes" 
            type="link" 
            size="small"
            @click="showChangesDetail(record)"
          >
            查看详情
          </a-button>
          <span v-else class="text-gray-400">-</span>
        </template>

        <!-- IP地址 -->
        <template #ip_address="{ record }">
          <span class="font-mono text-sm">{{ record.ip_address || '-' }}</span>
        </template>

        <!-- 时间 -->
        <template #created_at="{ record }">
          <div class="text-sm">
            {{ formatDateTime(record.created_at) }}
          </div>
        </template>
      </a-table>
    </a-card>

    <!-- 变更详情对话框 -->
    <a-modal
      v-model:open="detailVisible"
      title="变更详情"
      width="800px"
      :footer="null"
    >
      <a-descriptions :column="1" bordered size="small" class="mb-4">
        <a-descriptions-item label="操作人">
          {{ currentLog?.username || currentLog?.user_id }}
        </a-descriptions-item>
        <a-descriptions-item label="操作类型">
          <a-tag :color="getActionTypeColor(currentLog?.action_type)">
            {{ getActionTypeText(currentLog?.action_type) }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="资源类型">
          {{ getResourceTypeText(currentLog?.resource_type) }}
        </a-descriptions-item>
        <a-descriptions-item label="资源ID">
          {{ currentLog?.resource_id || '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="IP地址">
          {{ currentLog?.ip_address || '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="User Agent">
          <div class="text-xs break-all">
            {{ currentLog?.user_agent || '-' }}
          </div>
        </a-descriptions-item>
        <a-descriptions-item label="操作时间">
          {{ formatDateTime(currentLog?.created_at) }}
        </a-descriptions-item>
      </a-descriptions>

      <a-divider>变更内容</a-divider>
      
      <div class="bg-gray-50 p-4 rounded max-h-96 overflow-auto">
        <pre class="text-xs">{{ formatJSON(currentLog?.changes) }}</pre>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { 
  SearchOutlined, 
  ReloadOutlined, 
  DownloadOutlined 
} from '@ant-design/icons-vue'
import { auditLogAPI } from '@/api'
import dayjs from 'dayjs'

/**
 * 日期格式
 */
const dateFormat = 'YYYY-MM-DD'

/**
 * 加载状态
 */
const loading = ref(false)

/**
 * 导出状态
 */
const exporting = ref(false)

/**
 * 日期范围
 */
const dateRange = ref([])

/**
 * 筛选条件
 */
const filters = reactive({
  action_type: '',
  resource_type: '',
  user_id: '',
  start_date: '',
  end_date: ''
})

/**
 * 审计日志列表
 */
const logs = ref([])

/**
 * 分页配置
 */
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total) => `共 ${total} 条记录`
})

/**
 * 详情对话框可见性
 */
const detailVisible = ref(false)

/**
 * 当前查看的日志
 */
const currentLog = ref(null)

/**
 * 表格列配置
 */
const columns = [
  {
    title: '操作类型',
    dataIndex: 'action_type',
    key: 'action_type',
    width: 100,
    slots: { customRender: 'action_type' }
  },
  {
    title: '资源类型',
    dataIndex: 'resource_type',
    key: 'resource_type',
    width: 100,
    slots: { customRender: 'resource_type' }
  },
  {
    title: '资源ID',
    dataIndex: 'resource_id',
    key: 'resource_id',
    width: 150,
    ellipsis: true
  },
  {
    title: '操作人',
    key: 'user',
    width: 150,
    slots: { customRender: 'user' }
  },
  {
    title: 'IP地址',
    dataIndex: 'ip_address',
    key: 'ip_address',
    width: 140,
    slots: { customRender: 'ip_address' }
  },
  {
    title: '变更内容',
    key: 'changes',
    width: 100,
    slots: { customRender: 'changes' }
  },
  {
    title: '操作时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 160,
    slots: { customRender: 'created_at' }
  }
]

/**
 * 获取操作类型颜色
 */
function getActionTypeColor(type) {
  const colorMap = {
    login: 'green',
    logout: 'default',
    create: 'blue',
    update: 'orange',
    delete: 'red',
    publish: 'purple',
    audit: 'cyan'
  }
  return colorMap[type] || 'default'
}

/**
 * 获取操作类型文本
 */
function getActionTypeText(type) {
  const textMap = {
    login: '登录',
    logout: '登出',
    create: '创建',
    update: '更新',
    delete: '删除',
    publish: '发布',
    audit: '审核'
  }
  return textMap[type] || type
}

/**
 * 获取资源类型文本
 */
function getResourceTypeText(type) {
  const textMap = {
    user: '用户',
    rule: '规则',
    task: '任务',
    webhook: 'Webhook',
    system: '系统配置'
  }
  return textMap[type] || type
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateTime) {
  if (!dateTime) return '-'
  return dayjs(dateTime).format('YYYY-MM-DD HH:mm:ss')
}

/**
 * 格式化JSON
 */
function formatJSON(obj) {
  if (!obj) return '-'
  return JSON.stringify(obj, null, 2)
}

/**
 * 处理日期范围变化
 */
function handleDateChange(dates) {
  if (dates && dates.length === 2) {
    filters.start_date = dates[0].format(dateFormat)
    filters.end_date = dates[1].format(dateFormat)
  } else {
    filters.start_date = ''
    filters.end_date = ''
  }
}

/**
 * 加载审计日志
 */
async function loadLogs() {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      ...filters
    }
    
    // 移除空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })
    
    const response = await auditLogAPI.list(params)
    
    if (response.data) {
      logs.value = response.data.items || []
      pagination.total = response.data.total || 0
    }
  } catch (error) {
    console.error('加载审计日志失败:', error)
    message.error('加载审计日志失败')
  } finally {
    loading.value = false
  }
}

/**
 * 处理搜索
 */
function handleSearch() {
  pagination.current = 1
  loadLogs()
}

/**
 * 处理重置
 */
function handleReset() {
  dateRange.value = []
  filters.action_type = ''
  filters.resource_type = ''
  filters.user_id = ''
  filters.start_date = ''
  filters.end_date = ''
  pagination.current = 1
  loadLogs()
}

/**
 * 处理表格变化
 */
function handleTableChange(pag) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadLogs()
}

/**
 * 显示变更详情
 */
function showChangesDetail(log) {
  currentLog.value = log
  detailVisible.value = true
}

/**
 * 导出审计日志
 */
async function handleExport() {
  exporting.value = true
  try {
    const params = { ...filters }
    
    // 移除空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })
    
    const response = await auditLogAPI.export(params)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `audit_logs_${dayjs().format('YYYYMMDDHHmmss')}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    message.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    message.error('导出失败')
  } finally {
    exporting.value = false
  }
}

/**
 * 组件挂载时加载数据
 */
onMounted(() => {
  // 默认显示最近7天的日志
  const endDate = dayjs()
  const startDate = endDate.subtract(7, 'day')
  dateRange.value = [startDate, endDate]
  filters.start_date = startDate.format(dateFormat)
  filters.end_date = endDate.format(dateFormat)
  
  loadLogs()
})
</script>

<style scoped>
.audit-logs {
  /* 样式 */
}

:deep(.ant-table-cell) {
  padding: 12px 8px;
}

pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
