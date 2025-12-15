<template>
  <div class="document-upload-page p-6">
    <!-- 页面标题 -->
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">文档上传</h1>
    </div>

    <!-- 上传配置区域 -->
    <a-card class="mb-4">
      <a-form layout="inline" :model="uploadConfig">
        <a-form-item label="选择规则" required>
          <a-select
            v-model:value="uploadConfig.rule_id"
            placeholder="请选择处理规则"
            style="width: 280px"
            show-search
            :filter-option="filterRuleOption"
            :loading="loadingRules"
          >
            <a-select-option
              v-for="rule in rules"
              :key="rule.id"
              :value="rule.id"
            >
              {{ rule.name }} ({{ rule.code }})
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="规则版本">
          <a-select
            v-model:value="uploadConfig.rule_version"
            placeholder="默认使用最新版本"
            style="width: 160px"
            allow-clear
            :disabled="!uploadConfig.rule_id"
          >
            <a-select-option
              v-for="version in ruleVersions"
              :key="version"
              :value="version"
            >
              {{ version }}
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 上传区域 -->
    <a-card title="文件上传" class="mb-4">
      <template #extra>
        <a-space>
          <a-tag color="blue">支持 PDF / 图片</a-tag>
          <a-tag color="orange">单文件最大 20MB</a-tag>
          <a-tag color="green">单次最多 10 个文件</a-tag>
        </a-space>
      </template>

      <a-upload-dragger
        v-model:file-list="fileList"
        name="files"
        :multiple="true"
        :max-count="10"
        :before-upload="beforeUpload"
        :custom-request="handleCustomUpload"
        :accept="acceptTypes"
        :disabled="!uploadConfig.rule_id"
        @remove="handleRemove"
      >
        <p class="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p class="ant-upload-hint">
          支持单个或批量上传，支持 PDF、PNG、JPG、JPEG 格式
        </p>
      </a-upload-dragger>

      <!-- 上传按钮 -->
      <div class="mt-4 flex justify-center">
        <a-space>
          <a-button
            type="primary"
            size="large"
            :loading="uploading"
            :disabled="pendingFiles.length === 0 || !uploadConfig.rule_id"
            @click="handleBatchUpload"
          >
            <template #icon><CloudUploadOutlined /></template>
            开始上传 ({{ pendingFiles.length }} 个文件)
          </a-button>
          <a-button
            size="large"
            :disabled="fileList.length === 0"
            @click="handleClearAll"
          >
            清空列表
          </a-button>
        </a-space>
      </div>
    </a-card>

    <!-- 上传结果 -->
    <a-card v-if="uploadResults.length > 0" title="上传结果" class="mb-4">
      <template #extra>
        <a-space>
          <a-tag color="green">成功: {{ successCount }}</a-tag>
          <a-tag v-if="failedCount > 0" color="red">失败: {{ failedCount }}</a-tag>
        </a-space>
      </template>

      <a-table
        :columns="resultColumns"
        :data-source="uploadResults"
        :pagination="false"
        :row-key="record => record.file_name"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
            <a-tag v-if="record.is_instant" color="cyan">秒传</a-tag>
          </template>

          <template v-else-if="column.key === 'task_id'">
            <a-button
              v-if="record.task_id"
              type="link"
              size="small"
              @click="handleViewTask(record.task_id)"
            >
              {{ record.task_id }}
            </a-button>
            <span v-else class="text-gray-400">-</span>
          </template>

          <template v-else-if="column.key === 'error'">
            <a-tooltip v-if="record.error" :title="record.error">
              <span class="text-red-500">{{ truncate(record.error, 30) }}</span>
            </a-tooltip>
            <span v-else class="text-gray-400">-</span>
          </template>

          <template v-else-if="column.key === 'wait_time'">
            <span v-if="record.estimated_wait_seconds > 0">
              约 {{ record.estimated_wait_seconds }} 秒
            </span>
            <span v-else class="text-gray-400">-</span>
          </template>
        </template>
      </a-table>

      <div class="mt-4 flex justify-center">
        <a-button type="primary" @click="handleGoToTasks">
          <template #icon><UnorderedListOutlined /></template>
          查看任务列表
        </a-button>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import {
  InboxOutlined,
  CloudUploadOutlined,
  UnorderedListOutlined
} from '@ant-design/icons-vue'
import { taskAPI } from '@/api/task'
import { ruleAPI } from '@/api/rule'

const router = useRouter()

// 支持的文件类型
const acceptTypes = '.pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg'

// 规则列表
const rules = ref([])
const ruleVersions = ref([])
const loadingRules = ref(false)

// 上传配置
const uploadConfig = reactive({
  rule_id: undefined,
  rule_version: undefined
})

// 文件列表
const fileList = ref([])
const uploading = ref(false)

// 上传结果
const uploadResults = ref([])

// 待上传文件（状态为等待中的文件）
const pendingFiles = computed(() => {
  return fileList.value.filter(f => !f.status || f.status === 'pending')
})

// 成功/失败计数
const successCount = computed(() => {
  return uploadResults.value.filter(r => r.status !== 'failed').length
})

const failedCount = computed(() => {
  return uploadResults.value.filter(r => r.status === 'failed').length
})

// 结果表格列
const resultColumns = [
  { title: '文件名', dataIndex: 'file_name', key: 'file_name', ellipsis: true },
  { title: '状态', key: 'status', width: 140 },
  { title: '任务ID', key: 'task_id', width: 200 },
  { title: '预估等待', key: 'wait_time', width: 120 },
  { title: '错误信息', key: 'error', ellipsis: true }
]

/**
 * 加载规则列表
 */
