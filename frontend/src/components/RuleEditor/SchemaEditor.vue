<template>
  <div class="schema-editor-container">
    <div class="flex justify-between items-center mb-4">
      <div>
        <h3 class="text-lg font-medium">Schema结构定义</h3>
        <p class="text-sm text-gray-500">定义目标JSON的数据结构和字段属性</p>
      </div>
      <a-space>
        <a-button @click="handleAddRootNode">
          <template #icon><PlusOutlined /></template>
          添加根节点
        </a-button>
        <a-button @click="handleImportJson">
          <template #icon><ImportOutlined /></template>
          导入JSON
        </a-button>
        <a-button @click="handleExportJson">
          <template #icon><ExportOutlined /></template>
          导出JSON
        </a-button>
      </a-space>
    </div>

    <!-- Schema树形结构 -->
    <div class="schema-tree-container bg-white border rounded-lg p-4">
      <a-tree
        v-if="treeData.length > 0"
        :tree-data="treeData"
        :show-line="true"
        :show-icon="true"
        :selectable="true"
        :draggable="true"
        @drop="handleDrop"
        @select="handleSelect"
      >
        <template #icon="{ dataRef }">
          <component :is="getNodeIcon(dataRef.nodeType)" />
        </template>

        <template #title="{ dataRef }">
          <div class="flex items-center justify-between group">
            <div class="flex items-center space-x-2">
              <span class="font-medium">{{ dataRef.label }}</span>
              <span class="text-gray-500 text-sm">({{ dataRef.key }})</span>
              <a-tag :color="getTypeColor(dataRef.type)" size="small">
                {{ getTypeLabel(dataRef.type) }}
              </a-tag>
              <a-tag v-if="dataRef.required" color="red" size="small">必填</a-tag>
            </div>
            <div class="opacity-0 group-hover:opacity-100 transition-opacity">
              <a-space size="small">
                <a-button
                  v-if="canAddChild(dataRef.nodeType)"
                  type="link"
                  size="small"
                  @click.stop="handleAddChild(dataRef)"
                >
                  <PlusOutlined />
                </a-button>
                <a-button
                  type="link"
                  size="small"
                  @click.stop="handleEdit(dataRef)"
                >
                  <EditOutlined />
                </a-button>
                <a-button
                  type="link"
                  size="small"
                  danger
                  @click.stop="handleDelete(dataRef)"
                >
                  <DeleteOutlined />
                </a-button>
              </a-space>
            </div>
          </div>
        </template>
      </a-tree>

      <a-empty v-else description="暂无Schema定义，请添加根节点" />
    </div>

    <!-- 节点编辑对话框 -->
    <a-modal
      v-model:open="editModalVisible"
      :title="editMode === 'add' ? '添加节点' : '编辑节点'"
      width="600px"
      @ok="handleEditSubmit"
      @cancel="handleEditCancel"
    >
      <a-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        layout="vertical"
      >
        <a-form-item label="节点类型" name="nodeType">
          <a-select
            v-model:value="editForm.nodeType"
            :disabled="editMode === 'edit'"
            @change="handleNodeTypeChange"
          >
            <a-select-option value="object">
              <FolderOutlined /> Object（对象）
            </a-select-option>
            <a-select-option value="array">
              <UnorderedListOutlined /> Array（数组）
            </a-select-option>
            <a-select-option value="table">
              <TableOutlined /> Table（明细表）
            </a-select-option>
            <a-select-option value="field">
              <FileTextOutlined /> Field（字段）
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="字段Key" name="key">
              <a-input
                v-model:value="editForm.key"
                placeholder="字段名称（英文）"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="显示名称" name="label">
              <a-input
                v-model:value="editForm.label"
                placeholder="字段显示名称"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item
          v-if="editForm.nodeType === 'field'"
          label="数据类型"
          name="type"
        >
          <a-select v-model:value="editForm.type">
            <a-select-option value="string">String（字符串）</a-select-option>
            <a-select-option value="int">Int（整数）</a-select-option>
            <a-select-option value="decimal">Decimal（小数）</a-select-option>
            <a-select-option value="date">Date（日期）</a-select-option>
            <a-select-option value="boolean">Boolean（布尔）</a-select-option>
          </a-select>
        </a-form-item>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="默认值" name="defaultValue">
              <a-input
                v-model:value="editForm.defaultValue"
                placeholder="字段默认值"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="置信度阈值" name="confidenceThreshold">
              <a-input-number
                v-model:value="editForm.confidenceThreshold"
                :min="0"
                :max="100"
                :step="5"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="字段属性">
          <a-checkbox v-model:checked="editForm.required">必填字段</a-checkbox>
        </a-form-item>

        <a-form-item label="描述" name="description">
          <a-textarea
            v-model:value="editForm.description"
            placeholder="字段说明"
            :rows="2"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- JSON导入对话框 -->
    <a-modal
      v-model:open="importModalVisible"
      title="导入JSON Schema"
      @ok="handleImportSubmit"
      @cancel="importModalVisible = false"
    >
      <a-textarea
        v-model:value="importJson"
        placeholder="粘贴JSON Schema"
        :rows="10"
      />
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ImportOutlined,
  ExportOutlined,
  FolderOutlined,
  UnorderedListOutlined,
  TableOutlined,
  FileTextOutlined
} from '@ant-design/icons-vue'

