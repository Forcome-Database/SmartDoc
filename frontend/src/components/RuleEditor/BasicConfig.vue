<template>
  <div class="basic-config-container">
    <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 14 }">
      <!-- OCR引擎配置 -->
      <a-divider orientation="left">OCR引擎配置</a-divider>
      
      <a-form-item label="OCR引擎">
        <a-select v-model:value="localConfig.ocrEngine" placeholder="选择OCR引擎">
          <a-select-option value="paddleocr">
            <div class="flex items-center">
              <span class="font-medium">PaddleOCR</span>
              <a-tag color="blue" class="ml-2">推荐</a-tag>
            </div>
            <div class="text-xs text-gray-500">百度开源OCR，中文识别效果好</div>
          </a-select-option>
          <a-select-option value="tesseract">
            <div class="flex items-center">
              <span class="font-medium">Tesseract</span>
            </div>
            <div class="text-xs text-gray-500">开源OCR引擎，支持多语言</div>
          </a-select-option>
          <a-select-option value="umiocr">
            <div class="flex items-center">
              <span class="font-medium">UmiOCR</span>
              <a-tag color="green" class="ml-2">离线</a-tag>
            </div>
            <div class="text-xs text-gray-500">开源离线OCR服务，支持多语言</div>
          </a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="语言配置">
        <a-select v-model:value="localConfig.language" placeholder="选择识别语言">
          <a-select-option value="zh">中文</a-select-option>
          <a-select-option value="en">英文</a-select-option>
          <a-select-option value="zh_en">中英混排</a-select-option>
        </a-select>
      </a-form-item>

      <!-- 页面处理策略 -->
      <a-divider orientation="left">页面处理策略</a-divider>

      <a-form-item label="处理模式">
        <a-radio-group v-model:value="localConfig.pageStrategy">
          <a-space direction="vertical">
            <a-radio value="single_page">
              <div>
                <div class="font-medium">单页模式</div>
                <div class="text-xs text-gray-500">仅处理PDF的第一页</div>
              </div>
            </a-radio>
            <a-radio value="multi_page">
              <div>
                <div class="font-medium">多页合并模式</div>
                <div class="text-xs text-gray-500">处理所有页面并按顺序合并OCR结果</div>
              </div>
            </a-radio>
            <a-radio value="specified_pages">
              <div>
                <div class="font-medium">指定页码</div>
                <div class="text-xs text-gray-500">自定义处理的页码范围</div>
              </div>
            </a-radio>
          </a-space>
        </a-radio-group>
      </a-form-item>

      <a-form-item
        v-if="localConfig.pageStrategy === 'specified_pages'"
        label="页码范围"
      >
        <a-input
          v-model:value="localConfig.pageRange"
          placeholder="例如: 1-3 或 1,3,5 或 Last Page"
        />
        <div class="text-xs text-gray-500 mt-1">
          支持格式：1-3（范围）、1,3,5（指定页）、Last Page（最后一页）
        </div>
      </a-form-item>

      <a-form-item label="页面分隔符">
        <a-select v-model:value="localConfig.pageSeparator" placeholder="选择分隔符">
          <a-select-option value="\n">
            <div>
              <div class="font-medium">单换行符 (\n)</div>
              <div class="text-xs text-gray-500">默认选项，适合大多数场景</div>
            </div>
          </a-select-option>
          <a-select-option value="\n\n">
            <div>
              <div class="font-medium">双换行符 (\n\n)</div>
              <div class="text-xs text-gray-500">页面间增加空行，便于区分</div>
            </div>
          </a-select-option>
          <a-select-option value="custom">
            <div>
              <div class="font-medium">自定义</div>
              <div class="text-xs text-gray-500">输入自定义分隔符</div>
            </div>
          </a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item
        v-if="localConfig.pageSeparator === 'custom'"
        label="自定义分隔符"
      >
        <a-input
          v-model:value="localConfig.customSeparator"
          placeholder="输入自定义分隔符"
        />
      </a-form-item>

      <!-- OCR参数配置 -->
      <a-divider orientation="left">OCR参数配置</a-divider>

      <a-form-item label="超时时间">
        <a-input-number
          v-model:value="localConfig.ocrTimeout"
          :min="10"
          :max="600"
          :step="10"
          style="width: 200px"
        />
        <span class="ml-2 text-gray-500">秒</span>
        <div class="text-xs text-gray-500 mt-1">
          单个文档的最大处理时间，默认300秒
        </div>
      </a-form-item>

      <a-form-item label="最大并行数">
        <a-input-number
          v-model:value="localConfig.maxParallel"
          :min="1"
          :max="10"
          :step="1"
          style="width: 200px"
        />
        <span class="ml-2 text-gray-500">页</span>
        <div class="text-xs text-gray-500 mt-1">
          多页文档并行处理的最大页数，默认4页
        </div>
      </a-form-item>

      <a-form-item label="图片DPI">
        <a-select v-model:value="localConfig.imageDpi" style="width: 200px">
          <a-select-option :value="150">150 DPI（快速）</a-select-option>
          <a-select-option :value="300">300 DPI（标准）</a-select-option>
          <a-select-option :value="600">600 DPI（高清）</a-select-option>
        </a-select>
        <div class="text-xs text-gray-500 mt-1">
          PDF转图片的分辨率，越高识别越准确但速度越慢
        </div>
      </a-form-item>

      <!-- 预览区域 -->
      <a-divider orientation="left">配置预览</a-divider>

      <a-form-item label="配置摘要">
        <a-card size="small" class="bg-gray-50">
          <div class="space-y-2 text-sm">
            <div>
              <span class="text-gray-600">OCR引擎：</span>
              <span class="font-medium">{{ getOcrEngineLabel(localConfig.ocrEngine) }}</span>
            </div>
            <div>
              <span class="text-gray-600">识别语言：</span>
              <span class="font-medium">{{ getLanguageLabel(localConfig.language) }}</span>
            </div>
            <div>
              <span class="text-gray-600">处理模式：</span>
              <span class="font-medium">{{ getPageStrategyLabel(localConfig.pageStrategy) }}</span>
            </div>
            <div v-if="localConfig.pageStrategy === 'specified_pages'">
              <span class="text-gray-600">页码范围：</span>
              <span class="font-medium">{{ localConfig.pageRange || '未设置' }}</span>
            </div>
            <div>
              <span class="text-gray-600">页面分隔符：</span>
              <span class="font-medium">{{ getSeparatorLabel(localConfig.pageSeparator) }}</span>
            </div>
          </div>
        </a-card>
      </a-form-item>
    </a-form>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  config: {
    type: Object,
    default: () => ({
      ocrEngine: 'paddleocr',
      language: 'zh',
      pageStrategy: 'multi_page',
      pageSeparator: '\n',
      customSeparator: '',
      pageRange: '',
      ocrTimeout: 300,
      maxParallel: 4,
      imageDpi: 300
    })
  }
})

