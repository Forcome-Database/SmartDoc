<template>
  <div class="array-editor">
    <a-list
      :data-source="items"
      size="small"
      bordered
    >
      <template #renderItem="{ item, index }">
        <a-list-item>
          <template #actions>
            <a-button
              type="link"
              size="small"
              danger
              @click="removeItem(index)"
            >
              <template #icon><DeleteOutlined /></template>
            </a-button>
          </template>

          <div class="array-item">
            <component
              :is="getComponent(itemSchema?.type)"
              v-model:value="items[index]"
              :placeholder="`项目 ${index + 1}`"
              @change="onItemChange"
              v-bind="getProps(itemSchema || {})"
            />
          </div>
        </a-list-item>
      </template>
    </a-list>

    <a-button
      type="dashed"
      block
      class="mt-2"
      @click="addItem"
    >
      <template #icon><PlusOutlined /></template>
      添加项目
    </a-button>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons-vue'

/**
 * 数组编辑器组件
 * 支持添加、删除数组项
 */

const props = defineProps({
  // 数组数据
  value: {
    type: Array,
    default: () => []
  },
  // 数组项Schema
  itemSchema: {
    type: Object,
    default: () => ({ type: 'string' })
  }
})

const emit = defineEmits(['update:value', 'change'])

// 数组项
const items = ref([...props.value])

/**
 * 获取组件类型
 */
function getComponent(type) {
  const componentMap = {
    string: 'a-input',
    number: 'a-input-number',
    date: 'a-date-picker'
  }
  return componentMap[type] || 'a-input'
}

/**
 * 获取组件属性
 */
function getProps(schema) {
  const result = {}
  if (!schema) return result
  
  if (schema.type === 'number') {
    result.style = { width: '100%' }
  }
  
  if (schema.type === 'date') {
    result.format = 'YYYY-MM-DD'
    result.valueFormat = 'YYYY-MM-DD'
  }

  return result
}

/**
 * 添加项目
 */
function addItem() {
  const defaultValue = props.itemSchema?.default || ''
  items.value.push(defaultValue)
  emitChange()
}

/**
 * 删除项目
 */
function removeItem(index) {
  items.value.splice(index, 1)
  emitChange()
}

/**
 * 项目变化
 */
function onItemChange() {
  emitChange()
}

/**
 * 发送变化事件
 */
function emitChange() {
  emit('update:value', items.value)
  emit('change', items.value)
}

// 监听外部数据变化
watch(() => props.value, (newValue) => {
  items.value = [...newValue]
}, { deep: true })
</script>

<style scoped>
.array-editor {
  width: 100%;
}

.array-item {
  flex: 1;
}

.mt-2 {
  margin-top: 8px;
}
</style>
