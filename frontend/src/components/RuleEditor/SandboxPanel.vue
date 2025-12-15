<template>
  <div class="sandbox-panel h-full flex flex-col">
    <!-- 头部 -->
    <div class="flex justify-between items-center p-4 border-b">
      <h4 class="text-base font-medium">沙箱测试</h4>
      <a-button type="text" @click="handleClose">
        <template #icon><CloseOutlined /></template>
      </a-button>
    </div>

    <!-- 内容区 -->
    <div class="flex-1 overflow-y-auto p-4">
      <!-- 文件上传 -->
      <div class="mb-4">
        <a-upload
          :before-upload="handleBeforeUpload"
          :show-upload-list="false"
          accept=".pdf,.jpg,.jpeg,.png"
        >
          <a-button block>
            <template #icon><UploadOutlined /></template>
            上传测试文件
          </a-button>
        </a-upload>
        <div class="text-xs text-gray-500 mt-1">
          支持PDF、JPG、PNG格式，最大20MB
        </div>
      </div>

      <!-- 已上传文件 -->
      <div v-if="uploadedFile" class="mb-4 p-3 bg-gray-50 rounded">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <FileOutlined class="text-blue-500" />
            <span class="text-sm">{{ uploadedFile.name }}</span>
          </div>
          <a-button
            type="link"
            size="small"
            danger
            @click="handleRemoveFile"
          >
            删除
          </a-button>
        </div>
      </div>

      <!-- 运行测试按钮 -->
      <a-button
        type="primary"
        block
        :loading="testing"
        :disabled="!uploadedFile"
        @click="handleRunTest"
      >
        <template #icon><PlayCircleOutlined /></template>
        运行测试
      </a-button>

      <!-- 测试结果 -->
      <div v-if="testResult" class="mt-6">
        <a-divider orientation="left">测试结果</a-divider>

        <!-- 结果标签页 -->
        <a-tabs v-model:activeKey="resultTab">
          <!-- JSON结果 -->
          <a-tab-pane key="json" tab="提取结果">
            <div class="result-container">
              <div class="flex justify-between items-center mb-2">
                <span class="text-sm font-medium">JSON输出</span>
                <a-button size="small" @click="handleCopyJson">
                  <template #icon><CopyOutlined /></template>
                  复制
                </a-button>
              </div>
              <pre class="json-viewer">{{ formatJson(testResult.extracted_data) }}</pre>
            </div>
          </a-tab-pane>

          <!-- OCR标注 -->
          <a-tab-pane key="ocr" tab="OCR标注">
            <div class="result-container">
              <div v-if="testResult.ocr_result" class="space-y-3">
                <div
                  v-for="(page, index) in testResult.ocr_result.pages"
                  :key="index"
                  class="border rounded p-3"
                >
                  <div class="text-sm font-medium mb-2">第 {{ index + 1 }} 页</div>
                  <div class="text-xs space-y-1">
                    <div
                      v-for="(block, blockIndex) in page.blocks"
                      :key="blockIndex"
                      class="p-2 bg-gray-50 rounded"
                    >
                      <div class="font-medium">{{ block.text }}</div>
                      <div class="text-gray-500">
                        置信度: {{ (block.confidence * 100).toFixed(1) }}%
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <a-empty v-else description="无OCR结果" />
            </div>
          </a-tab-pane>

          <!-- 合并文本 -->
          <a-tab-pane key="text" tab="合并文本">
            <div class="result-container">
              <div class="flex justify-between items-center mb-2">
                <span class="text-sm font-medium">全文预览</span>
                <a-button size="small" @click="handleCopyText">
                  <template #icon><CopyOutlined /></template>
                  复制
                </a-button>
              </div>
              <pre class="text-viewer">{{ testResult.merged_text }}</pre>
            </div>
          </a-tab-pane>

          <!-- 置信度分析 -->
          <a-tab-pane key="confidence" tab="置信度">
            <div class="result-container">
              <div v-if="testResult.confidence_scores" class="space-y-2">
                <div
                  v-for="(confidence, key) in testResult.confidence_scores"
                  :key="key"
                  class="flex items-center justify-between p-2 border-b"
                >
                  <span class="text-sm">{{ key }}</span>
                  <div class="flex items-center space-x-2">
                    <a-progress
                      :percent="Math.round(confidence)"
                      :stroke-color="getConfidenceColor(confidence)"
                      :show-info="false"
                      style="width: 100px"
                    />
                    <span class="text-sm font-medium">
                      {{ confidence.toFixed(1) }}%
                    </span>
                  </div>
                </div>
              </div>
              <a-empty v-else description="无置信度数据" />
            </div>
          </a-tab-pane>
        </a-tabs>

        <!-- 处理信息 -->
        <div class="mt-4 p-3 bg-blue-50 rounded">
          <div class="text-sm space-y-1">
            <div>
              <span class="text-gray-600">处理耗时：</span>
              <span class="font-medium">{{ formatDuration(testResult.processing_time) }}</span>
            </div>
            <div v-if="testResult.ocr_result">
              <span class="text-gray-600">OCR引擎：</span>
              <span class="font-medium">{{ testResult.ocr_result.engine_used }}</span>
              <span v-if="testResult.ocr_result.fallback_used" class="ml-2 text-orange-500">(备用引擎)</span>
            </div>
            <div v-if="testResult.ocr_result && testResult.ocr_result.pages">
              <span class="text-gray-600">页数：</span>
              <span class="font-medium">{{ testResult.ocr_result.pages.length }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 错误信息 -->
      <div v-if="testError" class="mt-4">
        <a-alert
          type="error"
          :message="testError"
          show-icon
          closable
          @close="testError = ''"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  CloseOutlined,
  UploadOutlined,
  PlayCircleOutlined,
  FileOutlined,
  CopyOutlined
} from '@ant-design/icons-vue'
import { ruleAPI } from '@/api/rule'