async function loadRules() {
  loadingRules.value = true
  try {
    const response = await ruleAPI.list({ page: 1, page_size: 1000 })
    if (response && response.items) {
      // 只显示有已发布版本的规则
      rules.value = response.items.filter(r => r.current_version)
    }
  } catch (error) {
    message.error('加载规则列表失败')
    console.error('Load rules error:', error)
  } finally {
    loadingRules.value = false
  }
}

/**
 * 加载规则版本
 */
async function loadRuleVersions(ruleId) {
  if (!ruleId) {
    ruleVersions.value = []
    return
  }
  
  try {
    const response = await ruleAPI.getVersions(ruleId)
    if (response && response.versions) {
      // 只显示已发布的版本
      ruleVersions.value = response.versions
        .filter(v => v.status === 'published')
        .map(v => v.version)
    }
  } catch (error) {
    console.error('Load rule versions error:', error)
    ruleVersions.value = []
  }
}

// 监听规则变化，加载版本列表
watch(() => uploadConfig.rule_id, (newVal) => {
  uploadConfig.rule_version = undefined
  loadRuleVersions(newVal)
})

/**
 * 规则选项过滤
 */
function filterRuleOption(input, option) {
  const rule = rules.value.find(r => r.id === option.value)
  if (!rule) return false
  const searchText = input.toLowerCase()
  return rule.name.toLowerCase().includes(searchText) ||
         rule.code.toLowerCase().includes(searchText)
}

/**
 * 上传前校验
 */
function beforeUpload(file) {
  // 检查文件类型
  const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg']
  if (!allowedTypes.includes(file.type)) {
    message.error(`不支持的文件类型: ${file.name}`)
    return false
  }
  
  // 检查文件大小（20MB）
  const maxSize = 20 * 1024 * 1024
  if (file.size > maxSize) {
    message.error(`文件过大: ${file.name}，最大支持 20MB`)
    return false
  }
  
  // 检查文件数量
  if (fileList.value.length >= 10) {
    message.error('单次最多上传 10 个文件')
    return false
  }
  
  // 阻止自动上传，手动控制
  return false
}

/**
 * 自定义上传（阻止默认行为）
 */
function handleCustomUpload({ file, onSuccess }) {
  // 标记为待上传状态
  file.status = 'pending'
  onSuccess()
}

/**
 * 移除文件
 */
function handleRemove(file) {
  const index = fileList.value.indexOf(file)
  if (index > -1) {
    fileList.value.splice(index, 1)
  }
}

/**
 * 清空文件列表
 */
function handleClearAll() {
  fileList.value = []
  uploadResults.value = []
}

/**
 * 批量上传
 */
async function handleBatchUpload() {
  if (pendingFiles.value.length === 0) {
    message.warning('没有待上传的文件')
    return
  }
  
  if (!uploadConfig.rule_id) {
    message.warning('请先选择处理规则')
    return
  }
  
  uploading.value = true
  uploadResults.value = []
  
  try {
    // 构建 FormData
    const formData = new FormData()
    
    pendingFiles.value.forEach(fileWrapper => {
      formData.append('files', fileWrapper.originFileObj || fileWrapper)
    })
    
    formData.append('rule_id', uploadConfig.rule_id)
    if (uploadConfig.rule_version) {
      formData.append('rule_version', uploadConfig.rule_version)
    }
    
    // 上传进度回调
    const onProgress = (progressEvent) => {
      const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
      // 更新文件状态
      pendingFiles.value.forEach(f => {
        f.percent = percent
        f.status = 'uploading'
      })
    }
    
    // 调用上传 API
    const response = await taskAPI.upload(formData, onProgress)
    
    // 处理响应
    if (response.results) {
      // 批量上传响应
      uploadResults.value = response.results
      message.success(`上传完成: ${response.success_count} 成功, ${response.failed_count} 失败`)
    } else if (response.task_id) {
      // 单文件上传响应
      uploadResults.value = [{
        file_name: pendingFiles.value[0]?.name || '未知文件',
        task_id: response.task_id,
        is_instant: response.is_instant,
        status: response.status,
        estimated_wait_seconds: response.estimated_wait_seconds
      }]
      message.success(response.message || '上传成功')
    }
    
    // 更新文件状态
    fileList.value.forEach(f => {
      const result = uploadResults.value.find(r => r.file_name === f.name)
      if (result) {
        f.status = result.status === 'failed' ? 'error' : 'done'
      }
    })
    
  } catch (error) {
    message.error('上传失败: ' + (error.message || '未知错误'))
    console.error('Upload error:', error)
  } finally {
    uploading.value = false
  }
}

/**
 * 查看任务详情
 */
function handleViewTask(taskId) {
  router.push({ name: 'TaskList', query: { taskId } })
}

/**
 * 跳转到任务列表
 */
function handleGoToTasks() {
  router.push({ name: 'TaskList' })
}

/**
 * 获取状态颜色
 */
function getStatusColor(status) {
  const colorMap = {
    queued: 'blue',
    processing: 'orange',
    completed: 'green',
    failed: 'red'
  }
  return colorMap[status] || 'default'
}

/**
 * 获取状态文本
 */
function getStatusText(status) {
  const textMap = {
    queued: '排队中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return textMap[status] || status
}

/**
 * 截断文本
 */
function truncate(text, length) {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

// 初始化
onMounted(() => {
  loadRules()
})
</script>

<style scoped>
.document-upload-page {
  background-color: #f0f2f5;
  min-height: 100vh;
}

:deep(.ant-upload-drag) {
  padding: 40px 20px;
}

:deep(.ant-upload-drag-icon) {
  margin-bottom: 16px;
}

:deep(.ant-upload-drag-icon .anticon) {
  font-size: 48px;
  color: #1677ff;
}
</style>