const emit = defineEmits(['update:config'])

// 本地配置副本
const localConfig = ref({
  ocrEngine: 'paddleocr',
  language: 'zh',
  pageStrategy: 'multi_page',
  pageSeparator: '\n',
  customSeparator: '',
  pageRange: '',
  ocrTimeout: 300,
  maxParallel: 4,
  imageDpi: 300,
  ...props.config
})

// 监听props.config的变化，同步到localConfig
watch(
  () => props.config,
  (newConfig) => {
    if (newConfig) {
      Object.assign(localConfig.value, newConfig)
      console.log('BasicConfig: Config updated from props:', localConfig.value)
    }
  },
  { deep: true, immediate: false }
)

// 使用防抖的方式更新父组件
let updateTimer = null
watch(
  localConfig,
  (newVal) => {
    if (updateTimer) clearTimeout(updateTimer)
    updateTimer = setTimeout(() => {
      emit('update:config', { ...newVal })
    }, 300)
  },
  { deep: true }
)

// 获取OCR引擎标签
const getOcrEngineLabel = (engine) => {
  const labels = {
    paddleocr: 'PaddleOCR',
    tesseract: 'Tesseract',
    umiocr: 'UmiOCR'
  }
  return labels[engine] || engine
}

// 获取语言标签
const getLanguageLabel = (lang) => {
  const labels = {
    zh: '中文',
    en: '英文',
    zh_en: '中英混排'
  }
  return labels[lang] || lang
}

// 获取页面策略标签
const getPageStrategyLabel = (strategy) => {
  const labels = {
    single_page: '单页模式',
    multi_page: '多页合并模式',
    specified_pages: '指定页码'
  }
  return labels[strategy] || strategy
}

// 获取分隔符标签
const getSeparatorLabel = (separator) => {
  if (separator === '\n') return '单换行符'
  if (separator === '\n\n') return '双换行符'
  if (separator === 'custom') return localConfig.value.customSeparator || '自定义'
  return separator
}

onMounted(() => {
  // 确保配置有默认值
  if (!localConfig.value.ocrTimeout) {
    localConfig.value.ocrTimeout = 300
  }
  if (!localConfig.value.maxParallel) {
    localConfig.value.maxParallel = 4
  }
  if (!localConfig.value.imageDpi) {
    localConfig.value.imageDpi = 300
  }
})
</script>

<style scoped>
.basic-config-container {
  max-width: 900px;
}

:deep(.ant-select-item-option-content) {
  display: block;
}
</style>
