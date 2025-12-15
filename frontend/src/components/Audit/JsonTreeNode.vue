<template>
  <div class="json-tree-node">
    <!-- 根节点或对象/数组 -->
    <template v-if="isExpandable">
      <div class="node-row" :class="{ 'is-root': isRoot }">
        <span class="expand-icon" @click="$emit('toggle-expand', path)">
          <CaretRightOutlined v-if="!isExpanded" />
          <CaretDownOutlined v-else />
        </span>
        <span v-if="!isRoot" class="node-key">{{ displayKey }}</span>
        <span v-if="!isRoot" class="colon">:</span>
        <span class="node-type">{{ typeLabel }}</span>
        <span class="node-count">({{ itemCount }})</span>
        <!-- 置信度 -->
        <span v-if="confidence !== undefined" class="confidence-indicator" :class="confidenceClass">
          {{ confidenceText }}
        </span>
        <span class="node-actions">
          <a-tooltip title="添加">
            <PlusOutlined class="action-icon" @click="showAddModal" />
          </a-tooltip>
          <a-tooltip v-if="!isRoot" title="删除">
            <DeleteOutlined class="action-icon danger" @click="$emit('delete-field', path)" />
          </a-tooltip>
        </span>
      </div>
      
      <!-- 子节点 -->
      <div v-if="isExpanded" class="node-children">
        <template v-if="isArray">
          <JsonTreeNode
            v-for="(item, index) in data"
            :key="index"
            :data="item"
            :path="[...path, index]"
            :field-key="index"
            :expanded-keys="expandedKeys"
            :confidence-scores="confidenceScores"
            @update="(p, v) => $emit('update', p, v)"
            @toggle-expand="(p) => $emit('toggle-expand', p)"
            @add-field="(p, k, v) => $emit('add-field', p, k, v)"
            @delete-field="(p) => $emit('delete-field', p)"
          />
        </template>
        <template v-else>
          <JsonTreeNode
            v-for="key in objectKeys"
            :key="key"
            :data="data[key]"
            :path="[...path, key]"
            :field-key="key"
            :expanded-keys="expandedKeys"
            :confidence-scores="confidenceScores"
            @update="(p, v) => $emit('update', p, v)"
            @toggle-expand="(p) => $emit('toggle-expand', p)"
            @add-field="(p, k, v) => $emit('add-field', p, k, v)"
            @delete-field="(p) => $emit('delete-field', p)"
          />
        </template>
      </div>
    </template>

    <!-- 叶子节点（基本类型） -->
    <template v-else>
      <div class="node-row leaf-node" :class="{ 'low-confidence': confidence !== undefined && confidence < 70 }">
        <span class="node-key">{{ displayKey }}</span>
        <span class="colon">:</span>
        <div class="node-value-editor">
          <!-- 字符串 -->
          <a-input
            v-if="valueType === 'string'"
            v-model:value="localValue"
            size="small"
            @change="onValueChange"
            @pressEnter="onValueChange"
          />
          <!-- 数字 -->
          <a-input-number
            v-else-if="valueType === 'number'"
            v-model:value="localValue"
            size="small"
            style="width: 100%"
            @change="onValueChange"
          />
          <!-- 布尔 -->
          <a-switch
            v-else-if="valueType === 'boolean'"
            v-model:checked="localValue"
            size="small"
            @change="onValueChange"
          />
          <!-- null -->
          <span v-else-if="valueType === 'null'" class="null-value">null</span>
        </div>
        <span class="value-type-tag" :class="valueType">{{ valueType }}</span>
        <!-- 置信度 -->
        <span v-if="confidence !== undefined" class="confidence-indicator" :class="confidenceClass">
          {{ confidenceText }}
        </span>
        <span class="node-actions">
          <a-tooltip title="删除">
            <DeleteOutlined class="action-icon danger" @click="$emit('delete-field', path)" />
          </a-tooltip>
        </span>
      </div>
    </template>

    <!-- 添加字段弹窗 -->
    <a-modal
      v-model:open="addModalVisible"
      title="添加字段"
      @ok="handleAddField"
      @cancel="addModalVisible = false"
      width="400px"
    >
      <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-form-item v-if="!isArray" label="字段名">
          <a-input v-model:value="newFieldKey" placeholder="请输入字段名" />
        </a-form-item>
        <a-form-item label="类型">
          <a-select v-model:value="newFieldType" style="width: 100%">
            <a-select-option value="string">字符串 (string)</a-select-option>
            <a-select-option value="number">数字 (number)</a-select-option>
            <a-select-option value="boolean">布尔 (boolean)</a-select-option>
            <a-select-option value="null">空值 (null)</a-select-option>
            <a-select-option value="object">对象 (object)</a-select-option>
            <a-select-option value="array">数组 (array)</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item v-if="newFieldType === 'string'" label="值">
          <a-input v-model:value="newFieldValue" placeholder="请输入值" />
        </a-form-item>
        <a-form-item v-else-if="newFieldType === 'number'" label="值">
          <a-input-number v-model:value="newFieldValue" style="width: 100%" />
        </a-form-item>
        <a-form-item v-else-if="newFieldType === 'boolean'" label="值">
          <a-switch v-model:checked="newFieldValue" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import {
  CaretRightOutlined,
  CaretDownOutlined,
  PlusOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'

/**
 * JSON 树节点组件（递归）
 * 支持任意嵌套的 JSON 数据结构
 */

const props = defineProps({
  data: {
    type: [Object, Array, String, Number, Boolean, null],
    default: null
  },
  path: {
    type: Array,
    default: () => []
  },
  fieldKey: {
    type: [String, Number],
    default: ''
  },
  expandedKeys: {
    type: Set,
    default: () => new Set()
  },
  confidenceScores: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update', 'toggle-expand', 'add-field', 'delete-field'])

// 本地值
const localValue = ref(props.data)

// 添加弹窗
const addModalVisible = ref(false)
const newFieldKey = ref('')
const newFieldType = ref('string')
const newFieldValue = ref('')

// 是否是根节点
const isRoot = computed(() => props.path.length === 0)

// 显示的 key
const displayKey = computed(() => {
  if (typeof props.fieldKey === 'number') {
    return `[${props.fieldKey}]`
  }
  return props.fieldKey
})

// 值类型
const valueType = computed(() => {
  if (props.data === null) return 'null'
  if (Array.isArray(props.data)) return 'array'
  return typeof props.data
})

// 是否可展开
const isExpandable = computed(() => {
  return valueType.value === 'object' || valueType.value === 'array'
})

// 是否是数组
const isArray = computed(() => Array.isArray(props.data))

// 对象的 keys
const objectKeys = computed(() => {
  if (typeof props.data === 'object' && props.data !== null && !Array.isArray(props.data)) {
    return Object.keys(props.data)
  }
  return []
})

// 类型标签
const typeLabel = computed(() => {
  if (isArray.value) return '[]'
  return '{}'
})

// 项目数量
const itemCount = computed(() => {
  if (isArray.value) return props.data.length
  if (typeof props.data === 'object' && props.data !== null) {
    return Object.keys(props.data).length
  }
  return 0
})

// 是否展开
const isExpanded = computed(() => {
  const key = props.path.join('.') || 'root'
  return props.expandedKeys.has(key)
})

// 置信度
const confidence = computed(() => {
  if (!props.confidenceScores) return undefined
  const key = props.path.join('.')
  return props.confidenceScores[key] ?? props.confidenceScores[props.fieldKey]
})

// 置信度文本
const confidenceText = computed(() => {
  if (confidence.value === undefined) return ''
  return `${confidence.value.toFixed(1)}%`
})

// 置信度样式类
const confidenceClass = computed(() => {
  if (confidence.value === undefined) return ''
  if (confidence.value >= 90) return 'high'
  if (confidence.value >= 70) return 'medium'
  return 'low'
})

// 值变化
function onValueChange() {
  emit('update', props.path, localValue.value)
}

// 显示添加弹窗
function showAddModal() {
  newFieldKey.value = ''
  newFieldType.value = 'string'
  newFieldValue.value = ''
  addModalVisible.value = true
}

// 处理添加字段
function handleAddField() {
  if (!isArray.value && !newFieldKey.value.trim()) {
    message.warning('请输入字段名')
    return
  }

  let value
  switch (newFieldType.value) {
    case 'string':
      value = newFieldValue.value || ''
      break
    case 'number':
      value = newFieldValue.value || 0
      break
    case 'boolean':
      value = newFieldValue.value || false
      break
    case 'null':
      value = null
      break
    case 'object':
      value = {}
      break
    case 'array':
      value = []
      break
  }

  emit('add-field', props.path, newFieldKey.value, value)
  addModalVisible.value = false
}

// 监听外部数据变化
watch(() => props.data, (newVal) => {
  localValue.value = newVal
})
</script>

<style scoped>
.json-tree-node {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
}

.node-row {
  display: flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 6px;
  gap: 6px;
  min-height: 36px;
  transition: background 0.15s;
}

.node-row:hover {
  background: #f0f5ff;
}

.node-row.is-root {
  padding-left: 4px;
}

.node-row.low-confidence {
  background: #fffbe6;
  border-left: 3px solid #faad14;
}

.expand-icon {
  cursor: pointer;
  color: #666;
  width: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.15s;
}

.expand-icon:hover {
  color: #1890ff;
}

.node-key {
  color: #9c27b0;
  font-weight: 500;
}

.colon {
  color: #666;
}

.node-type {
  color: #1890ff;
  font-size: 12px;
  font-weight: 500;
}

.node-count {
  color: #999;
  font-size: 11px;
}

.node-children {
  margin-left: 16px;
  padding-left: 12px;
  border-left: 1px dashed #d9d9d9;
}

.leaf-node {
  padding-left: 28px;
}

.node-value-editor {
  flex: 1;
  max-width: 320px;
}

.node-value-editor :deep(.ant-input) {
  font-family: inherit;
}

.value-type-tag {
  font-size: 10px;
  color: #fff;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.value-type-tag.string {
  background: #52c41a;
}

.value-type-tag.number {
  background: #1890ff;
}

.value-type-tag.boolean {
  background: #722ed1;
}

.value-type-tag.null {
  background: #999;
}

.null-value {
  color: #999;
  font-style: italic;
  padding: 4px 8px;
  background: #f5f5f5;
  border-radius: 4px;
}

.confidence-indicator {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.confidence-indicator.high {
  background: #f6ffed;
  color: #52c41a;
}

.confidence-indicator.medium {
  background: #fffbe6;
  color: #faad14;
}

.confidence-indicator.low {
  background: #fff2f0;
  color: #ff4d4f;
}

.node-actions {
  display: flex;
  gap: 6px;
  opacity: 0;
  transition: opacity 0.15s;
}

.node-row:hover .node-actions {
  opacity: 1;
}

.action-icon {
  cursor: pointer;
  color: #666;
  font-size: 12px;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.15s;
}

.action-icon:hover {
  color: #1890ff;
  background: #e6f7ff;
}

.action-icon.danger:hover {
  color: #ff4d4f;
  background: #fff2f0;
}
</style>
