<template>
  <div class="webhook-config-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">Webhook配置</h2>
        <p class="page-description">管理下游业务系统的回调接口配置</p>
      </div>
      <div class="header-right">
        <a-button type="primary" @click="handleCreate">
          <template #icon><PlusOutlined /></template>
          新建Webhook
        </a-button>
      </div>
    </div>

    <!-- Webhook列表 -->
    <div class="webhook-list">
      <a-table
        :columns="columns"
        :data-source="webhookList"
        :loading="loading"
        :pagination="false"
        row-key="id"
      >
        <!-- 系统名称 -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <div class="webhook-name">
              <span class="name-text">{{ record.name }}</span>
            </div>
          </template>

          <!-- Webhook类型 -->
          <template v-else-if="column.key === 'webhook_type'">
            <a-tag :color="record.webhook_type === 'kingdee' ? 'gold' : 'blue'">
              {{ record.webhook_type === 'kingdee' ? '金蝶K3' : '标准HTTP' }}
            </a-tag>
          </template>

          <!-- Endpoint URL -->
          <template v-else-if="column.key === 'endpoint_url'">
            <div class="endpoint-url">
              <template v-if="record.webhook_type === 'kingdee'">
                <span class="url-text" style="color: #999">使用环境变量配置</span>
              </template>
              <template v-else>
                <a-tooltip :title="record.endpoint_url">
                  <span class="url-text">{{ record.endpoint_url }}</span>
                </a-tooltip>
              </template>
            </div>
          </template>

          <!-- 鉴权方式 -->
          <template v-else-if="column.key === 'auth_type'">
            <template v-if="record.webhook_type === 'kingdee'">
              <a-tag color="gold">Session认证</a-tag>
            </template>
            <template v-else>
              <a-tag :color="getAuthTypeColor(record.auth_type)">
                {{ getAuthTypeLabel(record.auth_type) }}
              </a-tag>
            </template>
          </template>

          <!-- 状态 -->
          <template v-else-if="column.key === 'is_active'">
            <a-badge
              :status="record.is_active ? 'success' : 'default'"
              :text="record.is_active ? '启用' : '禁用'"
            />
          </template>

          <!-- 操作 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button
                type="link"
                size="small"
                :loading="testingId === record.id"
                @click="handleTest(record)"
              >
                测试
              </a-button>
              <a-button type="link" size="small" @click="handleEdit(record)">
                编辑
              </a-button>
              <a-popconfirm
                title="确定要删除此Webhook吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="handleDelete(record.id)"
              >
                <a-button type="link" size="small" danger>
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>

    <!-- Webhook编辑对话框 -->
    <WebhookDialog
      v-model:visible="dialogVisible"
      :webhook="currentWebhook"
      @success="handleDialogSuccess"
    />

    <!-- 测试结果对话框 -->
    <a-modal
      v-model:open="testResultVisible"
      title="连通性测试结果"
      :width="800"
      :footer="null"
    >
      <div v-if="testResult" class="test-result">
        <!-- 测试状态 -->
        <div class="result-section">
          <h4>测试结果</h4>
          <a-tag :color="testResult.success ? 'success' : 'error'" style="font-size: 14px; padding: 4px 12px">
            {{ testResult.success ? '连接成功' : '连接失败' }}
          </a-tag>
        </div>

        <!-- 错误信息 -->
        <div v-if="testResult.error" class="result-section">
          <h4>错误信息</h4>
          <a-alert :message="testResult.error" type="error" show-icon />
        </div>

        <!-- HTTP状态码 -->
        <div v-if="testResult.status" class="result-section">
          <h4>HTTP状态码</h4>
          <a-tag
            :color="testResult.status >= 200 && testResult.status < 300 ? 'success' : 'error'"
            style="font-size: 16px; padding: 4px 12px"
          >
            {{ testResult.status }}
          </a-tag>
        </div>

        <!-- 响应头 -->
        <div v-if="testResult.response_headers" class="result-section">
          <h4>响应头</h4>
          <pre class="code-block">{{ formatJSON(testResult.response_headers) }}</pre>
        </div>

        <!-- 响应体 -->
        <div v-if="testResult.response_body" class="result-section">
          <h4>响应体</h4>
          <pre class="code-block">{{ formatResponseBody(testResult.response_body) }}</pre>
        </div>

        <!-- 耗时 -->
        <div class="result-section">
          <h4>耗时</h4>
          <span>{{ testResult.duration_ms }} ms</span>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import WebhookDialog from '@/components/Webhook/WebhookDialog.vue'
import {
  getWebhookList,
  getWebhookDetail,
  createWebhook,
  updateWebhook,
  deleteWebhook,
  testWebhook
} from '@/api/webhook'

// 数据状态
const loading = ref(false)
const webhookList = ref([])
const dialogVisible = ref(false)
const currentWebhook = ref(null)
const testResultVisible = ref(false)
const testResult = ref(null)
const testingId = ref(null)

