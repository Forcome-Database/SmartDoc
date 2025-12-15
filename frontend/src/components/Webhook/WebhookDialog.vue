<template>
  <a-modal
    :open="visible"
    :title="isEdit ? '编辑Webhook' : '新建Webhook'"
    :width="800"
    :confirm-loading="loading"
    @ok="handleSubmit"
    @cancel="handleCancel"
  >
    <a-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 16 }"
    >
      <!-- 系统名称 -->
      <a-form-item label="系统名称" name="name">
        <a-input
          v-model:value="formData.name"
          placeholder="请输入系统名称，如：财务系统、金蝶K3"
          :maxlength="100"
        />
      </a-form-item>

      <!-- Webhook类型 -->
      <a-form-item label="Webhook类型" name="webhook_type">
        <a-radio-group v-model:value="formData.webhook_type">
          <a-radio-button value="standard">标准HTTP</a-radio-button>
          <a-radio-button value="kingdee">金蝶K3 Cloud</a-radio-button>
        </a-radio-group>
        <div class="form-item-tip">
          {{ formData.webhook_type === 'kingdee' ? '金蝶类型使用环境变量中的连接配置' : '标准HTTP推送到指定URL' }}
        </div>
      </a-form-item>

      <!-- 标准HTTP配置 -->
      <template v-if="formData.webhook_type === 'standard'">
        <!-- Endpoint URL -->
        <a-form-item label="Endpoint URL" name="endpoint_url">
          <a-input
            v-model:value="formData.endpoint_url"
            placeholder="https://api.example.com/webhook"
            :maxlength="500"
          />
        </a-form-item>

        <!-- 鉴权方式 -->
        <a-form-item label="鉴权方式" name="auth_type">
          <a-select v-model:value="formData.auth_type" placeholder="请选择鉴权方式">
            <a-select-option value="none">无鉴权</a-select-option>
            <a-select-option value="basic">Basic Auth</a-select-option>
            <a-select-option value="bearer">Bearer Token</a-select-option>
            <a-select-option value="api_key">API Key</a-select-option>
          </a-select>
        </a-form-item>
      </template>

      <!-- 金蝶配置 -->
      <template v-if="formData.webhook_type === 'kingdee'">
        <a-form-item label="金蝶配置">
          <a-alert
            message="金蝶连接信息"
            description="金蝶K3 Cloud的API地址、数据库ID、用户名、密码等信息从后端环境变量读取，无需在此配置。管道脚本清洗后的数据将直接作为金蝶API请求体推送。"
            type="info"
            show-icon
          />
        </a-form-item>
        
        <a-form-item label="保存模式">
          <a-radio-group v-model:value="formData.kingdee_save_mode" button-style="solid">
            <a-radio-button value="smart">智能模式</a-radio-button>
            <a-radio-button value="save_only">仅创建</a-radio-button>
            <a-radio-button value="draft_only">仅暂存</a-radio-button>
          </a-radio-group>
          <div class="form-item-tip">
            智能模式：先尝试Save创建，如果校验失败自动降级为Draft暂存
          </div>
        </a-form-item>
      </template>

      <!-- 鉴权配置（仅标准类型） -->
      <a-form-item
        v-if="formData.webhook_type === 'standard' && formData.auth_type !== 'none'"
        label="鉴权配置"
        name="auth_config"
      >
        <!-- Basic Auth -->
        <div v-if="formData.auth_type === 'basic'" class="auth-config-group">
          <a-input
            v-model:value="formData.auth_config.username"
            placeholder="用户名"
            style="margin-bottom: 8px"
          />
          <a-input-password
            v-model:value="formData.auth_config.password"
            placeholder="密码"
          />
        </div>

        <!-- Bearer Token -->
        <a-input-password
          v-else-if="formData.auth_type === 'bearer'"
          v-model:value="formData.auth_config.token"
          placeholder="Bearer Token"
        />

        <!-- API Key -->
        <div v-else-if="formData.auth_type === 'api_key'" class="auth-config-group">
          <a-input
            v-model:value="formData.auth_config.header_name"
            placeholder="Header名称，如：X-API-Key"
            style="margin-bottom: 8px"
          />
          <a-input-password
            v-model:value="formData.auth_config.api_key"
            placeholder="API Key值"
          />
        </div>
      </a-form-item>

      <!-- Secret Key（用于HMAC签名，仅标准类型） -->
      <a-form-item v-if="formData.webhook_type === 'standard'" label="Secret Key" name="secret_key">
        <a-input-password
          v-model:value="formData.secret_key"
          placeholder="用于HMAC-SHA256签名的密钥"
        />
        <div class="form-item-tip">
          系统将使用此密钥对请求体生成HMAC-SHA256签名，并放入X-IDP-Signature请求头
        </div>
      </a-form-item>

      <!-- 请求体模版（仅标准类型） -->
      <a-form-item v-if="formData.webhook_type === 'standard'" label="请求体模版" name="request_template">
        <div class="template-editor">
          <a-textarea
            v-model:value="templateText"
            :rows="10"
            placeholder="请输入JSON格式的请求体模版"
            @blur="validateJSON"
          />
          <div class="variable-helper">
            <span class="helper-title">可用变量：</span>
            <a-tag
              v-for="variable in availableVariables"
              :key="variable.key"
              color="blue"
              style="cursor: pointer; margin: 4px"
              @click="insertVariable(variable.key)"
            >
              {{ variable.key }}
            </a-tag>
          </div>
          <div v-if="jsonError" class="json-error">
            <a-alert :message="jsonError" type="error" show-icon />
          </div>
        </div>
      </a-form-item>

      <!-- 关联规则 -->
      <a-form-item label="关联规则" name="rule_ids">
        <a-select
          v-model:value="formData.rule_ids"
          mode="multiple"
          placeholder="请选择要关联的规则（可多选）"
          :options="ruleOptions"
          :loading="rulesLoading"
          allow-clear
          show-search
          :filter-option="filterRuleOption"
        />
        <div class="form-item-tip">
          选择哪些规则的任务完成后会推送到此Webhook
        </div>
      </a-form-item>

      <!-- 状态 -->
      <a-form-item label="状态" name="is_active">
        <a-switch v-model:checked="formData.is_active" />
        <span style="margin-left: 8px">
          {{ formData.is_active ? '启用' : '禁用' }}
        </span>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup>
