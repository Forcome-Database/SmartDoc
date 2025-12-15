<template>
  <div class="data-form">
    <!-- 表单头部 -->
    <div class="form-header">
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

    <!-- 表单内容 -->
    <a-form
      ref="formRef"
      :model="formData"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 18 }"
      class="audit-form"
    >
      <template v-for="field in fields" :key="field.key">
        <!-- 普通字段（排除 table、array、object 类型） -->
        <a-form-item
          v-if="field.type !== 'table' && field.type !== 'array' && field.type !== 'object'"
          :label="field.label"
          :name="field.key"
        >
          <template #label>
            <span>{{ field.label }}</span>
            <!-- 置信度徽章 -->
            <ConfidenceBadge
              v-if="field.confidence !== undefined"
              :score="field.confidence"
              class="ml-2"
            />
            <!-- 来源页码 -->
            <a-tag
              v-if="field.sourcePage"
              size="small"
              color="blue"
              class="ml-2 cursor-pointer"
              @click="jumpToPage(field.sourcePage)"
            >
              P{{ field.sourcePage }}
            </a-tag>
          </template>

          <!-- 根据字段类型渲染不同的输入控件 -->
          <component
            :is="getFieldComponent(field.type)"
            v-model:value="formData[field.key]"
            :placeholder="`请输入${field.label}`"
            @change="onFieldChange(field.key)"
            @focus="onFieldFocus(field)"
            v-bind="getFieldProps(field)"
          />
        </a-form-item>

        <!-- 表格字段 -->
        <a-form-item
          v-else-if="field.type === 'table'"
          :label="field.label"
          :name="field.key"
          class="table-field"
        >
          <template #label>
            <span>{{ field.label }}</span>
            <ConfidenceBadge
              v-if="field.confidence !== undefined"
              :score="field.confidence"
              class="ml-2"
            />
          </template>

          <TableEditor
            v-model:value="formData[field.key]"
            :columns="field.columns"
            @change="onFieldChange(field.key)"
            @row-focus="onRowFocus(field, $event)"
          />
        </a-form-item>

        <!-- 数组字段 -->
        <a-form-item
          v-else-if="field.type === 'array'"
          :label="field.label"
          :name="field.key"
        >
          <template #label>
            <span>{{ field.label }}</span>
            <ConfidenceBadge
              v-if="field.confidence !== undefined"
              :score="field.confidence"
              class="ml-2"
            />
          </template>

          <ArrayEditor
            v-model:value="formData[field.key]"
            :item-schema="field.itemSchema"
            @change="onFieldChange(field.key)"
          />
        </a-form-item>

        <!-- 对象字段（显示为 JSON） -->
        <a-form-item
          v-else-if="field.type === 'object'"
          :label="field.label"
          :name="field.key"
        >
          <template #label>
            <span>{{ field.label }}</span>
            <ConfidenceBadge
              v-if="field.confidence !== undefined"
              :score="field.confidence"
              class="ml-2"
            />
          </template>

          <a-textarea
            :value="formatObjectValue(formData[field.key])"
            :rows="4"
            :placeholder="`请输入${field.label}（JSON格式）`"
            @change="(e) => onObjectFieldChange(field.key, e.target.value)"
          />
        </a-form-item>
      </template>
    </a-form>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { EditOutlined, CheckOutlined } from '@ant-design/icons-vue'
import ConfidenceBadge from '../Task/ConfidenceBadge.vue'
import TableEditor from './TableEditor.vue'
import ArrayEditor from './ArrayEditor.vue'

/**
 * 数据表单组件
 * 根据Schema动态生成表单，支持字段编辑和置信度显示
 */

const props = defineProps({
  // 表单数据
  modelValue: {
    type: Object,
    required: true
  },
  // 字段配置（可选，如果没有则从数据自动生成）
  schema: {
    type: Object,
    default: () => ({})
  },
  // 置信度数据
  confidenceScores: {
    type: Object,
    default: () => ({})
  },
  // 来源页码数据
  sourcePages: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'field-focus', 'jump-to-page', 'change'])

// 表单引用
const formRef = ref(null)

// 表单数据
const formData = ref({ ...props.modelValue })

// 是否有修改
const hasChanges = ref(false)

// 草稿是否已保存
const draftSaved = ref(false)

// 字段列表
const fields = computed(() => {
  // 如果有 schema，使用 schema 生成字段
  if (props.schema && Object.keys(props.schema).length > 0) {
    return parseSchema(props.schema, props.confidenceScores, props.sourcePages)
  }
  
  // 如果没有 schema，从 modelValue（extracted_data）动态生成字段
  return generateFieldsFromData(props.modelValue, props.confidenceScores, props.sourcePages)
})

/**
 * 解析Schema生成字段列表
 */
function parseSchema(schema, confidenceScores, sourcePages, prefix = '') {
  const result = []

  for (const [key, config] of Object.entries(schema)) {
    const fullKey = prefix ? `${prefix}.${key}` : key
    
    const field = {
      key: fullKey,
      label: config.label || key,
      type: config.type || 'string',
      required: config.required || false,
      confidence: confidenceScores[fullKey],
      sourcePage: sourcePages[fullKey],
      ...config
    }

    result.push(field)

    // 递归处理嵌套对象
    if (config.type === 'object' && config.properties) {
      result.push(...parseSchema(config.properties, confidenceScores, sourcePages, fullKey))
    }
  }

  return result
}

/**
 * 从数据动态生成字段列表（当没有schema时使用）
 */
