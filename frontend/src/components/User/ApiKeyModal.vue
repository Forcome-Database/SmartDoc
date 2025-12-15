<template>
  <a-modal
    v-model:open="visible"
    title="API密钥管理"
    width="700px"
    :footer="null"
    @cancel="handleClose"
  >
    <!-- 创建新密钥区域 -->
    <div class="create-section">
      <a-button type="primary" @click="showCreateForm = true" v-if="!showCreateForm">
        <PlusOutlined />
        生成新密钥
      </a-button>
      
      <div v-if="showCreateForm" class="create-form">
        <a-form layout="inline">
          <a-form-item label="有效期">
            <a-select v-model:value="createForm.expires_days" style="width: 150px">
              <a-select-option :value="30">30天</a-select-option>
              <a-select-option :value="90">90天</a-select-option>
              <a-select-option :value="180">180天</a-select-option>
              <a-select-option :value="365">1年</a-select-option>
              <a-select-option :value="0">永不过期</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item>
            <a-space>
              <a-button type="primary" @click="handleCreate" :loading="creating">
                确认生成
              </a-button>
              <a-button @click="showCreateForm = false">取消</a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </div>
    </div>

    <!-- 新生成的密钥展示（仅显示一次） -->
    <a-alert
      v-if="newlyCreatedKey"
      type="success"
      class="new-key-alert"
      closable
      @close="newlyCreatedKey = null"
    >
      <template #message>
        <div class="new-key-content">
          <div class="new-key-title">
            <CheckCircleOutlined /> 密钥生成成功！请立即复制保存，此密钥仅显示一次。
          </div>
          <div class="new-key-info">
            <div class="key-row">
              <span class="key-label">Key ID:</span>
              <code class="key-value">{{ newlyCreatedKey.key_id }}</code>
              <a-button size="small" @click="copyToClipboard(newlyCreatedKey.key_id)">
                <CopyOutlined />
              </a-button>
            </div>
            <div class="key-row">
              <span class="key-label">Secret:</span>
              <code class="key-value secret">{{ newlyCreatedKey.secret }}</code>
              <a-button size="small" @click="copyToClipboard(newlyCreatedKey.secret)">
                <CopyOutlined />
              </a-button>
            </div>
          </div>
        </div>
      </template>
    </a-alert>

    <!-- 密钥列表 -->
    <a-table
      :columns="columns"
      :data-source="apiKeys"
      :loading="loading"
      :pagination="false"
      row-key="id"
      size="small"
      class="key-table"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'key_id'">
          <code class="key-id-cell">{{ record.key_id }}</code>
        </template>
        <template v-else-if="column.key === 'expires_at'">
          <span :class="{ 'text-danger': isExpired(record.expires_at) }">
            {{ record.expires_at ? formatDate(record.expires_at) : '永不过期' }}
          </span>
        </template>
        <template v-else-if="column.key === 'is_active'">
          <a-tag :color="record.is_active ? 'green' : 'red'">
            {{ record.is_active ? '有效' : '已撤销' }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'last_used_at'">
          {{ record.last_used_at ? formatDate(record.last_used_at) : '从未使用' }}
        </template>
        <template v-else-if="column.key === 'action'">
          <a-popconfirm
            title="确定要撤销此密钥吗？撤销后将无法恢复。"
            @confirm="handleRevoke(record.id)"
            :disabled="!record.is_active"
          >
            <a-button 
              type="link" 
              danger 
              size="small"
              :disabled="!record.is_active"
            >
              撤销
            </a-button>
          </a-popconfirm>
        </template>
      </template>
    </a-table>

    <!-- 使用说明 -->
    <a-collapse class="usage-guide" ghost>
      <a-collapse-panel key="1" header="API使用说明">
        <div class="guide-content">
          <p><strong>方式一：使用独立的Header（推荐）</strong></p>
          <code class="code-block">
            X-API-Key: {key_id}<br>
            X-API-Secret: {secret}
          </code>
          <p><strong>方式二：使用Bearer Token格式</strong></p>
          <code class="code-block">
            Authorization: Bearer {key_id}:{secret}
          </code>
          <p class="guide-note">注意：key_id和secret之间用英文冒号(:)连接</p>
        </div>
      </a-collapse-panel>
    </a-collapse>
  </a-modal>
</template>

<script setup>
/**
 * API密钥管理弹窗组件
 * 支持查看、创建、撤销API密钥
 */
import { ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  CopyOutlined,
  CheckCircleOutlined
} from '@ant-design/icons-vue'
import { userAPI } from '@/api'

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:open'])

// 弹窗可见性
const visible = ref(false)

// 密钥列表
const apiKeys = ref([])
const loading = ref(false)

// 创建表单
const showCreateForm = ref(false)
const creating = ref(false)
const createForm = ref({
  expires_days: 90
})

// 新创建的密钥（仅显示一次）
const newlyCreatedKey = ref(null)

// 表格列配置
const columns = [
  {
    title: 'Key ID',
    key: 'key_id',
    width: 200
  },
  {
    title: '过期时间',
    key: 'expires_at',
    width: 150
  },
  {
    title: '状态',
    key: 'is_active',
    width: 80
  },
  {
    title: '最后使用',
    key: 'last_used_at',
    width: 150
  },
  {
    title: '操作',
    key: 'action',
    width: 80
  }
]

// 监听open属性
watch(() => props.open, (val) => {
  visible.value = val
  if (val) {
    fetchApiKeys()
  }
})

// 监听visible变化同步到父组件
watch(visible, (val) => {
  emit('update:open', val)
})

/**
 * 获取API密钥列表
 */
async function fetchApiKeys() {
  loading.value = true
  try {
    const res = await userAPI.getApiKeys()
    apiKeys.value = res.items || []
  } catch (error) {
    console.error('获取API密钥列表失败:', error)
    message.error('获取API密钥列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 创建新密钥
 */
async function handleCreate() {
  creating.value = true
  try {
    const res = await userAPI.createApiKey(createForm.value)
    newlyCreatedKey.value = res
    showCreateForm.value = false
    createForm.value = { expires_days: 90 }
    message.success('API密钥生成成功')
    fetchApiKeys()
  } catch (error) {
    console.error('创建API密钥失败:', error)
    message.error('创建API密钥失败')
  } finally {
    creating.value = false
  }
}

/**
 * 撤销密钥
 */
async function handleRevoke(keyId) {
  try {
    await userAPI.revokeApiKey(keyId)
    message.success('API密钥已撤销')
    fetchApiKeys()
  } catch (error) {
    console.error('撤销API密钥失败:', error)
    message.error('撤销API密钥失败')
  }
}

/**
 * 关闭弹窗
 */
function handleClose() {
  visible.value = false
  newlyCreatedKey.value = null
  showCreateForm.value = false
}

/**
 * 复制到剪贴板
 */
async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text)
    message.success('已复制到剪贴板')
  } catch {
    message.error('复制失败，请手动复制')
  }
}

/**
 * 格式化日期
 */
function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 检查是否已过期
 */
function isExpired(dateStr) {
  if (!dateStr) return false
  return new Date(dateStr) < new Date()
}
</script>

<style scoped>
.create-section {
  margin-bottom: 16px;
}

.create-form {
  padding: 12px;
  background: #fafafa;
  border-radius: 4px;
}

.new-key-alert {
  margin-bottom: 16px;
}

.new-key-content {
  padding: 8px 0;
}

.new-key-title {
  font-weight: 500;
  margin-bottom: 12px;
  color: #52c41a;
}

.new-key-info {
  background: #f6ffed;
  padding: 12px;
  border-radius: 4px;
}

.key-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.key-row:last-child {
  margin-bottom: 0;
}

.key-label {
  width: 60px;
  font-weight: 500;
}

.key-value {
  flex: 1;
  padding: 4px 8px;
  background: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-family: monospace;
  word-break: break-all;
}

.key-value.secret {
  color: #cf1322;
}

.key-table {
  margin-bottom: 16px;
}

.key-id-cell {
  font-family: monospace;
  font-size: 12px;
}

.text-danger {
  color: #ff4d4f;
}

.usage-guide {
  margin-top: 16px;
}

.guide-content {
  font-size: 13px;
}

.guide-content p {
  margin-bottom: 8px;
}

.code-block {
  display: block;
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 4px;
  font-family: monospace;
  margin-bottom: 12px;
}

.guide-note {
  color: #faad14;
  font-size: 12px;
  margin-top: 8px;
}
</style>
