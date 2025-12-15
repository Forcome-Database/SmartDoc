<template>
  <div class="extraction-config-container">
    <div class="mb-4">
      <h3 class="text-lg font-medium">提取策略配置</h3>
      <p class="text-sm text-gray-500">为每个字段配置数据提取方式（只有叶子节点可配置）</p>
    </div>

    <!-- 字段树形选择器 -->
    <div class="bg-white border rounded-lg p-4 mb-4">
      <div class="text-sm text-gray-600 mb-3">
        <span class="mr-4">图例：</span>
        <a-tag color="blue" size="small">字段</a-tag>
        <a-tag color="purple" size="small">对象</a-tag>
        <a-tag color="orange" size="small">数组</a-tag>
        <a-tag color="green" size="small">表格</a-tag>
        <span class="ml-4 text-green-600">✓ 已配置</span>
        <span class="ml-2 text-gray-400">○ 未配置</span>
      </div>
      
      <a-tree
        v-if="treeData.length > 0"
        :tree-data="treeData"
        :show-line="{ showLeafIcon: false }"
        :show-icon="true"
        :selectable="true"
        :selected-keys="selectedKeys"
        :default-expand-all="true"
        @select="handleTreeSelect"
      >
        <template #icon="{ dataRef }">
          <FolderOutlined v-if="dataRef.nodeType === 'object'" class="text-purple-500" />
          <UnorderedListOutlined v-else-if="dataRef.nodeType === 'array'" class="text-orange-500" />
          <TableOutlined v-else-if="dataRef.nodeType === 'table'" class="text-green-500" />
          <FileTextOutlined v-else class="text-blue-500" />
        </template>

        <template #title="{ dataRef }">
          <div class="flex items-center">
            <span :class="{ 'text-gray-400': !dataRef.canConfigure }">
              {{ dataRef.label }}
            </span>
            <a-tag 
              :color="getNodeTypeColor(dataRef.nodeType)" 
              size="small" 
              class="ml-2"
            >
              {{ getNodeTypeLabel(dataRef.nodeType) }}
            </a-tag>
            <!-- 配置状态指示 -->
            <span v-if="dataRef.canConfigure" class="ml-2">
              <CheckCircleFilled 
                v-if="isFieldConfigured(dataRef.key)" 
                class="text-green-500" 
              />
              <span v-else class="text-gray-300">○</span>
            </span>
            <!-- 不可配置提示 -->
            <a-tooltip v-if="!dataRef.canConfigure" title="有子节点的容器不能直接配置提取策略">
              <InfoCircleOutlined class="ml-2 text-gray-400" />
            </a-tooltip>
          </div>
        </template>
      </a-tree>

      <a-empty v-else description="请先在Schema定义中添加字段" />
    </div>

    <!-- 提取策略配置 -->
    <div v-if="selectedField && currentFieldConfig" class="bg-white border rounded-lg p-6">
      <div class="mb-6">
        <h4 class="text-base font-medium mb-2">
          {{ currentFieldConfig.label }}
          <a-tag :color="getNodeTypeColor(currentFieldConfig.nodeType)" class="ml-2">
            {{ getNodeTypeLabel(currentFieldConfig.nodeType) }}
          </a-tag>
          <a-tag color="blue" class="ml-1">{{ currentFieldConfig.key }}</a-tag>
        </h4>
        <p class="text-sm text-gray-500">{{ currentFieldConfig.description }}</p>
        <!-- 节点类型提示 -->
        <a-alert
          v-if="currentFieldConfig.nodeType === 'object'"
          type="warning"
          show-icon
          class="mt-2"
          message="对象类型只能使用LLM智能提取，可以一次性提取整个对象结构"
        />
        <a-alert
          v-if="currentFieldConfig.nodeType === 'array'"
          type="info"
          show-icon
          class="mt-2"
          message="数组类型（无子节点）推荐使用LLM智能提取，可以一次性提取所有数组元素"
        />
        <a-alert
          v-if="currentFieldConfig.nodeType === 'table'"
          type="info"
          show-icon
          class="mt-2"
          message="表格类型（无子节点）可以使用表格提取或LLM智能提取"
        />
      </div>

      <!-- 提取方式选择 -->
      <a-form :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="提取方式">
          <a-radio-group v-model:value="extractionRule.type">
            <a-space direction="vertical">
              <a-radio value="regex" :disabled="currentFieldConfig.nodeType === 'object'">
                <div>
                  <div class="font-medium">正则表达式</div>
                  <div class="text-xs text-gray-500">使用正则表达式从全文中匹配提取</div>
                </div>
              </a-radio>
              <a-radio value="anchor" :disabled="currentFieldConfig.nodeType === 'object'">
                <div>
                  <div class="font-medium">锚点定位</div>
                  <div class="text-xs text-gray-500">基于关键词的相对位置提取</div>
                </div>
              </a-radio>
              <a-radio value="table" :disabled="currentFieldConfig.nodeType === 'object'">
                <div>
                  <div class="font-medium">表格提取</div>
                  <div class="text-xs text-gray-500">从表格结构中提取数据</div>
                </div>
              </a-radio>
              <a-radio value="llm">
                <div>
                  <div class="font-medium">LLM智能提取</div>
                  <div class="text-xs text-gray-500">使用大语言模型智能理解和提取</div>
                </div>
              </a-radio>
            </a-space>
          </a-radio-group>
        </a-form-item>

        <!-- 正则表达式配置 -->
        <template v-if="extractionRule.type === 'regex'">
          <a-divider orientation="left">正则表达式配置</a-divider>
          
          <a-form-item label="正则表达式">
            <a-input
              v-model:value="extractionRule.pattern"
              placeholder="例如: 发票号：([\w]+)"
            />
            <div class="text-xs text-gray-500 mt-1">
              使用括号()捕获需要提取的内容
            </div>
          </a-form-item>

          <a-form-item label="匹配模式">
            <a-radio-group v-model:value="extractionRule.matchMode">
              <a-radio value="first">提取第一个匹配</a-radio>
              <a-radio value="all">提取所有匹配</a-radio>
            </a-radio-group>
          </a-form-item>

          <a-form-item label="捕获组">
            <a-input-number
              v-model:value="extractionRule.captureGroup"
              :min="0"
              :max="10"
              placeholder="默认为1"
            />
            <div class="text-xs text-gray-500 mt-1">
              指定要提取的捕获组编号，0表示整个匹配
            </div>
          </a-form-item>

          <a-form-item label="测试文本">
            <a-textarea
              v-model:value="testText"
              placeholder="输入测试文本"
              :rows="3"
            />
            <a-button class="mt-2" @click="handleTestRegex">测试正则</a-button>
            <div v-if="testResult" class="mt-2 p-2 bg-gray-50 rounded">
              <div class="text-sm font-medium">匹配结果：</div>
              <pre class="text-sm text-green-600 whitespace-pre-wrap">{{ testResult }}</pre>
            </div>
          </a-form-item>
        </template>

        <!-- 锚点定位配置 -->
        <template v-if="extractionRule.type === 'anchor'">
          <a-divider orientation="left">锚点定位配置</a-divider>
          
          <a-form-item label="锚点关键词">
            <a-input
              v-model:value="extractionRule.anchorKeyword"
              placeholder="例如: 发票号："
            />
            <div class="text-xs text-gray-500 mt-1">
              用于定位的关键词
            </div>
          </a-form-item>

          <a-form-item label="相对位置">
            <a-select v-model:value="extractionRule.relativePosition">
              <a-select-option value="right">右侧</a-select-option>
              <a-select-option value="below">下方</a-select-option>
              <a-select-option value="right_below">右下方</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="提取范围">
            <a-input-number
              v-model:value="extractionRule.maxDistance"
              :min="1"
              :max="1000"
              placeholder="最大字符数"
            />
            <span class="ml-2 text-gray-500">字符</span>
            <div class="text-xs text-gray-500 mt-1">
              从锚点位置开始提取的最大字符数
            </div>
          </a-form-item>

          <a-form-item label="结束标记">
            <a-input
              v-model:value="extractionRule.endMarker"
              placeholder="可选，例如: \n 或 ，"
            />
            <div class="text-xs text-gray-500 mt-1">
              遇到此标记时停止提取
            </div>
          </a-form-item>
        </template>

        <!-- 表格提取配置 -->
        <template v-if="extractionRule.type === 'table'">
          <a-divider orientation="left">表格提取配置</a-divider>
          
          <a-form-item label="表格识别">
            <a-radio-group v-model:value="extractionRule.tableMode">
              <a-radio value="auto">自动识别</a-radio>
              <a-radio value="header">基于表头</a-radio>
            </a-radio-group>
          </a-form-item>

          <a-form-item
            v-if="extractionRule.tableMode === 'header'"
            label="表头关键词"
          >
            <a-select
              v-model:value="extractionRule.headerKeywords"
              mode="tags"
              placeholder="输入表头关键词"
              style="width: 100%"
            />
            <div class="text-xs text-gray-500 mt-1">
              用于识别表格的表头关键词
            </div>
          </a-form-item>

          <a-form-item label="列映射">
            <a-button @click="handleAddColumnMapping">
              <template #icon><PlusOutlined /></template>
              添加列映射
            </a-button>
            <div class="mt-2 space-y-2">
              <div
                v-for="(mapping, index) in extractionRule.columnMappings"
                :key="index"
                class="flex items-center space-x-2"
              >
                <a-input
                  v-model:value="mapping.columnName"
                  placeholder="列名"
                  style="width: 200px"
                />
                <span>→</span>
                <a-input
                  v-model:value="mapping.fieldKey"
                  placeholder="字段Key"
                  style="width: 200px"
                />
                <a-button
                  type="link"
                  danger
                  @click="handleRemoveColumnMapping(index)"
                >
                  <DeleteOutlined />
                </a-button>
              </div>
            </div>
          </a-form-item>

          <a-form-item label="跨页合并">
            <a-checkbox v-model:checked="extractionRule.mergeCrossPage">
              启用跨页表格合并
            </a-checkbox>
            <div class="text-xs text-gray-500 mt-1">
              自动合并延伸到多页的表格
            </div>
          </a-form-item>
        </template>

        <!-- LLM提取配置 -->
        <template v-if="extractionRule.type === 'llm'">
          <a-divider orientation="left">LLM智能提取配置</a-divider>
          
          <a-form-item label="上下文范围">
            <a-select v-model:value="extractionRule.contextScope">
              <a-select-option value="all">全文</a-select-option>
              <a-select-option value="first_n_pages">前N页</a-select-option>
              <a-select-option value="region">指定区域</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item
            v-if="extractionRule.contextScope === 'first_n_pages'"
            label="页数"
          >
            <a-input-number
              v-model:value="extractionRule.pageCount"
              :min="1"
              :max="50"
            />
          </a-form-item>

          <a-form-item label="提示词模板">
            <a-textarea
              v-model:value="extractionRule.promptTemplate"
              :placeholder="getPromptPlaceholder()"
              :rows="6"
            />
            <div class="text-xs text-gray-500 mt-2 space-y-1">
              <div>💡 <strong>提示词书写说明：</strong></div>
              <div v-if="currentFieldConfig?.nodeType === 'field'">
                • 普通字段：描述如何查找内容，如 <code>从文本中提取"发票号："后面的内容</code>
              </div>
              <div v-else-if="currentFieldConfig?.nodeType === 'object'">
                • 对象类型：可在提示词中定义期望的JSON结构，系统会自动解析
              </div>
              <div v-else-if="currentFieldConfig?.nodeType === 'array'">
                • 数组类型：描述如何查找所有匹配项，如 <code>提取所有"画面："后面的描述</code>
              </div>
              <div class="text-blue-500">• 系统会自动根据Schema生成输出格式，无需重复定义</div>
            </div>
          </a-form-item>

          <a-form-item label="输出格式">
            <a-input
              v-model:value="extractionRule.outputFormat"
              placeholder="例如: JSON, 纯文本"
            />
          </a-form-item>

          <a-form-item label="最大Token数">
            <a-input-number
              v-model:value="extractionRule.maxTokens"
              :min="100"
              :max="1000000"
              :step="100"
            />
            <div class="text-xs text-gray-500 mt-1">
              限制单次LLM调用的最大Token数
            </div>
          </a-form-item>
        </template>

        <!-- 保存按钮 -->
        <a-form-item :wrapper-col="{ offset: 4, span: 18 }">
          <a-space>
            <a-button type="primary" @click="handleSaveRule">
              保存配置
            </a-button>
            <a-button @click="handleResetRule">
              重置
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </div>

    <!-- 未选择字段时的提示 -->
    <div v-else-if="treeData.length > 0" class="bg-white border rounded-lg p-6">
      <a-empty description="请在上方树形结构中选择要配置的字段" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  DeleteOutlined,
  FolderOutlined,
  UnorderedListOutlined,
  TableOutlined,
  FileTextOutlined,
  CheckCircleFilled,
  InfoCircleOutlined
} from '@ant-design/icons-vue'