import { ref, reactive, watch, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { ruleAPI } from '@/api/rule'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  webhook: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'success'])

// 表单引用
const formRef = ref()
const loading = ref(false)
const jsonError = ref('')
const rulesLoading = ref(false)
const ruleOptions = ref([])

// 是否为编辑模式
const isEdit = computed(() => !!props.webhook)

// 可用变量列表
const availableVariables = [
  { key: '{{task_id}}', description: '任务ID' },
  { key: '{{result_json}}', description: '提取结果JSON' },
  { key: '{{file_url}}', description: '文件访问URL' },
  { key: '{{meta_info}}', description: '任务元信息' }
]

// 表单数据
const formData = reactive({
  name: '',
  webhook_type: 'standard',  // standard | kingdee
  endpoint_url: '',
  auth_type: 'none',
  auth_config: {},
  secret_key: '',
  request_template: {},
  kingdee_save_mode: 'smart',  // smart | save_only | draft_only
  is_active: true,
  rule_ids: []
})

// 模版文本（用于编辑）
const templateText = ref('')

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入系统名称', trigger: 'blur' },
    { max: 100, message: '系统名称不能超过100个字符', trigger: 'blur' }
  ],
  webhook_type: [
    { required: true, message: '请选择Webhook类型', trigger: 'change' }
  ]
}

// 监听webhook变化，初始化表单
watch(() => props.webhook, (newVal) => {
  if (newVal) {
    Object.assign(formData, {
      name: newVal.name || '',
      webhook_type: newVal.webhook_type || 'standard',
      endpoint_url: newVal.endpoint_url || '',
      auth_type: newVal.auth_type || 'none',
      auth_config: newVal.auth_config || {},
      secret_key: newVal.secret_key || '',
      request_template: newVal.request_template || {},
      kingdee_save_mode: newVal.kingdee_config?.save_mode || 'smart',
      is_active: newVal.is_active !== undefined ? newVal.is_active : true,
      rule_ids: newVal.rule_ids || []
    })
    templateText.value = JSON.stringify(newVal.request_template || {}, null, 2)
  } else {
    resetForm()
  }
}, { immediate: true })

// 监听对话框显示，加载规则列表
watch(() => props.visible, (newVal) => {
  if (newVal) {
    loadRules()
  }
})

/**
 * 加载规则列表
 */
