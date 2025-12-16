<template>
  <div class="global-config">
    <a-spin :spinning="loading">
      <a-form
        :model="formData"
        :label-col="{ span: 8 }"
        :wrapper-col="{ span: 12 }"
        @finish="handleSubmit"
      >
        <a-alert
          message="全局配置说明"
          description="配置系统运行的核心参数。修改后立即生效，无需重启服务。"
          type="info"
          show-icon
          class="mb-6"
        />

        <!-- 钉钉通知配置 -->
        <a-divider orientation="left">
          <DingdingOutlined class="mr-2" />
          钉钉群通知
        </a-divider>

        <a-form-item label="启用钉钉通知">
          <a-switch
            v-model:checked="dingtalkConfig.enabled"
            checked-children="开启"
            un-checked-children="关闭"
          />
          <div class="text-xs text-gray-400 mt-1">
            开启后，系统将根据配置的事件和规则发送通知到钉钉群
          </div>
        </a-form-item>

        <a-form-item label="Webhook URL">
          <a-input
            v-model:value="dingtalkConfig.webhook_url"
            placeholder="https://oapi.dingtalk.com/robot/send?access_token=xxx"
            :disabled="!dingtalkConfig.enabled"
            style="width: 100%"
            :status="dingtalkConfig.enabled && !dingtalkConfig.webhook_url ? 'error' : ''"
          />
          <div class="text-xs text-gray-400 mt-1">
            钉钉群机器人的Webhook地址，可在钉钉群设置中获取
          </div>
        </a-form-item>

        <a-form-item label="加签密钥">
          <a-input-password
            v-model:value="dingtalkConfig.secret"
            placeholder="SEC开头的密钥（如已配置加签安全设置）"
            :disabled="!dingtalkConfig.enabled"
            style="width: 100%"
          />
          <div class="text-xs text-gray-400 mt-1">
            <span v-if="dingtalkConfig.has_secret" class="text-green-500">✓ 已配置加签密钥</span>
            <span v-else>如果机器人启用了"加签"安全设置，请填写SEC开头的密钥</span>
          </div>
        </a-form-item>

        <!-- @人员配置 -->
        <a-form-item label="@人员设置">
          <a-radio-group v-model:value="atMode" :disabled="!dingtalkConfig.enabled">
            <a-radio value="all">@所有人</a-radio>
            <a-radio value="mobiles">@指定人员</a-radio>
            <a-radio value="none">不@任何人</a-radio>
          </a-radio-group>
        </a-form-item>

        <a-form-item v-if="atMode === 'mobiles'" label="手机号列表">
          <a-select
            v-model:value="dingtalkConfig.at_mobiles"
            mode="tags"
            placeholder="输入手机号后按回车添加"
            :disabled="!dingtalkConfig.enabled"
            style="width: 100%"
            :token-separators="[',', ' ']"
          />
          <div class="text-xs text-gray-400 mt-1">
            输入需要@的人员手机号，多个手机号用逗号或空格分隔
          </div>
        </a-form-item>

        <!-- 通知事件配置 -->
        <a-form-item label="通知事件">
          <div class="event-checkboxes">
            <a-checkbox
              v-model:checked="dingtalkConfig.notify_events.pending_audit"
              :disabled="!dingtalkConfig.enabled"
            >
              <span class="font-medium">人工审核提醒</span>
              <span class="text-xs text-gray-400 ml-2">文档需要人工审核时通知</span>
            </a-checkbox>
            <a-checkbox
              v-model:checked="dingtalkConfig.notify_events.audit_completed"
              :disabled="!dingtalkConfig.enabled"
            >
              <span class="font-medium">审核完成通知</span>
              <span class="text-xs text-gray-400 ml-2">审核通过或驳回时通知</span>
            </a-checkbox>
            <a-checkbox
              v-model:checked="dingtalkConfig.notify_events.pipeline_success"
              :disabled="!dingtalkConfig.enabled"
            >
              <span class="font-medium">管道处理成功</span>
              <span class="text-xs text-gray-400 ml-2">数据清洗转换完成时通知</span>
            </a-checkbox>
            <a-checkbox
              v-model:checked="dingtalkConfig.notify_events.pipeline_failed"
              :disabled="!dingtalkConfig.enabled"
            >
              <span class="font-medium">管道处理失败</span>
              <span class="text-xs text-gray-400 ml-2">管道执行出错时通知</span>
            </a-checkbox>
            <a-checkbox
              v-model:checked="dingtalkConfig.notify_events.push_success"
              :disabled="!dingtalkConfig.enabled"
            >
              <span class="font-medium">推送成功通知</span>
              <span class="text-xs text-gray-400 ml-2">数据推送到目标系统成功时通知</span>
            </a-checkbox>
            <a-checkbox
              v-model:checked="dingtalkConfig.notify_events.push_failed"
              :disabled="!dingtalkConfig.enabled"
            >
              <span class="font-medium">推送失败通知</span>
              <span class="text-xs text-gray-400 ml-2">推送失败进入死信队列时通知</span>
            </a-checkbox>
          </div>
        </a-form-item>

        <!-- 适用规则配置 -->
        <a-form-item label="适用规则">
          <a-radio-group v-model:value="ruleMode" :disabled="!dingtalkConfig.enabled">
            <a-radio value="all">全部规则</a-radio>
            <a-radio value="selected">指定规则</a-radio>
          </a-radio-group>
        </a-form-item>

        <a-form-item v-if="ruleMode === 'selected'" label="选择规则">
          <a-select
            v-model:value="dingtalkConfig.notify_rules"
            mode="multiple"
            placeholder="请选择需要通知的规则"
            :disabled="!dingtalkConfig.enabled"
            style="width: 100%"
            :options="ruleOptions"
            :loading="loadingRules"
          />
          <div class="text-xs text-gray-400 mt-1">
            只有选中的规则触发事件时才会发送通知
          </div>
        </a-form-item>

        <a-form-item :wrapper-col="{ offset: 8, span: 12 }">
          <a-space>
            <a-button
              type="primary"
              :loading="savingDingtalk"
              :disabled="dingtalkConfig.enabled && !dingtalkConfig.webhook_url"
              @click="handleSaveDingtalk"
            >
              <SaveOutlined />
              保存钉钉配置
            </a-button>
            <a-button
              :loading="testingDingtalk"
              :disabled="!dingtalkConfig.webhook_url"
              @click="handleTestDingtalk"
            >
              <SendOutlined />
              发送测试消息
            </a-button>
          </a-space>
        </a-form-item>

        <!-- OCR配置 -->
        <a-divider orientation="left">
          <ScanOutlined class="mr-2" />
          OCR配置
        </a-divider>

        <a-form-item
          label="OCR超时时间"
          name="ocr_timeout"
          :rules="[
            { required: true, message: '请输入OCR超时时间' },
            { type: 'number', min: 30, max: 600, message: '超时时间范围为30-600秒' }
          ]"
        >
          <a-input-number
            v-model:value="formData.ocr_timeout"
            :min="30"
            :max="600"
            :step="10"
            style="width: 200px"
          />
          <span class="ml-2 text-gray-500">秒</span>
        </a-form-item>

        <a-form-item
          label="最大并行OCR任务数"
          name="ocr_max_parallel"
          :rules="[
            { required: true, message: '请输入最大并行任务数' },
            { type: 'number', min: 1, max: 16, message: '并行数范围为1-16' }
          ]"
        >
          <a-input-number
            v-model:value="formData.ocr_max_parallel"
            :min="1"
            :max="16"
            :step="1"
            style="width: 200px"
          />
          <span class="ml-2 text-gray-500">个</span>
        </a-form-item>

        <!-- LLM配置 -->
        <a-divider orientation="left">
          <RobotOutlined class="mr-2" />
          LLM配置
        </a-divider>

        <a-form-item
          label="LLM超时时间"
          name="llm_timeout"
          :rules="[
            { required: true, message: '请输入LLM超时时间' },
            { type: 'number', min: 10, max: 300, message: '超时时间范围为10-300秒' }
          ]"
        >
          <a-input-number
            v-model:value="formData.llm_timeout"
            :min="10"
            :max="300"
            :step="5"
            style="width: 200px"
          />
          <span class="ml-2 text-gray-500">秒</span>
        </a-form-item>

        <a-form-item
          label="LLM Token单价"
          name="llm_token_price"
          :rules="[
            { required: true, message: '请输入Token单价' },
            { type: 'number', min: 0, message: 'Token单价不能为负数' }
          ]"
        >
          <a-input-number
            v-model:value="formData.llm_token_price"
            :min="0"
            :max="1"
            :step="0.0001"
            :precision="4"
            style="width: 200px"
          />
          <span class="ml-2 text-gray-500">元/Token</span>
        </a-form-item>

        <!-- 任务队列配置 -->
        <a-divider orientation="left">
          <UnorderedListOutlined class="mr-2" />
          任务队列配置
        </a-divider>

        <a-form-item
          label="消息队列最大长度"
          name="queue_max_length"
          :rules="[
            { required: true, message: '请输入队列最大长度' },
            { type: 'number', min: 100, max: 100000, message: '队列长度范围为100-100000' }
          ]"
        >
          <a-input-number
            v-model:value="formData.queue_max_length"
            :min="100"
            :max="100000"
            :step="100"
            style="width: 200px"
          />
          <span class="ml-2 text-gray-500">条</span>
        </a-form-item>

        <a-form-item
          label="Worker并发数"
          name="worker_concurrency"
          :rules="[
            { required: true, message: '请输入Worker并发数' },
            { type: 'number', min: 1, max: 50, message: '并发数范围为1-50' }
          ]"
        >
          <a-input-number
            v-model:value="formData.worker_concurrency"
            :min="1"
            :max="50"
            :step="1"
            style="width: 200px"
          />
          <span class="ml-2 text-gray-500">个</span>
        </a-form-item>

        <!-- 性能配置 -->
        <a-divider orientation="left">
          <ThunderboltOutlined class="mr-2" />
          性能配置
        </a-divider>

        <a-form-item
          label="数据库连接池大小"
          name="db_pool_size"
          :rules="[
            { required: true, message: '请输入连接池大小' },
            { type: 'number', min: 5, max: 100, message: '连接池大小范围为5-100' }
          ]"
        >
          <a-input-number
            v-model:value="formData.db_pool_size"
            :min="5"
            :max="100"
            :step="5"
            style="width: 200px"
          />
          <span class="ml-2 text-gray-500">个</span>
        </a-form-item>

        <a-form-item
          label="Redis缓存过期时间"
          name="redis_cache_ttl"
          :rules="[
            { required: true, message: '请输入缓存过期时间' },
            { type: 'number', min: 60, max: 86400, message: '过期时间范围为60-86400秒' }
          ]"
        >
          <a-input-number
            v-model:value="formData.redis_cache_ttl"
            :min="60"
            :max="86400"
            :step="60"
            style="width: 200px"
          />
          <span class="ml-2 text-gray-500">秒</span>
        </a-form-item>

        <!-- 配置摘要 -->
        <a-divider orientation="left">
          <InfoCircleOutlined class="mr-2" />
          配置摘要
        </a-divider>

        <a-descriptions :column="2" bordered size="small" class="mb-6">
          <a-descriptions-item label="最后更新时间">
            {{ lastUpdated || '未更新' }}
          </a-descriptions-item>
          <a-descriptions-item label="更新人">
            {{ updatedBy || '系统' }}
          </a-descriptions-item>
        </a-descriptions>

        <!-- 操作按钮 -->
        <a-form-item :wrapper-col="{ offset: 8, span: 12 }">
          <a-space>
            <a-button type="primary" html-type="submit" :loading="saving">
              <SaveOutlined />
              保存配置
            </a-button>
            <a-button @click="handleReset">
              <ReloadOutlined />
              重置
            </a-button>
            <a-button @click="handleRestoreDefaults" danger>
              <UndoOutlined />
              恢复默认值
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-spin>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { 
  ScanOutlined,
  RobotOutlined,
  UnorderedListOutlined,
  ThunderboltOutlined,
  InfoCircleOutlined,
  SaveOutlined, 
  ReloadOutlined,
  UndoOutlined,
  SendOutlined,
  DingdingOutlined
} from '@ant-design/icons-vue'
import { systemAPI } from '@/api'
import dayjs from 'dayjs'