function generateFieldsFromData(data, confidenceScores, sourcePages, prefix = '') {
  const result = []
  
  if (!data || typeof data !== 'object') {
    return result
  }

  for (const [key, value] of Object.entries(data)) {
    const fullKey = prefix ? `${prefix}.${key}` : key
    
    // 根据值类型推断字段类型
    let fieldType = 'string'
    if (typeof value === 'number') {
      fieldType = Number.isInteger(value) ? 'int' : 'decimal'
    } else if (typeof value === 'boolean') {
      fieldType = 'boolean'
    } else if (Array.isArray(value)) {
      // 如果是数组且元素是对象，使用table类型
      if (value.length > 0 && typeof value[0] === 'object') {
        fieldType = 'table'
      } else {
        fieldType = 'array'
      }
    } else if (value !== null && typeof value === 'object') {
      fieldType = 'object'
    } else if (typeof value === 'string' && value.length > 100) {
      fieldType = 'textarea'
    }
    
    const field = {
      key: fullKey,
      label: key,
      type: fieldType,
      required: false,
      confidence: confidenceScores ? confidenceScores[fullKey] : undefined,
      sourcePage: sourcePages ? sourcePages[fullKey] : undefined
    }
    
    // 如果是表格类型，生成列配置
    if (fieldType === 'table' && Array.isArray(value) && value.length > 0) {
      const firstRow = value[0]
      field.columns = Object.keys(firstRow).map(colKey => ({
        key: colKey,
        title: colKey,
        dataIndex: colKey
      }))
    }
    
    // 如果是数组类型，生成 itemSchema
    if (fieldType === 'array') {
      // 根据数组第一个元素推断类型
      if (value.length > 0) {
        const firstItem = value[0]
        if (typeof firstItem === 'number') {
          field.itemSchema = { type: 'number' }
        } else if (typeof firstItem === 'string') {
          field.itemSchema = { type: 'string' }
        } else {
          field.itemSchema = { type: 'string' }
        }
      } else {
        field.itemSchema = { type: 'string' }
      }
    }

    result.push(field)
  }

  return result
}

/**
 * 获取字段组件
 */
function getFieldComponent(type) {
  const componentMap = {
    string: 'a-input',
    int: 'a-input-number',
    decimal: 'a-input-number',
    date: 'a-date-picker',
    boolean: 'a-switch',
    textarea: 'a-textarea'
  }

  return componentMap[type] || 'a-input'
}

/**
 * 获取字段属性
 */
function getFieldProps(field) {
  const props = {}

  switch (field.type) {
    case 'int':
      props.precision = 0
      break
    case 'decimal':
      props.precision = field.precision || 2
      props.step = 0.01
      break
    case 'date':
      props.format = 'YYYY-MM-DD'
      props.valueFormat = 'YYYY-MM-DD'
      break
    case 'textarea':
      props.rows = 4
      break
  }

  if (field.min !== undefined) props.min = field.min
  if (field.max !== undefined) props.max = field.max
  if (field.disabled) props.disabled = true

  return props
}

/**
 * 格式化对象值为 JSON 字符串
 */
function formatObjectValue(value) {
  if (value === null || value === undefined) {
    return ''
  }
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value, null, 2)
    } catch {
      return String(value)
    }
  }
  return String(value)
}

/**
 * 对象字段值变化
 */
function onObjectFieldChange(key, value) {
  try {
    formData.value[key] = JSON.parse(value)
  } catch {
    // 如果不是有效的 JSON，保存为字符串
    formData.value[key] = value
  }
  onFieldChange(key)
}

/**
 * 字段值变化
 */
function onFieldChange(key) {
  hasChanges.value = true
  draftSaved.value = false
  emit('update:modelValue', formData.value)
  emit('change', { key, value: formData.value[key] })
}

/**
 * 字段获得焦点
 */
function onFieldFocus(field) {
  emit('field-focus', {
    key: field.key,
    label: field.label,
    sourcePage: field.sourcePage
  })
}

/**
 * 表格行获得焦点
 */
function onRowFocus(field, rowData) {
  emit('field-focus', {
    key: field.key,
    label: field.label,
    sourcePage: rowData.sourcePage || field.sourcePage
  })
}

/**
 * 跳转到页面
 */
function jumpToPage(page) {
  emit('jump-to-page', page)
}

/**
 * 设置字段值（用于划词回填）
 */
function setFieldValue(key, value) {
  formData.value[key] = value
  onFieldChange(key)
}

/**
 * 标记草稿已保存
 */
function markDraftSaved() {
  draftSaved.value = true
}

/**
 * 重置修改标记
 */
function resetChanges() {
  hasChanges.value = false
}

/**
 * 验证表单
 */
async function validate() {
  try {
    await formRef.value.validate()
    return true
  } catch (error) {
    return false
  }
}

// 监听外部数据变化
watch(() => props.modelValue, (newValue) => {
  formData.value = { ...newValue }
}, { deep: true })

// 暴露方法给父组件
defineExpose({
  setFieldValue,
  markDraftSaved,
  resetChanges,
  validate,
  formData
})
</script>

<style scoped>
.data-form {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
}

.form-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.audit-form {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.ml-2 {
  margin-left: 8px;
}

.cursor-pointer {
  cursor: pointer;
}

.cursor-pointer:hover {
  opacity: 0.8;
}

.table-field :deep(.ant-form-item-control-input) {
  min-height: auto;
}

/* 响应式 */
@media (max-width: 768px) {
  .audit-form :deep(.ant-form-item) {
    flex-direction: column;
  }

  .audit-form :deep(.ant-form-item-label) {
    text-align: left;
    padding-bottom: 8px;
  }

  .audit-form :deep(.ant-form-item-control) {
    max-width: 100%;
  }
}
</style>
