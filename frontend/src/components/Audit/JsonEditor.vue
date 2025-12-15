<template>
  <div class="json-editor">
    <!-- 工具栏 -->
    <div class="editor-toolbar">
      <a-space>
        <a-radio-group v-model:value="viewMode" size="small" button-style="solid">
          <a-radio-button value="tree">
            <ApartmentOutlined /> 树形
          </a-radio-button>
          <a-radio-button value="code">
            <CodeOutlined /> 源码
          </a-radio-button>
        </a-radio-group>
      </a-space>
      <a-space>
        <a-button size="small" @click="expandAll" v-if="viewMode === 'tree'">
          <template #icon><ExpandOutlined /></template>
          展开全部
        </a-button>
        <a-button size="small" @click="collapseAll" v-if="viewMode === 'tree'">
          <template #icon><CompressOutlined /></template>
          折叠全部
        </a-button>
        <a-button size="small" @click="formatCode" v-if="viewMode === 'code'">
          <template #icon><FormatPainterOutlined /></template>
          格式化
        </a-button>
        <a-button size="small" @click="copyJson">
          <template #icon><CopyOutlined /></template>
          复制
        </a-button>
      </a-space>
    </div>

    <!-- 树形视图 -->
    <div v-show="viewMode === 'tree'" class="tree-view">
      <JsonTreeNode
        :data="localData"
        :path="[]"
        :expanded-keys="expandedKeys"
        :confidence-scores="confidenceScores"
        @update="onTreeUpdate"
        @toggle-expand="toggleExpand"
        @add-field="onAddField"
        @delete-field="onDeleteField"
      />
    </div>

    <!-- 源码视图 -->
    <div v-show="viewMode === 'code'" class="code-view">
      <div class="code-editor-wrapper">
        <div class="line-numbers">
          <div v-for="n in lineCount" :key="n" class="line-number">{{ n }}</div>
        </div>
        <textarea
          ref="codeTextarea"
          v-model="codeContent"
          class="code-textarea"
          :class="{ 'has-error': codeError }"
          spellcheck="false"
          @input="onCodeInput"
          @keydown="onCodeKeydown"
        />
      </div>
      <div v-if="codeError" class="code-error">
        <ExclamationCircleOutlined /> {{ codeError }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import {
  ApartmentOutlined,
  CodeOutlined,
  ExpandOutlined,
  CompressOutlined,
  FormatPainterOutlined,
  CopyOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons-vue'
import JsonTreeNode from './JsonTreeNode.vue'

/**
 * JSON 编辑器组件
 * 支持树形视图和源码视图两种模式
 * 适配所有 JSON 数据结构
 */

const props = defineProps({
  modelValue: {
    type: [Object, Array],
    default: () => ({})
  },
  confidenceScores: {
    type: Object,
    default: () => ({})
  },
  readonly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// 视图模式
const viewMode = ref('tree')

// 本地数据
const localData = ref(JSON.parse(JSON.stringify(props.modelValue || {})))

// 源码内容
const codeContent = ref('')

// 源码错误
const codeError = ref('')

// 展开的节点
const expandedKeys = ref(new Set())

// textarea 引用
const codeTextarea = ref(null)

// 行数
const lineCount = computed(() => {
  return codeContent.value.split('\n').length
})

// 初始化
function init() {
  localData.value = JSON.parse(JSON.stringify(props.modelValue || {}))
  codeContent.value = JSON.stringify(localData.value, null, 2)
  expandedKeys.value.clear()
  // 默认展开前两层
  initExpandedKeys(localData.value, [])
}

// 初始化展开的 key
function initExpandedKeys(data, path) {
  if (typeof data === 'object' && data !== null) {
    const key = path.join('.') || 'root'
    if (path.length < 2) {
      expandedKeys.value.add(key)
    }
    if (Array.isArray(data)) {
      data.forEach((item, index) => {
        initExpandedKeys(item, [...path, index])
      })
    } else {
      Object.keys(data).forEach(k => {
        initExpandedKeys(data[k], [...path, k])
      })
    }
  }
}

// 展开全部
function expandAll() {
  expandAllNodes(localData.value, [])
}

function expandAllNodes(data, path) {
  if (typeof data === 'object' && data !== null) {
    const key = path.join('.') || 'root'
    expandedKeys.value.add(key)
    if (Array.isArray(data)) {
      data.forEach((item, index) => {
        expandAllNodes(item, [...path, index])
      })
    } else {
      Object.keys(data).forEach(k => {
        expandAllNodes(data[k], [...path, k])
      })
    }
  }
}

// 折叠全部
function collapseAll() {
  expandedKeys.value.clear()
}

// 切换展开
function toggleExpand(path) {
  const key = path.join('.') || 'root'
  if (expandedKeys.value.has(key)) {
    expandedKeys.value.delete(key)
  } else {
    expandedKeys.value.add(key)
  }
}

// 格式化代码
function formatCode() {
  try {
    const parsed = JSON.parse(codeContent.value)
    codeContent.value = JSON.stringify(parsed, null, 2)
    codeError.value = ''
  } catch (e) {
    codeError.value = '无法格式化：JSON 格式错误'
  }
}

// 复制 JSON
async function copyJson() {
  try {
    const text = JSON.stringify(localData.value, null, 2)
    await navigator.clipboard.writeText(text)
    message.success('已复制到剪贴板')
  } catch (e) {
    message.error('复制失败')
  }
}

// 树形更新
function onTreeUpdate(path, value) {
  setValueByPath(localData.value, path, value)
  codeContent.value = JSON.stringify(localData.value, null, 2)
  emitChange()
}

// 添加字段
function onAddField(path, key, value) {
  const target = path.length === 0 ? localData.value : getValueByPath(localData.value, path)
  if (Array.isArray(target)) {
    target.push(value)
  } else if (typeof target === 'object' && target !== null) {
    target[key] = value
  }
  codeContent.value = JSON.stringify(localData.value, null, 2)
  emitChange()
}

// 删除字段
function onDeleteField(path) {
  if (path.length === 0) return
  const parentPath = path.slice(0, -1)
  const key = path[path.length - 1]
  const parent = parentPath.length === 0 ? localData.value : getValueByPath(localData.value, parentPath)
  if (Array.isArray(parent)) {
    parent.splice(key, 1)
  } else if (typeof parent === 'object' && parent !== null) {
    delete parent[key]
  }
  codeContent.value = JSON.stringify(localData.value, null, 2)
  emitChange()
}

// 源码输入
function onCodeInput() {
  try {
    const parsed = JSON.parse(codeContent.value)
    localData.value = parsed
    codeError.value = ''
    emitChange()
  } catch (e) {
    codeError.value = `JSON 解析错误: ${e.message}`
  }
}

// 源码键盘事件（Tab 缩进）
function onCodeKeydown(e) {
  if (e.key === 'Tab') {
    e.preventDefault()
    const textarea = codeTextarea.value
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    codeContent.value = codeContent.value.substring(0, start) + '  ' + codeContent.value.substring(end)
    nextTick(() => {
      textarea.selectionStart = textarea.selectionEnd = start + 2
    })
  }
}

// 根据路径获取值
function getValueByPath(obj, path) {
  let current = obj
  for (const key of path) {
    if (current === null || current === undefined) return undefined
    current = current[key]
  }
  return current
}

// 根据路径设置值
function setValueByPath(obj, path, value) {
  if (path.length === 0) return
  let current = obj
  for (let i = 0; i < path.length - 1; i++) {
    current = current[path[i]]
  }
  current[path[path.length - 1]] = value
}

// 发送变化
function emitChange() {
  emit('update:modelValue', localData.value)
  emit('change', localData.value)
}

// 监听外部数据变化
watch(() => props.modelValue, (newVal) => {
  if (JSON.stringify(newVal) !== JSON.stringify(localData.value)) {
    init()
  }
}, { deep: true })

// 初始化
init()
</script>

<style scoped>
.json-editor {
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
  flex-shrink: 0;
}

.tree-view {
  flex: 1;
  padding: 12px;
  overflow: auto;
  background: #fff;
}

.code-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  overflow: hidden;
}

.code-editor-wrapper {
  flex: 1;
  display: flex;
  overflow: auto;
}

.line-numbers {
  padding: 12px 8px;
  background: #252526;
  color: #858585;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  text-align: right;
  user-select: none;
  min-width: 40px;
  flex-shrink: 0;
}

.line-number {
  height: 20.8px;
}

.code-textarea {
  flex: 1;
  padding: 12px;
  border: none;
  outline: none;
  resize: none;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.code-textarea.has-error {
  background: #2d1f1f;
}

.code-error {
  padding: 8px 12px;
  background: #5c2121;
  color: #f48771;
  font-size: 12px;
  flex-shrink: 0;
}
</style>