// 加载状态
const loading = ref(false)
const saving = ref(false)
const savingDingtalk = ref(false)
const testingDingtalk = ref(false)
const loadingRules = ref(false)

// 元信息
const lastUpdated = ref('')
const updatedBy = ref('')

// 规则列表
const ruleOptions = ref([])

// @人员模式
const atMode = ref('all')

// 规则模式
const ruleMode = ref('all')

// 默认配置值
const defaultConfig = {
  ocr_timeout: 300,
  ocr_max_parallel: 4,
  llm_timeout: 60,
  llm_token_price: 0.002,
  queue_max_length: 10000,
  worker_concurrency: 5,
  db_pool_size: 20,
  redis_cache_ttl: 3600
}

// 表单数据
const formData = reactive({ ...defaultConfig })

// 钉钉配置
const dingtalkConfig = reactive({
  enabled: false,
  webhook_url: '',
  secret: '',
  has_secret: false,
  at_all: true,
  at_mobiles: [],
  notify_events: {
    pending_audit: true,
    audit_completed: false,
    pipeline_success: false,
    pipeline_failed: true,
    push_success: false,
    push_failed: true
  },
  notify_rules: []
})

// 监听atMode变化，同步到dingtalkConfig
watch(atMode, (newVal) => {
  if (newVal === 'all') {
    dingtalkConfig.at_all = true
    dingtalkConfig.at_mobiles = []
  } else if (newVal === 'none') {
    dingtalkConfig.at_all = false
    dingtalkConfig.at_mobiles = []
  } else {
    dingtalkConfig.at_all = false
  }
})