const props = defineProps({
  config: {
    type: Object,
    default: () => ({})
  },
  schema: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:config'])

// 本地配置
const localConfig = ref({ ...props.config })

// 监听props.config变化，同步到localConfig
watch(
  () => props.config,
  (newConfig) => {
    if (newConfig && Object.keys(newConfig).length > 0) {
      localConfig.value = { ...newConfig }
    }
  },
  { immediate: true, deep: true }
)

// 选中的字段
const selectedField = ref('')
const selectedKeys = computed(() => selectedField.value ? [selectedField.value] : [])
const currentFieldConfig = ref(null)

// 提取规则
const extractionRule = reactive({
  type: 'regex',
  // 正则配置
  pattern: '',
  matchMode: 'first',
  captureGroup: 1,
  // 锚点配置
  anchorKeyword: '',
  relativePosition: 'right',
  maxDistance: 100,
  endMarker: '',
  // 表格配置
  tableMode: 'auto',
  headerKeywords: [],
  columnMappings: [],
  mergeCrossPage: true,
  // LLM配置
  contextScope: 'all',
  pageCount: 3,
  promptTemplate: '',
  outputFormat: 'JSON',
  maxTokens: 1000
})

// 测试文本和结果
const testText = ref('')
const testResult = ref('')

// 判断节点是否有子节点
const hasChildren = (value) => {
  if (!value) return false
  const nodeType = value.nodeType || 'field'
  if (nodeType === 'object' && value.properties && Object.keys(value.properties).length > 0) {
    return true
  }
  if (nodeType === 'array' && value.items && Object.keys(value.items).length > 0) {
    return true
  }
  if (nodeType === 'table' && value.columns && Object.keys(value.columns).length > 0) {
    return true
  }
  return false
}

// 将schema转换为树形数据
const treeData = computed(() => {
  const buildTree = (schema, prefix = '') => {
    if (!schema || typeof schema !== 'object') return []
    
    const nodes = []
    for (const [key, value] of Object.entries(schema)) {
      if (!value || typeof value !== 'object') continue
      
      const fullKey = prefix ? `${prefix}.${key}` : key
      const nodeType = value.nodeType || 'field'
      const nodeHasChildren = hasChildren(value)
      
      // 只有叶子节点（无子节点）才能配置提取策略
      const canConfigure = !nodeHasChildren
      
      const node = {
        key: fullKey,
        title: value.label || key,
        label: value.label || key,
        nodeType: nodeType,
        type: value.type || 'string',
        description: value.description || '',
        canConfigure: canConfigure,
        selectable: canConfigure, // 只有可配置的节点才能选中
        children: []
      }
      
      // 递归处理子节点
      if (nodeType === 'object' && value.properties) {
        node.children = buildTree(value.properties, fullKey)
      } else if (nodeType === 'array' && value.items) {
        node.children = buildTree(value.items, fullKey)
      } else if (nodeType === 'table' && value.columns) {
        node.children = buildTree(value.columns, fullKey)
      }
      
      nodes.push(node)
    }
    return nodes
  }
  
  return buildTree(props.schema)
})

// 扁平化的可配置字段列表（用于查找）
const configurableFields = computed(() => {
  const fields = []
  
  const flatten = (nodes) => {
    for (const node of nodes) {
      if (node.canConfigure) {
        fields.push({
          key: node.key,
          label: node.label,
          nodeType: node.nodeType,
          type: node.type,
          description: node.description
        })
      }
      if (node.children && node.children.length > 0) {
        flatten(node.children)
      }
    }
  }
  
  flatten(treeData.value)
  return fields
})

// 检查字段是否已配置
const isFieldConfigured = (fieldKey) => {
  return !!localConfig.value[fieldKey]
}

// 树形选择处理
const handleTreeSelect = (selectedKeysValue, { node }) => {
  if (!node.dataRef.canConfigure) {
    message.warning('有子节点的容器不能直接配置提取策略，请选择其子字段')
    return
  }
  
  selectedField.value = node.dataRef.key
  currentFieldConfig.value = {
    key: node.dataRef.key,
    label: node.dataRef.label,
    nodeType: node.dataRef.nodeType,
    type: node.dataRef.type,
    description: node.dataRef.description
  }
  
  // 加载该字段的提取规则
  if (localConfig.value[selectedField.value]) {
    Object.assign(extractionRule, localConfig.value[selectedField.value])
    // 如果是对象类型但之前配置的不是LLM，强制改为LLM
    if (node.dataRef.nodeType === 'object' && extractionRule.type !== 'llm') {
      extractionRule.type = 'llm'
      message.info('对象类型只能使用LLM智能提取')
    }
  } else {
    // 重置为默认值
    resetExtractionRule()
    // 如果是对象类型，默认使用LLM
    if (node.dataRef.nodeType === 'object') {
      extractionRule.type = 'llm'
    }
  }
}

// 重置提取规则为默认值
const resetExtractionRule = () => {
  Object.assign(extractionRule, {
    type: 'regex',
    pattern: '',
    matchMode: 'first',
    captureGroup: 1,
    anchorKeyword: '',
    relativePosition: 'right',
    maxDistance: 100,
    endMarker: '',
    tableMode: 'auto',
    headerKeywords: [],
    columnMappings: [],
    mergeCrossPage: true,
    contextScope: 'all',
    pageCount: 3,
    promptTemplate: '',
    outputFormat: 'JSON',
    maxTokens: 100000
  })
}

// 测试正则
const handleTestRegex = () => {
  if (!extractionRule.pattern || !testText.value) {
    message.warning('请输入正则表达式和测试文本')
    return
  }
  
  try {
    const regex = new RegExp(extractionRule.pattern, 'g')
    const groupIndex = extractionRule.captureGroup !== undefined ? extractionRule.captureGroup : 1
    
    if (extractionRule.matchMode === 'all') {
      const values = []
      let match
      regex.lastIndex = 0
      
      while ((match = regex.exec(testText.value)) !== null) {
        const value = match[groupIndex] !== undefined ? match[groupIndex] : match[0]
        values.push(value)
        if (match.index === regex.lastIndex) {
          regex.lastIndex++
        }
      }
      
      if (values.length > 0) {
        if (currentFieldConfig.value?.nodeType === 'array' || currentFieldConfig.value?.nodeType === 'table') {
          testResult.value = JSON.stringify(values, null, 2)
        } else {
          testResult.value = values.join(', ')
        }
      } else {
        testResult.value = '未匹配到内容'
      }
    } else {
      const match = regex.exec(testText.value)
      
      if (match) {
        const matchValue = match[groupIndex] !== undefined ? match[groupIndex] : match[0]
        if (currentFieldConfig.value?.nodeType === 'array' || currentFieldConfig.value?.nodeType === 'table') {
          testResult.value = JSON.stringify([matchValue], null, 2)
        } else {
          testResult.value = matchValue
        }
      } else {
        testResult.value = '未匹配到内容'
      }
    }
  } catch (error) {
    message.error('正则表达式错误：' + error.message)
  }
}

// 添加列映射
const handleAddColumnMapping = () => {
  extractionRule.columnMappings.push({
    columnName: '',
    fieldKey: ''
  })
}

// 删除列映射
const handleRemoveColumnMapping = (index) => {
  extractionRule.columnMappings.splice(index, 1)
}

// 保存规则
const handleSaveRule = () => {
  if (!selectedField.value) {
    message.warning('请先选择字段')
    return
  }
  
  localConfig.value[selectedField.value] = { ...extractionRule }
  emit('update:config', { ...localConfig.value })
  message.success('提取规则保存成功，请点击顶部"保存"按钮保存到服务器')
}

// 重置规则
const handleResetRule = () => {
  if (localConfig.value[selectedField.value]) {
    Object.assign(extractionRule, localConfig.value[selectedField.value])
  } else {
    resetExtractionRule()
  }
  message.info('已重置为上次保存的配置')
}

// 获取提示词输入框的placeholder
const getPromptPlaceholder = () => {
  const nodeType = currentFieldConfig.value?.nodeType
  const label = currentFieldConfig.value?.label || '字段'
  
  if (nodeType === 'object') {
    return `示例：请从文本中提取"${label}"内容，返回JSON格式：
{"key1":"描述1", "key2":"描述2", "key3":"描述3"}

说明：
• 描述如何查找内容
• 可定义期望的JSON结构（键名和说明）
• 系统会自动解析JSON结构生成输出格式`
  } else if (nodeType === 'array' || nodeType === 'table') {
    return `示例1（简单数组）：提取所有"${label}"项

示例2（对象数组）：提取所有"${label}"，返回JSON格式：
[{"scene":"场景名", "content":"内容"}]

说明：
• 简单数组：只描述如何查找，返回字符串数组
• 对象数组：用 [{"key":"说明"}] 格式定义每个元素的结构`
  } else {
    return `示例：从文本中提取"${label}："后面的内容

说明：
• 描述如何查找和提取内容
• 可使用关键词定位，如"发票号："、"金额："等`
  }
}

// 获取节点类型颜色
const getNodeTypeColor = (nodeType) => {
  const colors = {
    field: 'blue',
    object: 'purple',
    array: 'orange',
    table: 'green'
  }
  return colors[nodeType] || 'default'
}

// 获取节点类型标签
const getNodeTypeLabel = (nodeType) => {
  const labels = {
    field: '字段',
    object: '对象',
    array: '数组',
    table: '表格'
  }
  return labels[nodeType] || nodeType
}

// 监听配置变化
watch(
  () => props.config,
  (newConfig) => {
    if (newConfig && Object.keys(newConfig).length > 0) {
      localConfig.value = { ...newConfig }
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.extraction-config-container {
  max-width: 1200px;
}

:deep(.ant-tree-node-content-wrapper) {
  width: 100%;
}

:deep(.ant-tree-title) {
  width: 100%;
}

:deep(.ant-tree-node-selected) {
  background-color: #e6f7ff !important;
}
</style>
