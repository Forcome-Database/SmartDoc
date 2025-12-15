<template>
  <div class="data-form-v2">
    <!-- 表单头部 -->
    <div class="form-header">
      <div class="header-left">
        <h3>提取结果</h3>
        <a-space>
          <a-tag v-if="hasChanges" color="orange">
            <template #icon><EditOutlined /></template>
            已修改
          </a-tag>
          <a-tag v-if="draftSaved" color="green">
            <template #icon><CheckOutlined /></template>
            草稿已保存
          </a-tag>
        </a-space>
      </div>
      <div class="header-right">
        <a-tooltip title="支持任意 JSON 数据结构的编辑">
          <InfoCircleOutlined style="color: #999; cursor: help;" />
        </a-tooltip>
      </div>
    </div>

    <!-- JSON 编辑器 -->
    <div class="editor-content">
      <JsonEditor
        v-if="hasData"
        v-model="formData"
        :confidence-scores="confidenceScores"
        @change="onDataChange"
      />
      <a-empty v-else description="暂无提取数据" class="empty-state" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import {
  EditOutlined,
  CheckOutlined,
  InfoCircleOutlined
} from '@ant-design/icons-vue'
import JsonEditor from './JsonEditor.vue'

/**
 * 数据表单组件 V2
 * 使用统一的 JsonEditor 处理所有数据结构
 */

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  schema: {
    type: Object,
    default: () => ({})
  },
  confidenceScores: {
    type: Object,
    default: () => ({})
  },
  sourcePages: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'field-focus', 'jump-to-page', 'change'])

// 表单数据
const formData = ref({ ...props.modelValue })

// 是否有修改
const hasChanges = ref(false)

// 草稿是否已保存
const draftSaved = ref(false)

// 是否有数据
const hasData = computed(() => {
  return formData.value && Object.keys(formData.value).length > 0
})

/**
 * 格式化审核原因
 */
function formatReason(reason) {
  if (!reason) return '-'
  if (typeof reason === 'string') return reason
  if (typeof reason === 'object') {
    if (reason.message) {
      return reason.field ? `${reason.field}: ${reason.message}` : reason.message
    }
    if (reason.reason) return reason.reason
    if (reason.type === 'validation_error') return `校验失败: ${reason.field || '未知字段'}`
    if (reason.type === 'confidence_low') return `置信度低: ${reason.field || '未知字段'}`
    return JSON.stringify(reason)
  }
  return String(reason)
}

/**
 * 数据变化
 */
function onDataChange() {
  hasChanges.value = true
  draftSaved.value = false
  emit('update:modelValue', formData.value)
  emit('change', { key: null, value: formData.value })
}

/**
 * 标记草稿已保存
 */
function markDraftSaved() {
  draftSaved.value = true
}

/**
 * 验证表单（JSON 编辑器始终有效）
 */
async function validate() {
  return true
}

// 监听外部数据变化
watch(() => props.modelValue, (newValue) => {
  if (JSON.stringify(newValue) !== JSON.stringify(formData.value)) {
    formData.value = { ...newValue }
  }
}, { deep: true })

// 暴露方法
defineExpose({
  markDraftSaved,
  validate,
  formData
})
</script>

<style scoped>
.data-form-v2 {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.form-header {
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.audit-reasons-section {
  margin: 12px 16px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #fffbe6 0%, #fff7e6 100%);
  border: 1px solid #ffe58f;
  border-radius: 8px;
  flex-shrink: 0;
}

.reasons-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #d48806;
  margin-bottom: 10px;
}

.warning-icon {
  font-size: 16px;
}

.reasons-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.reason-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: #8c6d1f;
}

.reason-bullet {
  width: 18px;
  height: 18px;
  background: #faad14;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

.reason-text {
  line-height: 1.5;
}

.editor-content {
  flex: 1;
  overflow: hidden;
  padding: 0 16px 16px;
}

.empty-state {
  padding: 48px 0;
}
</style>
