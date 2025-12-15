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
          <div class="text-xs text-gray-400 mt-1">
            单个文档OCR处理的最大等待时间
          </div>
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
          <div class="text-xs text-gray-400 mt-1">
            多页文档并行处理的最大页数
          </div>
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
          <div class="text-xs text-gray-400 mt-1">
            LLM服务调用的最大等待时间，超时将自动降级
          </div>
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
          <div class="text-xs text-gray-400 mt-1">
            用于成本估算，不影响实际计费
          </div>
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
          <div class="text-xs text-gray-400 mt-1">
            RabbitMQ队列的最大消息数量
          </div>
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
          <div class="text-xs text-gray-400 mt-1">
            每个Worker进程同时处理的任务数
          </div>
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
          <div class="text-xs text-gray-400 mt-1">
            MySQL连接池的最大连接数
          </div>
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
          <div class="text-xs text-gray-400 mt-1">
            规则配置等数据的缓存有效期
          </div>
        </a-form-item>

        <!-- 当前配置摘要 -->
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
import { ref, reactive, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { 
  ScanOutlined,
  RobotOutlined,
  UnorderedListOutlined,
  ThunderboltOutlined,
  InfoCircleOutlined,
  SaveOutlined, 
  ReloadOutlined,
  UndoOutlined
} from '@ant-design/icons-vue'
import { systemAPI } from '@/api'
import dayjs from 'dayjs'

/**
 * 加载状态
 */
const loading = ref(false)

/**
 * 保存状态
 */
const saving = ref(false)

/**
 * 最后更新时间
 */
const lastUpdated = ref('')

/**
 * 更新人
 */
const updatedBy = ref('')

/**
 * 默认配置值
 */
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

/**
 * 表单数据
 */
const formData = reactive({ ...defaultConfig })

/**
 * 加载配置
 */
async function loadConfig() {
  loading.value = true
  try {
    const response = await systemAPI.getConfigs()
    
    if (response.data && response.data.configs) {
      const configs = response.data.configs
      
      // 更新表单数据
      Object.keys(formData).forEach(key => {
        if (configs[key] !== undefined) {
          formData[key] = configs[key].value
        }
      })
      
      // 更新元信息
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
 * 提交表单
 */
async function handleSubmit() {
  saving.value = true
  try {
    // 批量更新所有配置
    const updatePromises = Object.keys(formData).map(key => 
      systemAPI.updateConfig(key, formData[key])
    )
    
    await Promise.all(updatePromises)
    message.success('配置保存成功，已立即生效')
    
    // 重新加载配置
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

/**
 * 组件挂载时加载配置
 */
onMounted(() => {
  loadConfig()
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
</style>