const props = defineProps({
  ruleId: {
    type: String,
    required: true
  },
  config: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['close'])

// 状态
const uploadedFile = ref(null)
const testing = ref(false)
const testResult = ref(null)
const testError = ref('')
const resultTab = ref('json')

// 文件上传前处理
const handleBeforeUpload = (file) => {
  // 验证文件大小
  const isLt20M = file.size / 1024 / 1024 < 20
  if (!isLt20M) {
    message.error('文件大小不能超过20MB')
    return false
  }

  // 验证文件类型
  const validTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
  if (!validTypes.includes(file.type)) {
    message.error('只支持PDF、JPG、PNG格式')
    return false
  }

  uploadedFile.value = file
  message.success('文件上传成功')
  
  // 阻止自动上传
  return false
}

// 删除文件
const handleRemoveFile = () => {
  uploadedFile.value = null
  testResult.value = null
  testError.value = ''
}

// 运行测试
const handleRunTest = async () => {
  if (!uploadedFile.value) {
    message.warning('请先上传测试文件')
    return
  }

  testing.value = true
  testError.value = ''
  testResult.value = null

  try {
    // 提示：沙箱测试将使用当前保存的配置
    // 如果用户修改了配置但未保存，需要先保存
    message.info('正在使用当前保存的配置进行测试...')
    
    const formData = new FormData()
    formData.append('file', uploadedFile.value)

    const response = await ruleAPI.sandbox(props.ruleId, formData)
    testResult.value = response
    console.log('Sandbox test result:', response)
    message.success('测试完成')
    resultTab.value = 'json'
  } catch (error) {
    testError.value = error.message || '测试失败'
    message.error('测试失败：' + testError.value)
  } finally {
    testing.value = false
  }
}

// 格式化JSON
const formatJson = (obj) => {
  return JSON.stringify(obj, null, 2)
}

// 复制JSON
const handleCopyJson = () => {
  const text = formatJson(testResult.value.extracted_data)
  navigator.clipboard.writeText(text)
  message.success('已复制到剪贴板')
}

// 复制文本
const handleCopyText = () => {
  navigator.clipboard.writeText(testResult.value.merged_text)
  message.success('已复制到剪贴板')
}

// 获取置信度颜色
const getConfidenceColor = (confidence) => {
  if (confidence >= 80) return '#52c41a'
  if (confidence >= 60) return '#faad14'
  return '#f5222d'
}

// 格式化处理时间
const formatDuration = (seconds) => {
  if (!seconds) return '0ms'
  if (seconds < 1) {
    return `${Math.round(seconds * 1000)}ms`
  }
  return `${seconds.toFixed(2)}s`
}

// 关闭面板
const handleClose = () => {
  emit('close')
}
</script>

<style scoped>
.sandbox-panel {
  background-color: white;
}

.result-container {
  max-height: 400px;
  overflow-y: auto;
}

.json-viewer,
.text-viewer {
  background-color: #f5f5f5;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  padding: 12px;
  font-size: 12px;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.json-viewer {
  color: #1890ff;
}

.text-viewer {
  color: #262626;
}
</style>