// 表格列定义
const columns = [
  {
    title: '系统名称',
    dataIndex: 'name',
    key: 'name',
    width: 200
  },
  {
    title: '类型',
    dataIndex: 'webhook_type',
    key: 'webhook_type',
    width: 120
  },
  {
    title: 'Endpoint URL',
    dataIndex: 'endpoint_url',
    key: 'endpoint_url',
    ellipsis: true
  },
  {
    title: '鉴权方式',
    dataIndex: 'auth_type',
    key: 'auth_type',
    width: 120
  },
  {
    title: '状态',
    dataIndex: 'is_active',
    key: 'is_active',
    width: 100
  },
  {
    title: '操作',
    key: 'action',
    width: 200,
    fixed: 'right'
  }
]

/**
 * 加载Webhook列表
 */
async function loadWebhookList() {
  try {
    loading.value = true
    const response = await getWebhookList()
    // API 返回 { items: [...], total: ... } 结构
    webhookList.value = response.items || response.data?.items || []
  } catch (error) {
    console.error('加载Webhook列表失败:', error)
    message.error('加载Webhook列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 新建Webhook
 */
function handleCreate() {
  currentWebhook.value = null
  dialogVisible.value = true
}

/**
 * 编辑Webhook
 */
async function handleEdit(webhook) {
  try {
    // 获取 Webhook 详情（包含 rule_ids）
    const response = await getWebhookDetail(webhook.id)
    currentWebhook.value = response.data || response
    dialogVisible.value = true
  } catch (error) {
    console.error('获取Webhook详情失败:', error)
    // 降级使用列表数据
    currentWebhook.value = { ...webhook, rule_ids: [] }
    dialogVisible.value = true
  }
}

/**
 * 删除Webhook
 */
async function handleDelete(webhookId) {
  try {
    await deleteWebhook(webhookId)
    message.success('删除成功')
    loadWebhookList()
  } catch (error) {
    console.error('删除Webhook失败:', error)
    message.error(error.response?.data?.message || '删除失败')
  }
}

/**
 * 测试Webhook连通性
 */
async function handleTest(webhook) {
  try {
    testingId.value = webhook.id
    const response = await testWebhook(webhook.id)
    // API 可能直接返回结果或在 data 中
    const result = response.data || response
    // 统一字段名（API 返回 status_code，前端使用 status）
    testResult.value = {
      ...result,
      status: result.status_code || result.status
    }
    testResultVisible.value = true
    
    // 根据状态码显示提示
    const statusCode = testResult.value.status
    if (statusCode >= 200 && statusCode < 300) {
      message.success('连通性测试成功')
    } else {
      message.warning(`连通性测试返回状态码: ${statusCode}`)
    }
  } catch (error) {
    console.error('测试Webhook失败:', error)
    message.error(error.response?.data?.message || '测试失败')
  } finally {
    testingId.value = null
  }
}

/**
 * 对话框提交成功
 */
async function handleDialogSuccess(formData) {
  try {
    if (currentWebhook.value) {
      // 编辑
      await updateWebhook(currentWebhook.value.id, formData)
      message.success('更新成功')
    } else {
      // 新建
      await createWebhook(formData)
      message.success('创建成功')
    }
    
    dialogVisible.value = false
    loadWebhookList()
  } catch (error) {
    console.error('保存Webhook失败:', error)
    message.error(error.response?.data?.message || '保存失败')
  }
}

/**
 * 获取鉴权方式标签
 */
function getAuthTypeLabel(authType) {
  const labels = {
    none: '无鉴权',
    basic: 'Basic Auth',
    bearer: 'Bearer Token',
    api_key: 'API Key'
  }
  return labels[authType] || authType
}

/**
 * 获取鉴权方式颜色
 */
function getAuthTypeColor(authType) {
  const colors = {
    none: 'default',
    basic: 'blue',
    bearer: 'green',
    api_key: 'purple'
  }
  return colors[authType] || 'default'
}

/**
 * 格式化JSON
 */
function formatJSON(obj) {
  try {
    return JSON.stringify(obj, null, 2)
  } catch (e) {
    return String(obj)
  }
}

/**
 * 格式化响应体
 */
function formatResponseBody(body) {
  if (typeof body === 'string') {
    try {
      return JSON.stringify(JSON.parse(body), null, 2)
    } catch (e) {
      return body
    }
  }
  return formatJSON(body)
}

// 组件挂载时加载数据
onMounted(() => {
  loadWebhookList()
})
</script>

<style scoped>
.webhook-config-page {
  padding: 24px;
  background-color: #fff;
  min-height: calc(100vh - 64px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.header-left {
  flex: 1;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #262626;
}

.page-description {
  margin: 8px 0 0;
  font-size: 14px;
  color: #8c8c8c;
}

.header-right {
  display: flex;
  gap: 12px;
}

.webhook-list {
  margin-top: 16px;
}

.webhook-name {
  display: flex;
  align-items: center;
}

.name-text {
  font-weight: 500;
  color: #262626;
}

.endpoint-url {
  max-width: 400px;
}

.url-text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #1890ff;
}

.test-result {
  padding: 16px 0;
}

.result-section {
  margin-bottom: 24px;
}

.result-section h4 {
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

.code-block {
  padding: 12px;
  background-color: #f5f5f5;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
  max-height: 300px;
  overflow-y: auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .webhook-config-page {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .header-right {
    width: 100%;
  }

  .header-right .ant-btn {
    width: 100%;
  }
}
</style>
