<template>
  <div class="enhancement-config-container">
    <div class="mb-4">
      <h3 class="text-lg font-medium">增强风控配置</h3>
      <p class="text-sm text-gray-500">配置自动增强、一致性校验和成本熔断策略</p>
    </div>

    <div class="space-y-6">
      <!-- 自动增强配置 -->
      <div class="bg-white border rounded-lg p-6">
        <h4 class="text-base font-medium mb-4">自动增强</h4>
        
        <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
          <a-form-item label="启用自动增强">
            <a-switch v-model:checked="localConfig.autoEnhancement.enabled" />
            <div class="text-xs text-gray-500 mt-1">
              当OCR结果为空或质量低时，自动使用备用策略
            </div>
          </a-form-item>

          <template v-if="localConfig.autoEnhancement.enabled">
            <a-divider />

            <a-form-item label="备用OCR引擎">
              <a-checkbox-group v-model:value="localConfig.autoEnhancement.fallbackEngines">
                <a-space direction="vertical">
                  <a-checkbox value="tesseract">
                    Tesseract
                    <span class="text-xs text-gray-500 ml-2">开源OCR引擎</span>
                  </a-checkbox>
                  <a-checkbox value="umiocr">
                    UmiOCR
                    <span class="text-xs text-gray-500 ml-2">开源离线OCR服务</span>
                  </a-checkbox>
                </a-space>
              </a-checkbox-group>
              <div class="text-xs text-gray-500 mt-1">
                当主引擎识别结果为空时，按顺序尝试备用引擎
              </div>
            </a-form-item>

            <a-form-item label="LLM补全">
              <a-switch v-model:checked="localConfig.autoEnhancement.llmCompletion" />
              <div class="text-xs text-gray-500 mt-1">
                使用LLM对低置信度字段进行智能补全
              </div>
            </a-form-item>

            <a-form-item
              v-if="localConfig.autoEnhancement.llmCompletion"
              label="触发阈值"
            >
              <a-input-number
                v-model:value="localConfig.autoEnhancement.llmThreshold"
                :min="0"
                :max="100"
                :step="5"
              />
              <span class="ml-2 text-gray-500">%</span>
              <div class="text-xs text-gray-500 mt-1">
                当字段置信度低于此阈值时触发LLM补全
              </div>
            </a-form-item>

            <a-form-item label="重试次数">
              <a-input-number
                v-model:value="localConfig.autoEnhancement.maxRetries"
                :min="1"
                :max="5"
              />
              <div class="text-xs text-gray-500 mt-1">
                备用引擎的最大重试次数
              </div>
            </a-form-item>
          </template>
        </a-form>
      </div>

      <!-- 一致性校验配置 -->
      <div class="bg-white border rounded-lg p-6">
        <h4 class="text-base font-medium mb-4">一致性校验</h4>
        
        <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
          <a-form-item label="启用一致性校验">
            <a-switch v-model:checked="localConfig.consistencyCheck.enabled" />
            <div class="text-xs text-gray-500 mt-1">
              同时运行OCR和LLM提取，对比结果差异
            </div>
          </a-form-item>

          <template v-if="localConfig.consistencyCheck.enabled">
            <a-divider />

            <a-form-item label="校验模式">
              <a-radio-group v-model:value="localConfig.consistencyCheck.mode">
                <a-space direction="vertical">
                  <a-radio value="all_fields">
                    <div>
                      <div class="font-medium">全字段校验</div>
                      <div class="text-xs text-gray-500">对所有字段进行一致性校验</div>
                    </div>
                  </a-radio>
                  <a-radio value="key_fields">
                    <div>
                      <div class="font-medium">关键字段校验</div>
                      <div class="text-xs text-gray-500">仅对指定的关键字段进行校验</div>
                    </div>
                  </a-radio>
                </a-space>
              </a-radio-group>
            </a-form-item>

            <a-form-item
              v-if="localConfig.consistencyCheck.mode === 'key_fields'"
              label="关键字段"
            >
              <a-select
                v-model:value="localConfig.consistencyCheck.keyFields"
                mode="tags"
                placeholder="选择或输入关键字段"
                style="width: 100%"
              />
              <div class="text-xs text-gray-500 mt-1">
                输入字段Key，多个字段用回车分隔
              </div>
            </a-form-item>

            <a-form-item label="相似度算法">
              <a-select v-model:value="localConfig.consistencyCheck.algorithm">
                <a-select-option value="edit_distance">
                  编辑距离（Levenshtein）
                </a-select-option>
                <a-select-option value="cosine">
                  余弦相似度
                </a-select-option>
                <a-select-option value="jaccard">
                  Jaccard相似度
                </a-select-option>
              </a-select>
            </a-form-item>

            <a-form-item label="差异阈值">
              <a-input-number
                v-model:value="localConfig.consistencyCheck.threshold"
                :min="0"
                :max="100"
                :step="5"
              />
              <span class="ml-2 text-gray-500">%</span>
              <div class="text-xs text-gray-500 mt-1">
                当相似度低于此阈值时，标记为不一致并转人工审核
              </div>
            </a-form-item>

            <a-form-item label="处理策略">
              <a-radio-group v-model:value="localConfig.consistencyCheck.strategy">
                <a-space direction="vertical">
                  <a-radio value="manual_review">
                    <div>
                      <div class="font-medium">转人工审核</div>
                      <div class="text-xs text-gray-500">发现不一致时强制人工审核</div>
                    </div>
                  </a-radio>
                  <a-radio value="use_llm">
                    <div>
                      <div class="font-medium">优先使用LLM结果</div>
                      <div class="text-xs text-gray-500">自动采用LLM提取结果</div>
                    </div>
                  </a-radio>
                  <a-radio value="use_ocr">
                    <div>
                      <div class="font-medium">优先使用OCR结果</div>
                      <div class="text-xs text-gray-500">自动采用OCR提取结果</div>
                    </div>
                  </a-radio>
                </a-space>
              </a-radio-group>
            </a-form-item>
          </template>
        </a-form>
      </div>

      <!-- 成本熔断配置 -->
      <div class="bg-white border rounded-lg p-6">
        <h4 class="text-base font-medium mb-4">成本熔断</h4>
        
        <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
          <a-form-item label="启用成本熔断">
            <a-switch v-model:checked="localConfig.circuitBreaker.enabled" />
            <div class="text-xs text-gray-500 mt-1">
              当LLM服务异常或成本超标时自动降级
            </div>
          </a-form-item>

          <template v-if="localConfig.circuitBreaker.enabled">
            <a-divider />

            <a-form-item label="Token限制">
              <a-input-number
                v-model:value="localConfig.circuitBreaker.maxTokens"
                :min="100"
                :max="10000"
                :step="100"
              />
              <span class="ml-2 text-gray-500">Tokens</span>
              <div class="text-xs text-gray-500 mt-1">
                单次任务的最大Token消耗限制
              </div>
            </a-form-item>

            <a-form-item label="超时时间">
              <a-input-number
                v-model:value="localConfig.circuitBreaker.timeout"
                :min="10"
                :max="300"
                :step="10"
              />
              <span class="ml-2 text-gray-500">秒</span>
              <div class="text-xs text-gray-500 mt-1">
                LLM接口的最大响应时间
              </div>
            </a-form-item>

            <a-form-item label="失败阈值">
              <a-input-number
                v-model:value="localConfig.circuitBreaker.failureThreshold"
                :min="1"
                :max="10"
              />
              <span class="ml-2 text-gray-500">次</span>
              <div class="text-xs text-gray-500 mt-1">
                连续失败多少次后触发熔断
              </div>
            </a-form-item>

            <a-form-item label="恢复时间">
              <a-input-number
                v-model:value="localConfig.circuitBreaker.recoveryTimeout"
                :min="60"
                :max="3600"
                :step="60"
              />
              <span class="ml-2 text-gray-500">秒</span>
              <div class="text-xs text-gray-500 mt-1">
                熔断后多久尝试恢复服务
              </div>
            </a-form-item>

            <a-form-item label="降级策略">
              <a-radio-group v-model:value="localConfig.circuitBreaker.fallbackStrategy">
                <a-space direction="vertical">
                  <a-radio value="ocr_only">
                    <div>
                      <div class="font-medium">纯OCR模式</div>
                      <div class="text-xs text-gray-500">仅使用OCR提取，不调用LLM</div>
                    </div>
                  </a-radio>
                  <a-radio value="manual_review">
                    <div>
                      <div class="font-medium">转人工审核</div>
                      <div class="text-xs text-gray-500">所有任务转入人工审核队列</div>
                    </div>
                  </a-radio>
                  <a-radio value="queue">
                    <div>
                      <div class="font-medium">延迟处理</div>
                      <div class="text-xs text-gray-500">任务进入等待队列，服务恢复后处理</div>
                    </div>
                  </a-radio>
                </a-space>
              </a-radio-group>
            </a-form-item>

            <a-form-item label="告警通知">
              <a-checkbox v-model:checked="localConfig.circuitBreaker.alertEnabled">
                启用告警通知
              </a-checkbox>
              <div class="text-xs text-gray-500 mt-1">
                熔断触发时发送通知给管理员
              </div>
            </a-form-item>
          </template>
        </a-form>
      </div>

      <!-- 配置摘要 -->
      <div class="bg-white border rounded-lg p-6">
        <h4 class="text-base font-medium mb-4">配置摘要</h4>
        
        <a-descriptions bordered size="small" :column="1">
          <a-descriptions-item label="自动增强">
            <a-tag :color="localConfig.autoEnhancement.enabled ? 'green' : 'default'">
              {{ localConfig.autoEnhancement.enabled ? '已启用' : '未启用' }}
            </a-tag>
            <span v-if="localConfig.autoEnhancement.enabled" class="ml-2 text-sm text-gray-600">
              备用引擎: {{ (localConfig.autoEnhancement.fallbackEngines || []).join(', ') || '无' }}
            </span>
          </a-descriptions-item>
          
          <a-descriptions-item label="一致性校验">
            <a-tag :color="localConfig.consistencyCheck.enabled ? 'green' : 'default'">
              {{ localConfig.consistencyCheck.enabled ? '已启用' : '未启用' }}
            </a-tag>
            <span v-if="localConfig.consistencyCheck.enabled" class="ml-2 text-sm text-gray-600">
              阈值: {{ localConfig.consistencyCheck.threshold }}%
            </span>
          </a-descriptions-item>
          
          <a-descriptions-item label="成本熔断">
            <a-tag :color="localConfig.circuitBreaker.enabled ? 'green' : 'default'">
              {{ localConfig.circuitBreaker.enabled ? '已启用' : '未启用' }}
            </a-tag>
            <span v-if="localConfig.circuitBreaker.enabled" class="ml-2 text-sm text-gray-600">
              Token限制: {{ localConfig.circuitBreaker.maxTokens }}
            </span>
          </a-descriptions-item>
        </a-descriptions>
      </div>

      <!-- 保存按钮 -->
      <div class="flex justify-end">
        <a-button type="primary" size="large" @click="handleSave">
          保存配置
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { message } from 'ant-design-vue'