async function loadRules() {
  rulesLoading.value = true
  try {
    const response = await ruleAPI.list({ page: 1, page_size: 1000 })
    if (response && response.items) {
      ruleOptions.value = response.items.map(rule => ({
        value: rule.id,
        label: `${rule.name} (${rule.id})`
      }))
    }
  } catch (error) {
    console.error('加载规则列表失败:', error)
  } finally {
    rulesLoading.value = false
  }
}

/**
 * 规则选项过滤
 */
function filterRuleOption(input, option) {
  return option.label.toLowerCase().includes(input.toLowerCase())
}

// 监听鉴权方式变化，初始化auth_config
watch(() => formData.auth_type, (newVal) => {
  if (newVal === 'none') {
    formData.auth_config = {}
  } else if (newVal === 'basic') {
    formData.auth_config = { username: '', password: '' }
  } else if (newVal === 'bearer') {
    formData.auth_config = { token: '' }
  } else if (newVal === 'api_key') {
    formData.auth_config = { header_name: 'X-API-Key', api_key: '' }
  }
})

/**
 * 验证JSON格式
 */
function validateJSON() {
  jsonError.value = ''
  try {
    if (templateText.value.trim()) {
      formData.request_template = JSON.parse(templateText.value)
    } else {
      formData.request_template = {}
    }
  } catch (e) {
    jsonError.value = `JSON格式错误: ${e.message}`
  }
}

/**
 * 插入变量到模版
 */
function insertVariable(variable) {
  const textarea = document.querySelector('.template-editor textarea')
  if (textarea) {
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const text = templateText.value
    templateText.value = text.substring(0, start) + variable + text.substring(end)
    
    // 设置光标位置
    setTimeout(() => {
      textarea.focus()
      textarea.setSelectionRange(start + variable.length, start + variable.length)
    }, 0)
  }
}

/**
 * 提交表单
 */
async function handleSubmit() {
  try {
    // 验证表单
    await formRef.value.validate()
    
    // 标准类型的额外验证
    if (formData.webhook_type === 'standard') {
      // 验证URL
      if (!formData.endpoint_url) {
        message.error('请输入Endpoint URL')
        return
      }
      
      // 验证JSON
      validateJSON()
      if (jsonError.value) {
        message.error('请修正JSON格式错误')
        return
      }

      // 验证鉴权配置
      if (formData.auth_type !== 'none') {
        if (formData.auth_type === 'basic') {
          if (!formData.auth_config.username || !formData.auth_config.password) {
            message.error('请填写完整的Basic Auth配置')
            return
          }
        } else if (formData.auth_type === 'bearer') {
          if (!formData.auth_config.token) {
            message.error('请填写Bearer Token')
            return
          }
        } else if (formData.auth_type === 'api_key') {
          if (!formData.auth_config.header_name || !formData.auth_config.api_key) {
            message.error('请填写完整的API Key配置')
            return
          }
        }
      }
    }

    loading.value = true
    
    // 构建提交数据
    const submitData = {
      name: formData.name,
      webhook_type: formData.webhook_type,
      endpoint_url: formData.webhook_type === 'standard' ? formData.endpoint_url : '',
      auth_type: formData.webhook_type === 'standard' ? formData.auth_type : 'none',
      auth_config: formData.webhook_type === 'standard' ? formData.auth_config : {},
      secret_key: formData.webhook_type === 'standard' ? formData.secret_key : '',
      request_template: formData.webhook_type === 'standard' ? formData.request_template : {},
      kingdee_config: formData.webhook_type === 'kingdee' ? {
        save_mode: formData.kingdee_save_mode
      } : null,
      is_active: formData.is_active,
      rule_ids: formData.rule_ids
    }
    
    // 触发成功事件
    emit('success', submitData)
    
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 取消操作
 */
function handleCancel() {
  emit('update:visible', false)
  resetForm()
}

/**
 * 重置表单
 */
function resetForm() {
  Object.assign(formData, {
    name: '',
    webhook_type: 'standard',
    endpoint_url: '',
    auth_type: 'none',
    auth_config: {},
    secret_key: '',
    request_template: {},
    kingdee_save_mode: 'smart',
    is_active: true,
    rule_ids: []
  })
  templateText.value = ''
  jsonError.value = ''
  formRef.value?.resetFields()
}
</script>

<style scoped>
.auth-config-group {
  display: flex;
  flex-direction: column;
}

.form-item-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}

.template-editor {
  position: relative;
}

.variable-helper {
  margin-top: 8px;
  padding: 8px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.helper-title {
  font-size: 12px;
  color: #666;
  margin-right: 8px;
}

.json-error {
  margin-top: 8px;
}
</style>
