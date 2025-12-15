<template>
  <div class="retention-config">
    <a-spin :spinning="loading">
      <a-form
        :model="formData"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 14 }"
        @finish="handleSubmit"
      >
        <a-alert
          message="数据生命周期说明"
          description="配置原始文件和提取数据的留存期限。系统将在每日凌晨02:00自动清理过期数据。"
          type="info"
          show-icon
          class="mb-6"
        />

        <!-- 原始文件留存期 -->
        <a-form-item
          label="原始文件留存期"
          name="file_retention_days"
          :rules="[
            { required: true, message: '请输入文件留存天数' },
            { type: 'number', min: 1, max: 365, message: '留存天数范围为1-365天' }
          ]"
        >
          <a-input-number
            v-model:value="formData.file_retention_days"
            :min="1"
            :max="365"
            :step="1"
            style="width: 200px"
          />
          <span class="ml-2 text-gray-500">天</span>
          <div class="text-xs text-gray-400 mt-1">
            超过此期限的PDF和图片文件将被自动删除
          </div>
        </a-form-item>

        <!-- 提取数据留存期 -->
        <a-form-item
          label="提取数据留存期"
          name="data_retention_days"
        >
          <a-radio-group v-model:value="dataRetentionType">
            <a-radio value="permanent">永久保留</a-radio>
            <a-radio value="custom">自定义天数</a-radio>
          </a-radio-group>
          
          <a-input-number
            v-if="dataRetentionType === 'custom'"
            v-model:value="formData.data_retention_days"
            :min="1"
            :max="3650"
            :step="1"
            style="width: 200px"
            class="mt-2"
          />
          <span v-if="dataRetentionType === 'custom'" class="ml-2 text-gray-500">天</span>
          
          <div class="text-xs text-gray-400 mt-1">
            提取结果、OCR文本等结构化数据的留存期限
          </div>
        </a-form-item>

        <!-- 下次清理时间 -->
        <a-form-item label="下次清理时间">
          <div class="flex items-center">
            <ClockCircleOutlined class="mr-2 text-blue-500" />
            <span class="font-medium">{{ nextCleanupTime }}</span>
          </div>
          <div class="text-xs text-gray-400 mt-1">
            系统将在每日凌晨02:00自动执行清理任务
          </div>
        </a-form-item>

        <!-- 清理统计 -->
        <a-form-item label="最近清理记录" v-if="lastCleanup">
          <a-descriptions :column="1" size="small" bordered>
            <a-descriptions-item label="清理时间">
              {{ lastCleanup.time }}
            </a-descriptions-item>
            <a-descriptions-item label="删除文件数">
              {{ lastCleanup.file_count }} 个
            </a-descriptions-item>
            <a-descriptions-item label="释放空间">
              {{ formatBytes(lastCleanup.space_freed) }}
            </a-descriptions-item>
          </a-descriptions>
        </a-form-item>

        <!-- 操作按钮 -->
        <a-form-item :wrapper-col="{ offset: 6, span: 14 }">
          <a-space>
            <a-button type="primary" html-type="submit" :loading="saving">
              <SaveOutlined />
              保存配置
            </a-button>
            <a-button @click="handleReset">
              <ReloadOutlined />
              重置
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-spin>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { 
  ClockCircleOutlined, 
  SaveOutlined, 
  ReloadOutlined 
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
 * 数据留存类型（永久/自定义）
 */
const dataRetentionType = ref('permanent')

/**
 * 表单数据
 */
const formData = reactive({
  file_retention_days: 30,
  data_retention_days: -1 // -1表示永久保留
})

/**
 * 最近清理记录
 */
const lastCleanup = ref(null)

/**
 * 计算下次清理时间
 */
const nextCleanupTime = computed(() => {
  const now = dayjs()
  let next = dayjs().hour(2).minute(0).second(0)
  
  // 如果当前时间已过今天的02:00，则显示明天的02:00
  if (now.isAfter(next)) {
    next = next.add(1, 'day')
  }
  
  return next.format('YYYY-MM-DD HH:mm:ss')
})

/**
 * 格式化字节大小
 */
function formatBytes(bytes) {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

/**
 * 加载配置
 */
async function loadConfig() {
  loading.value = true
  try {
    const response = await systemAPI.getRetentionConfig()
    
    if (response.data) {
      formData.file_retention_days = response.data.file_retention_days || 30
      formData.data_retention_days = response.data.data_retention_days || -1
      
      // 设置数据留存类型
      if (formData.data_retention_days === -1) {
        dataRetentionType.value = 'permanent'
      } else {
        dataRetentionType.value = 'custom'
      }
      
      // 加载最近清理记录
      if (response.data.last_cleanup) {
        lastCleanup.value = response.data.last_cleanup
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
    // 根据选择的类型设置data_retention_days
    const submitData = {
      file_retention_days: formData.file_retention_days,
      data_retention_days: dataRetentionType.value === 'permanent' 
        ? -1 
        : formData.data_retention_days
    }
    
    await systemAPI.updateRetentionConfig(submitData)
    message.success('配置保存成功')
    
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
 * 组件挂载时加载配置
 */
onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.retention-config {
  max-width: 800px;
}

:deep(.ant-form-item-label) {
  font-weight: 500;
}
</style>