const props = defineProps({
  config: {
    type: Object,
    default: () => ({
      autoEnhancement: {
        enabled: false,
        fallbackEngines: [],
        llmCompletion: false,
        llmThreshold: 60,
        maxRetries: 2
      },
      consistencyCheck: {
        enabled: false,
        mode: 'all_fields',
        keyFields: [],
        algorithm: 'edit_distance',
        threshold: 80,
        strategy: 'manual_review'
      },
      circuitBreaker: {
        enabled: false,
        maxTokens: 2000,
        timeout: 60,
        failureThreshold: 5,
        recoveryTimeout: 300,
        fallbackStrategy: 'ocr_only',
        alertEnabled: true
      }
    })
  }
})

const emit = defineEmits(['update:config'])

// 默认配置
const defaultConfig = {
  autoEnhancement: {
    enabled: false,
    fallbackEngines: [],
    llmCompletion: false,
    llmThreshold: 60,
    maxRetries: 2
  },
  consistencyCheck: {
    enabled: false,
    mode: 'all_fields',
    keyFields: [],
    algorithm: 'edit_distance',
    threshold: 80,
    strategy: 'manual_review'
  },
  circuitBreaker: {
    enabled: false,
    maxTokens: 2000,
    timeout: 60,
    failureThreshold: 5,
    recoveryTimeout: 300,
    fallbackStrategy: 'ocr_only',
    alertEnabled: true
  }
}

// 本地配置（合并默认值，防止undefined）
const localConfig = ref({
  autoEnhancement: { ...defaultConfig.autoEnhancement, ...props.config?.autoEnhancement },
  consistencyCheck: { ...defaultConfig.consistencyCheck, ...props.config?.consistencyCheck },
  circuitBreaker: { ...defaultConfig.circuitBreaker, ...props.config?.circuitBreaker }
})

// 保存配置
const handleSave = () => {
  emit('update:config', { ...localConfig.value })
  message.success('增强风控配置保存成功')
}

// 监听配置变化
watch(
  () => props.config,
  (newConfig) => {
    if (newConfig && Object.keys(newConfig).length > 0) {
      localConfig.value = {
        autoEnhancement: { ...defaultConfig.autoEnhancement, ...newConfig.autoEnhancement },
        consistencyCheck: { ...defaultConfig.consistencyCheck, ...newConfig.consistencyCheck },
        circuitBreaker: { ...defaultConfig.circuitBreaker, ...newConfig.circuitBreaker }
      }
      console.log('EnhancementConfig: Config loaded from props:', localConfig.value)
    }
  },
  { immediate: true, deep: true }
)
</script>

<style scoped>
.enhancement-config-container {
  max-width: 1000px;
}
</style>
