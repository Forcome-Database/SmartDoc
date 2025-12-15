<template>
  <div class="table-editor">
    <a-table
      :columns="tableColumns"
      :data-source="tableData"
      :pagination="false"
      size="small"
      bordered
      :scroll="{ x: 'max-content' }"
    >
      <!-- 自定义单元格渲染 -->
      <template
        v-for="col in editableColumns"
        :key="col.dataIndex"
        #[`bodyCell`]="{ column, record, index }"
      >
        <template v-if="column.dataIndex === col.dataIndex">
          <a-input
            v-if="col.type === 'string'"
            v-model:value="record[col.dataIndex]"
            size="small"
            @change="onCellChange(index)"
            @focus="onRowFocus(record, index)"
          />
          <a-input-number
            v-else-if="col.type === 'number'"
            v-model:value="record[col.dataIndex]"
            size="small"
            style="width: 100%"
            @change="onCellChange(index)"
            @focus="onRowFocus(record, index)"
          />
        </template>
      </template>

      <!-- 操作列 -->
      <template #bodyCell="{ column, record, index }">
        <template v-if="column.dataIndex === 'actions'">
          <a-space size="small">
            <a-button
              type="link"
              size="small"
              :disabled="index === 0"
              @click="moveUp(index)"
            >
              <template #icon><ArrowUpOutlined /></template>
            </a-button>
            <a-button
              type="link"
              size="small"
              :disabled="index === tableData.length - 1"
              @click="moveDown(index)"
            >
              <template #icon><ArrowDownOutlined /></template>
            </a-button>
            <a-button
              type="link"
              size="small"
              danger
              @click="deleteRow(index)"
            >
              <template #icon><DeleteOutlined /></template>
            </a-button>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 添加行按钮 -->
    <a-button
      type="dashed"
      block
      class="mt-2"
      @click="addRow"
    >
      <template #icon><PlusOutlined /></template>
      添加行
    </a-button>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import {
  PlusOutlined,
  DeleteOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined
} from '@ant-design/icons-vue'

/**
 * 表格编辑器组件
 * 支持插入行、删除行、上移、下移操作
 */

const props = defineProps({
  // 表格数据
  value: {
    type: Array,
    default: () => []
  },
  // 列配置
  columns: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['update:value', 'change', 'row-focus'])

// 表格数据
const tableData = ref([...props.value])

// 表格列配置
const tableColumns = computed(() => {
  const cols = props.columns.map(col => ({
    title: col.label || col.key,
    dataIndex: col.key,
    key: col.key,
    width: col.width || 150,
    ellipsis: true
  }))

  // 添加操作列
  cols.push({
    title: '操作',
    dataIndex: 'actions',
    key: 'actions',
    width: 150,
    fixed: 'right'
  })

  return cols
})

// 可编辑列
const editableColumns = computed(() => {
  return props.columns.map(col => ({
    dataIndex: col.key,
    type: col.type || 'string'
  }))
})

/**
 * 添加行
 */
function addRow() {
  const newRow = {}
  props.columns.forEach(col => {
    newRow[col.key] = col.default || ''
  })
  tableData.value.push(newRow)
  emitChange()
}

/**
 * 删除行
 */
function deleteRow(index) {
  tableData.value.splice(index, 1)
  emitChange()
}

/**
 * 上移
 */
function moveUp(index) {
  if (index > 0) {
    const temp = tableData.value[index]
    tableData.value[index] = tableData.value[index - 1]
    tableData.value[index - 1] = temp
    emitChange()
  }
}

/**
 * 下移
 */
function moveDown(index) {
  if (index < tableData.value.length - 1) {
    const temp = tableData.value[index]
    tableData.value[index] = tableData.value[index + 1]
    tableData.value[index + 1] = temp
    emitChange()
  }
}

/**
 * 单元格变化
 */
function onCellChange(index) {
  emitChange()
}

/**
 * 行获得焦点
 */
function onRowFocus(record, index) {
  emit('row-focus', { record, index })
}

/**
 * 发送变化事件
 */
function emitChange() {
  emit('update:value', tableData.value)
  emit('change', tableData.value)
}

// 监听外部数据变化
watch(() => props.value, (newValue) => {
  tableData.value = [...newValue]
}, { deep: true })
</script>

<style scoped>
.table-editor {
  width: 100%;
}

.mt-2 {
  margin-top: 8px;
}

:deep(.ant-table-cell) {
  padding: 8px !important;
}

:deep(.ant-input),
:deep(.ant-input-number) {
  font-size: 12px;
}
</style>