const props = defineProps({
  schema: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:schema'])

// 树形数据
const treeData = ref([])
const selectedNode = ref(null)
// 防止循环更新的标志
let isUpdatingFromProps = false
let isEmittingUpdate = false

// 编辑对话框
const editModalVisible = ref(false)
const editMode = ref('add') // 'add' or 'edit'
const editFormRef = ref()
const editForm = reactive({
  nodeType: 'field',
  key: '',
  label: '',
  type: 'string',
  defaultValue: '',
  confidenceThreshold: 80,
  required: false,
  description: ''
})

const editRules = {
  nodeType: [{ required: true, message: '请选择节点类型', trigger: 'change' }],
  key: [
    { required: true, message: '请输入字段Key', trigger: 'blur' },
    { pattern: /^[a-zA-Z_][a-zA-Z0-9_]*$/, message: 'Key只能包含字母、数字和下划线，且不能以数字开头', trigger: 'blur' }
  ],
  label: [{ required: true, message: '请输入显示名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择数据类型', trigger: 'change' }]
}

// JSON导入
const importModalVisible = ref(false)
const importJson = ref('')

// 将schema转换为树形数据
const schemaToTree = (schema, parentKey = '') => {
  const nodes = []
  
  for (const [key, value] of Object.entries(schema)) {
    const nodeKey = parentKey ? `${parentKey}.${key}` : key
    const node = {
      key: nodeKey,
      ...value,
      children: []
    }
    
    if (value.nodeType === 'object' && value.properties) {
      node.children = schemaToTree(value.properties, nodeKey)
    } else if (value.nodeType === 'array' && value.items) {
      node.children = schemaToTree(value.items, nodeKey)
    } else if (value.nodeType === 'table' && value.columns) {
      node.children = schemaToTree(value.columns, nodeKey)
    }
    
    nodes.push(node)
  }
  
  return nodes
}

// 将树形数据转换为schema
const treeToSchema = (nodes) => {
  const schema = {}
  
  for (const node of nodes) {
    const { key, children, ...rest } = node
    const fieldKey = key.split('.').pop()
    
    schema[fieldKey] = { ...rest }
    
    if (children && children.length > 0) {
      if (rest.nodeType === 'object') {
        schema[fieldKey].properties = treeToSchema(children)
      } else if (rest.nodeType === 'array') {
        schema[fieldKey].items = treeToSchema(children)
      } else if (rest.nodeType === 'table') {
        schema[fieldKey].columns = treeToSchema(children)
      }
    }
  }
  
  return schema
}

// 初始化树形数据（监听props.schema变化）
watch(
  () => props.schema,
  (newSchema) => {
    // 如果是自己emit导致的更新，跳过
    if (isEmittingUpdate) {
      return
    }
    if (newSchema && Object.keys(newSchema).length > 0) {
      isUpdatingFromProps = true
      treeData.value = schemaToTree(newSchema)
      console.log('SchemaEditor: Schema loaded from props:', newSchema)
      // 使用 nextTick 确保更新完成后再重置标志
      setTimeout(() => {
        isUpdatingFromProps = false
      }, 0)
    }
  },
  { immediate: true, deep: true }
)

// 同步树形数据到schema（使用防抖避免频繁更新）
let syncTimer = null
watch(
  treeData,
  (newTree) => {
    // 如果是从props更新来的，跳过emit
    if (isUpdatingFromProps) {
      return
    }
    if (syncTimer) clearTimeout(syncTimer)
    syncTimer = setTimeout(() => {
      isEmittingUpdate = true
      const newSchema = treeToSchema(newTree)
      console.log('SchemaEditor: Emitting schema update:', newSchema)
      emit('update:schema', newSchema)
      // 延迟重置标志，等待父组件更新完成
      setTimeout(() => {
        isEmittingUpdate = false
      }, 100)
    }, 300)
  },
  { deep: true }
)

// 添加根节点
const handleAddRootNode = () => {
  editMode.value = 'add'
  Object.assign(editForm, {
    nodeType: 'field',  // 默认为field类型
    key: '',
    label: '',
    type: 'string',
    defaultValue: '',
    confidenceThreshold: 80,
    required: false,
    description: ''
  })
  selectedNode.value = null
  editModalVisible.value = true
}

// 添加子节点
const handleAddChild = (node) => {
  editMode.value = 'add'
  Object.assign(editForm, {
    nodeType: 'field',
    key: '',
    label: '',
    type: 'string',
    defaultValue: '',
    confidenceThreshold: 80,
    required: false,
    description: ''
  })
  selectedNode.value = node
  editModalVisible.value = true
}

// 编辑节点
const handleEdit = (node) => {
  editMode.value = 'edit'
  Object.assign(editForm, {
    nodeType: node.nodeType,
    key: node.key.split('.').pop(),
    label: node.label,
    type: node.type || 'string',
    defaultValue: node.defaultValue || '',
    confidenceThreshold: node.confidenceThreshold || 80,
    required: node.required || false,
    description: node.description || ''
  })
  selectedNode.value = node
  editModalVisible.value = true
}

// 删除节点
const handleDelete = (node) => {
  const deleteFromTree = (nodes, targetKey) => {
    for (let i = 0; i < nodes.length; i++) {
      if (nodes[i].key === targetKey) {
        nodes.splice(i, 1)
        return true
      }
      if (nodes[i].children && deleteFromTree(nodes[i].children, targetKey)) {
        return true
      }
    }
    return false
  }
  
  deleteFromTree(treeData.value, node.key)
  message.success('节点已删除')
}

// 提交编辑
const handleEditSubmit = async () => {
  try {
    await editFormRef.value.validate()
    
    const newNode = {
      key: editForm.key,
      label: editForm.label,
      nodeType: editForm.nodeType,
      type: editForm.type,
      defaultValue: editForm.defaultValue,
      confidenceThreshold: editForm.confidenceThreshold,
      required: editForm.required,
      description: editForm.description,
      children: []
    }
    
    if (editMode.value === 'add') {
      if (selectedNode.value) {
        // 添加子节点
        newNode.key = `${selectedNode.value.key}.${editForm.key}`
        if (!selectedNode.value.children) {
          selectedNode.value.children = []
        }
        selectedNode.value.children.push(newNode)
      } else {
        // 添加根节点
        treeData.value.push(newNode)
      }
      message.success('节点添加成功')
    } else {
      // 编辑节点
      Object.assign(selectedNode.value, newNode)
      message.success('节点更新成功')
    }
    
    editModalVisible.value = false
  } catch (error) {
    // 表单验证失败
  }
}

// 取消编辑
const handleEditCancel = () => {
  editFormRef.value.resetFields()
  editModalVisible.value = false
}

// 节点类型变化
const handleNodeTypeChange = (type) => {
  if (type === 'field') {
    editForm.type = 'string'
  }
}

// 拖拽排序
const handleDrop = (info) => {
  const dropKey = info.node.key
  const dragKey = info.dragNode.key
  const dropPos = info.node.pos.split('-')
  const dropPosition = info.dropPosition - Number(dropPos[dropPos.length - 1])
  
  // 实现拖拽逻辑
  // 这里简化处理，实际需要更复杂的逻辑
  message.info('拖拽排序功能开发中')
}

// 选择节点
const handleSelect = (selectedKeys, info) => {
  if (selectedKeys.length > 0) {
    selectedNode.value = info.node.dataRef
  }
}

// 判断是否可以添加子节点
const canAddChild = (nodeType) => {
  return ['object', 'array', 'table'].includes(nodeType)
}

// 获取节点图标
const getNodeIcon = (nodeType) => {
  const icons = {
    object: FolderOutlined,
    array: UnorderedListOutlined,
    table: TableOutlined,
    field: FileTextOutlined
  }
  return icons[nodeType] || FileTextOutlined
}

// 获取类型颜色
const getTypeColor = (type) => {
  const colors = {
    string: 'blue',
    int: 'green',
    decimal: 'cyan',
    date: 'orange',
    boolean: 'purple'
  }
  return colors[type] || 'default'
}

// 获取类型标签
const getTypeLabel = (type) => {
  const labels = {
    string: 'String',
    int: 'Int',
    decimal: 'Decimal',
    date: 'Date',
    boolean: 'Boolean'
  }
  return labels[type] || type
}

// 导入JSON
const handleImportJson = () => {
  importModalVisible.value = true
}

// 提交导入
const handleImportSubmit = () => {
  try {
    const schema = JSON.parse(importJson.value)
    treeData.value = schemaToTree(schema)
    message.success('导入成功')
    importModalVisible.value = false
    importJson.value = ''
  } catch (error) {
    message.error('JSON格式错误：' + error.message)
  }
}

// 导出JSON
const handleExportJson = () => {
  const schema = treeToSchema(treeData.value)
  const dataStr = JSON.stringify(schema, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  const link = document.createElement('a')
  link.href = url
  link.download = `schema_${Date.now()}.json`
  link.click()
  URL.revokeObjectURL(url)
  message.success('导出成功')
}
</script>

<style scoped>
.schema-editor-container {
  max-width: 1200px;
}

.schema-tree-container {
  min-height: 400px;
}

:deep(.ant-tree-node-content-wrapper) {
  width: 100%;
}

:deep(.ant-tree-title) {
  width: 100%;
}
</style>