// 监听ruleMode变化
watch(ruleMode, (newVal) => {
  if (newVal === 'all') {
    dingtalkConfig.notify_rules = []
  }
})

/**
 * 加载配置
 */
async function loadConfig() {
  loading.value = true
  try {
    const response = await systemAPI.getConfigs()
    
    if (response.data && response.data.configs) {
      const configs = response.data.configs
      
      Object.keys(formData).forEach(key => {
        if (configs[key] !== undefined) {
          formData[key] = configs[key].value
        }
      })
      
      if (configs.ocr_timeout) {
        lastUpdated.value = configs.ocr_timeout.updated_at 
          ? dayjs(configs.ocr_timeout.updated_at).format('YYYY-MM-DD HH:mm:ss')
          : ''
        updatedBy.value = configs.ocr_timeout.updated_by || '系统'
      }
    }
  } catch (error) {
    console.error('加载配置失败:', error)
    message.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

/**
 * 加载钉钉配置
 */
async function loadDingtalkConfig() {
  try {
    const response = await systemAPI.getDingTalkConfig()
    const data = response?.data
    if (data) {
      dingtalkConfig.enabled = data.enabled || false
      dingtalkConfig.webhook_url = data.webhook_url || ''
      dingtalkConfig.has_secret = data.has_secret || false
      dingtalkConfig.secret = ''
      dingtalkConfig.at_all = data.at_all !== false
      dingtalkConfig.at_mobiles = data.at_mobiles || []
      dingtalkConfig.notify_events = {
        pending_audit: true,
        audit_completed: false,
        pipeline_success: false,
        pipeline_failed: true,
        push_success: false,
        push_failed: true,
        ...data.notify_events
      }
      dingtalkConfig.notify_rules = data.notify_rules || []
      
      // 设置atMode
      if (dingtalkConfig.at_mobiles && dingtalkConfig.at_mobiles.length > 0) {
        atMode.value = 'mobiles'
      } else if (dingtalkConfig.at_all) {
        atMode.value = 'all'
      } else {
        atMode.value = 'none'
      }
      
      // 设置ruleMode
      ruleMode.value = dingtalkConfig.notify_rules.length > 0 ? 'selected' : 'all'
    }
  } catch (error) {
    console.error('加载钉钉配置失败:', error)
  }
}

/**
 * 加载规则列表
 */
async function loadRules() {
  loadingRules.value = true
  try {
    const response = await systemAPI.getRulesSimple()
    const data = response?.data
    if (Array.isArray(data)) {
      ruleOptions.value = data.map(r => ({
        value: r.id,
        label: r.name
      }))
    }
  } catch (error) {
    console.error('加载规则列表失败:', error)
  } finally {
    loadingRules.value = false
  }
}

/**
 * 保存钉钉配置
 */
async function handleSaveDingtalk() {
  savingDingtalk.value = true
  try {
    const data = {
      enabled: dingtalkConfig.enabled,
      webhook_url: dingtalkConfig.webhook_url,
      at_all: dingtalkConfig.at_all,
      at_mobiles: dingtalkConfig.at_mobiles,
      notify_events: dingtalkConfig.notify_events,
      notify_rules: ruleMode.value === 'all' ? [] : dingtalkConfig.notify_rules
    }
    
    if (dingtalkConfig.secret) {
      data.secret = dingtalkConfig.secret
    }
    
    await systemAPI.updateDingTalkConfig(data)
    message.success('钉钉配置保存成功')
    await loadDingtalkConfig()
  } catch (error) {
    console.error('保存钉钉配置失败:', error)
    message.error(error.response?.data?.detail || '保存钉钉配置失败')
  } finally {
    savingDingtalk.value = false
  }
}

/**
 * 测试钉钉Webhook
 */
async function handleTestDingtalk() {
  if (!dingtalkConfig.webhook_url) {
    message.warning('请先输入Webhook URL')
    return
  }
  
  testingDingtalk.value = true
  try {
    await systemAPI.testDingTalkWebhook(
      dingtalkConfig.webhook_url, 
      dingtalkConfig.secret,
      dingtalkConfig.at_all,
      dingtalkConfig.at_mobiles
    )
    message.success('测试消息发送成功，请查看钉钉群')
  } catch (error) {
    console.error('测试钉钉Webhook失败:', error)
    message.error(error.response?.data?.detail || '测试失败，请检查配置')
  } finally {
    testingDingtalk.value = false
  }
}

/**
 * 提交表单
 */
async function handleSubmit() {
  saving.value = true
  try {
    const updatePromises = Object.keys(formData).map(key => 
      systemAPI.updateConfig(key, formData[key])
    )
    
    await Promise.all(updatePromises)
    message.success('配置保存成功')
    await loadConfig()
  } catch (error) {
    console.error('保存配置失败:', error)
    message.error(error.response?.data?.message || '保存配置失败')
  } finally {
    saving.value = false
  }
}

/**
 * 重置表单
 */
function handleReset() {
  loadConfig()
  loadDingtalkConfig()
}

/**
 * 恢复默认值
 */
function handleRestoreDefaults() {
  Modal.confirm({
    title: '确认恢复默认值',
    content: '此操作将恢复所有配置项为系统默认值，是否继续？',
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      Object.assign(formData, defaultConfig)
      message.success('已恢复默认值，请点击保存按钮应用更改')
    }
  })
}

// 组件挂载时加载配置
onMounted(() => {
  loadConfig()
  loadDingtalkConfig()
  loadRules()
})
</script>

<style scoped>
.global-config {
  max-width: 900px;
}

:deep(.ant-form-item-label) {
  font-weight: 500;
}

:deep(.ant-divider-inner-text) {
  font-weight: 600;
  font-size: 15px;
}

.event-checkboxes {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.event-checkboxes .ant-checkbox-wrapper {
  margin-left: 0;
}
</style>
