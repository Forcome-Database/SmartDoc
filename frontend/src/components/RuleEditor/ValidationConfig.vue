<template>
  <div class="validation-config-container">
    <div class="mb-4">
      <h3 class="text-lg font-medium">清洗校验配置</h3>
      <p class="text-sm text-gray-500">配置数据清洗管道和校验规则</p>
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
            <span>{{ dataRef.label }}</span>
            <a-tag 
              :color="getNodeTypeColor(dataRef.nodeType)" 
              size="small" 
              class="ml-2"
            >
              {{ getNodeTypeLabel(dataRef.nodeType) }}
            </a-tag>
            <!-- 配置状态指示 -->
            <span class="ml-2">
              <CheckCircleFilled 
                v-if="isFieldConfigured(dataRef.key)" 
                class="text-green-500" 
              />
              <span v-else class="text-gray-300">○</span>
            </span>
          </div>
        </template>
      </a-tree>

      <a-empty v-else description="请先在Schema定义中添加字段" />
    </div>

    <!-- 配置内容 -->
    <div v-if="selectedField && currentFieldConfig" class="space-y-6">
      <!-- 当前字段信息 -->
      <div class="bg-white border rounded-lg p-4">
        <h4 class="text-base font-medium mb-2">
          {{ currentFieldConfig.label }}
          <a-tag :color="getNodeTypeColor(currentFieldConfig.nodeType)" class="ml-2">
            {{ getNodeTypeLabel(currentFieldConfig.nodeType) }}
          </a-tag>
          <a-tag color="blue" class="ml-1">{{ currentFieldConfig.key }}</a-tag>
        </h4>
        <p v-if="currentFieldConfig.description" class="text-sm text-gray-500">
          {{ currentFieldConfig.description }}
        </p>
      </div>

      <!-- 数据清洗管道（仅对普通字段显示） -->
      <div v-if="currentFieldConfig?.nodeType === 'field'" class="bg-white border rounded-lg p-6">
        <div class="flex justify-between items-center mb-4">
          <h4 class="text-base font-medium">数据清洗管道</h4>
          <a-button @click="handleAddCleaningRule">
            <template #icon><PlusOutlined /></template>
            添加清洗规则
          </a-button>
        </div>

        <div v-if="cleaningRules.length > 0" class="space-y-3">
          <div
            v-for="(rule, index) in cleaningRules"
            :key="index"
            class="border rounded p-4"
          >
            <div class="flex justify-between items-start mb-3">
              <a-tag color="blue">步骤 {{ index + 1 }}</a-tag>
              <a-button
                type="link"
                danger
                size="small"
                @click="handleRemoveCleaningRule(index)"
              >
                <DeleteOutlined /> 删除
              </a-button>
            </div>

            <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
              <a-form-item label="清洗类型">
                <a-select v-model:value="rule.type">
                  <a-select-option value="regex_replace">正则替换</a-select-option>
                  <a-select-option value="trim">去除空格</a-select-option>
                  <a-select-option value="date_format">日期格式化</a-select-option>
                  <a-select-option value="number_format">数字格式化</a-select-option>
                  <a-select-option value="case_convert">大小写转换</a-select-option>
                </a-select>
              </a-form-item>

              <!-- 正则替换配置 -->
              <template v-if="rule.type === 'regex_replace'">
                <a-form-item label="匹配模式">
                  <a-input v-model:value="rule.pattern" placeholder="正则表达式" />
                </a-form-item>
                <a-form-item label="替换为">
                  <a-input v-model:value="rule.replacement" placeholder="替换内容" />
                </a-form-item>
              </template>

              <!-- 去除空格配置 -->
              <template v-if="rule.type === 'trim'">
                <a-form-item label="去除位置">
                  <a-select v-model:value="rule.trimMode">
                    <a-select-option value="both">两端</a-select-option>
                    <a-select-option value="left">左侧</a-select-option>
                    <a-select-option value="right">右侧</a-select-option>
                    <a-select-option value="all">全部</a-select-option>
                  </a-select>
                </a-form-item>
              </template>

              <!-- 日期格式化配置 -->
              <template v-if="rule.type === 'date_format'">
                <a-form-item label="输入格式">
                  <a-select v-model:value="rule.inputFormat" mode="tags" placeholder="支持的输入格式">
                    <a-select-option value="YYYY-MM-DD">YYYY-MM-DD</a-select-option>
                    <a-select-option value="YYYY/MM/DD">YYYY/MM/DD</a-select-option>
                    <a-select-option value="DD-MM-YYYY">DD-MM-YYYY</a-select-option>
                    <a-select-option value="YYYY年MM月DD日">YYYY年MM月DD日</a-select-option>
                  </a-select>
                </a-form-item>
                <a-form-item label="输出格式">
                  <a-input v-model:value="rule.outputFormat" placeholder="例如: YYYY-MM-DD" />
                </a-form-item>
              </template>

              <!-- 数字格式化配置 -->
              <template v-if="rule.type === 'number_format'">
                <a-form-item label="小数位数">
                  <a-input-number v-model:value="rule.decimalPlaces" :min="0" :max="10" />
                </a-form-item>
                <a-form-item label="千分位">
                  <a-checkbox v-model:checked="rule.useThousandSeparator">使用千分位分隔符</a-checkbox>
                </a-form-item>
              </template>

              <!-- 大小写转换配置 -->
              <template v-if="rule.type === 'case_convert'">
                <a-form-item label="转换方式">
                  <a-select v-model:value="rule.caseMode">
                    <a-select-option value="upper">全部大写</a-select-option>
                    <a-select-option value="lower">全部小写</a-select-option>
                    <a-select-option value="title">首字母大写</a-select-option>
                  </a-select>
                </a-form-item>
              </template>
            </a-form>
          </div>
        </div>

        <a-empty v-else description="暂无清洗规则" />
      </div>

      <!-- 对象/数组类型的清洗提示 -->
      <div v-if="['object', 'array', 'table'].includes(currentFieldConfig?.nodeType)" class="bg-white border rounded-lg p-6">
        <h4 class="text-base font-medium mb-4">数据清洗管道</h4>
        <a-alert
          type="info"
          show-icon
          :message="currentFieldConfig?.nodeType === 'object' ? '对象类型不支持直接清洗' : '数组类型不支持直接清洗'"
          :description="currentFieldConfig?.nodeType === 'object' 
            ? '对象是容器类型，清洗操作应配置在其子字段上。请选择子字段（如 ' + currentFieldConfig?.key + '.fengge）进行清洗配置。'
            : '数组是容器类型，清洗操作应配置在其元素的子字段上。请选择子字段进行清洗配置。'"
        />
      </div>

      <!-- 数据校验规则 -->
      <div class="bg-white border rounded-lg p-6">
        <div class="flex justify-between items-center mb-4">
          <h4 class="text-base font-medium">数据校验规则</h4>
          <a-button @click="handleAddValidationRule">
            <template #icon><PlusOutlined /></template>
            添加校验规则
          </a-button>
        </div>

        <div v-if="validationRules.length > 0" class="space-y-3">
          <div
            v-for="(rule, index) in validationRules"
            :key="index"
            class="border rounded p-4"
          >
            <div class="flex justify-between items-start mb-3">
              <a-tag color="orange">规则 {{ index + 1 }}</a-tag>
              <a-button type="link" danger size="small" @click="handleRemoveValidationRule(index)">
                <DeleteOutlined /> 删除
              </a-button>
            </div>

            <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
              <a-form-item label="校验类型">
                <a-select v-model:value="rule.type">
                  <!-- 通用校验 -->
                  <a-select-option value="required">必填校验</a-select-option>
                  <a-select-option value="not_empty">非空校验</a-select-option>
                  <!-- 字段类型校验 -->
                  <a-select-option v-if="currentFieldConfig?.nodeType === 'field'" value="pattern">格式校验</a-select-option>
                  <a-select-option v-if="currentFieldConfig?.nodeType === 'field'" value="range">范围校验</a-select-option>
                  <a-select-option v-if="currentFieldConfig?.nodeType === 'field'" value="length">长度校验</a-select-option>
                  <!-- 对象类型校验 -->
                  <a-select-option v-if="currentFieldConfig?.nodeType === 'object'" value="has_fields">子字段存在性</a-select-option>
                  <!-- 数组类型校验 -->
                  <a-select-option v-if="['array', 'table'].includes(currentFieldConfig?.nodeType)" value="array_length">数组长度</a-select-option>
                  <a-select-option v-if="['array', 'table'].includes(currentFieldConfig?.nodeType)" value="array_unique">元素唯一性</a-select-option>
                  <!-- 自定义脚本 -->
                  <a-select-option value="custom">自定义脚本</a-select-option>
                </a-select>
              </a-form-item>

              <!-- 必填校验 -->
              <template v-if="rule.type === 'required'">
                <a-form-item label="错误提示">
                  <a-input v-model:value="rule.message" placeholder="该字段为必填项" />
                </a-form-item>
              </template>

              <!-- 非空校验 -->
              <template v-if="rule.type === 'not_empty'">
                <a-form-item label="说明">
                  <span class="text-gray-500 text-sm">
                    <template v-if="currentFieldConfig?.nodeType === 'object'">对象不能为空（至少有一个子字段有值）</template>
                    <template v-else-if="['array', 'table'].includes(currentFieldConfig?.nodeType)">数组不能为空（至少有一个元素）</template>
                    <template v-else>字段值不能为空字符串</template>
                  </span>
                </a-form-item>
                <a-form-item label="错误提示">
                  <a-input v-model:value="rule.message" placeholder="该字段不能为空" />
                </a-form-item>
              </template>

              <!-- 子字段存在性校验（对象类型） -->
              <template v-if="rule.type === 'has_fields'">
                <a-form-item label="必须包含的子字段">
                  <a-select v-model:value="rule.requiredFields" mode="tags" placeholder="输入子字段名，回车确认" style="width: 100%"></a-select>
                  <div class="text-xs text-gray-500 mt-1">输入子字段的键名，如：fengge, yinyue</div>
                </a-form-item>
                <a-form-item label="错误提示">
                  <a-input v-model:value="rule.message" placeholder="缺少必要的子字段" />
                </a-form-item>
              </template>

              <!-- 数组长度校验 -->
              <template v-if="rule.type === 'array_length'">
                <a-form-item label="最小元素数">
                  <a-input-number v-model:value="rule.minLength" :min="0" style="width: 100%" placeholder="不限制" />
                </a-form-item>
                <a-form-item label="最大元素数">
                  <a-input-number v-model:value="rule.maxLength" :min="0" style="width: 100%" placeholder="不限制" />
                </a-form-item>
                <a-form-item label="错误提示">
                  <a-input v-model:value="rule.message" placeholder="数组长度不符合要求" />
                </a-form-item>
              </template>

              <!-- 数组元素唯一性校验 -->
              <template v-if="rule.type === 'array_unique'">
                <a-form-item label="唯一性判断键">
                  <a-input v-model:value="rule.uniqueKey" placeholder="如：scene（留空则比较整个元素）" />
                  <div class="text-xs text-gray-500 mt-1">如果数组元素是对象，指定用于判断唯一性的键名</div>
                </a-form-item>
                <a-form-item label="错误提示">
                  <a-input v-model:value="rule.message" placeholder="数组存在重复元素" />
                </a-form-item>
              </template>

              <!-- 格式校验 -->
              <template v-if="rule.type === 'pattern'">
                <a-form-item label="格式类型">
                  <a-select v-model:value="rule.patternType">
                    <a-select-option value="email">邮箱</a-select-option>
                    <a-select-option value="phone">手机号</a-select-option>
                    <a-select-option value="id_card">身份证</a-select-option>
                    <a-select-option value="url">URL</a-select-option>
                    <a-select-option value="custom">自定义正则</a-select-option>
                  </a-select>
                </a-form-item>
                <a-form-item v-if="rule.patternType === 'custom'" label="正则表达式">
                  <a-input v-model:value="rule.pattern" placeholder="输入正则表达式" />
                </a-form-item>
                <a-form-item label="错误提示">
                  <a-input v-model:value="rule.message" placeholder="格式不正确" />
                </a-form-item>
              </template>

              <!-- 范围校验 -->
              <template v-if="rule.type === 'range'">
                <a-form-item label="最小值">
                  <a-input-number v-model:value="rule.min" style="width: 100%" />
                </a-form-item>
                <a-form-item label="最大值">
                  <a-input-number v-model:value="rule.max" style="width: 100%" />
                </a-form-item>
                <a-form-item label="错误提示">
                  <a-input v-model:value="rule.message" placeholder="数值超出范围" />
                </a-form-item>
              </template>

              <!-- 长度校验 -->
              <template v-if="rule.type === 'length'">
                <a-form-item label="最小长度">
                  <a-input-number v-model:value="rule.minLength" :min="0" style="width: 100%" />
                </a-form-item>
                <a-form-item label="最大长度">
                  <a-input-number v-model:value="rule.maxLength" :min="0" style="width: 100%" />
                </a-form-item>
                <a-form-item label="错误提示">
                  <a-input v-model:value="rule.message" placeholder="长度不符合要求" />
                </a-form-item>
              </template>

              <!-- 自定义脚本 -->
              <template v-if="rule.type === 'custom'">
                <a-form-item label="JavaScript表达式">
                  <a-textarea v-model:value="rule.expression" placeholder="例如: fields.amount * fields.count === fields.total" :rows="3" />
                  <div class="text-xs text-gray-500 mt-1">可使用 fields.字段名 访问其他字段值</div>
                </a-form-item>
                <a-form-item label="错误提示">
                  <a-input v-model:value="rule.message" placeholder="校验失败" />
                </a-form-item>
              </template>
            </a-form>
          </div>
        </div>

        <a-empty v-else description="暂无校验规则" />
      </div>

      <!-- 保存按钮 -->
      <div class="flex justify-end space-x-3">
        <a-button @click="handleReset">重置</a-button>
        <a-button type="primary" @click="handleSave">保存配置</a-button>
      </div>
    </div>

    <!-- 未选择字段时的提示 -->
    <div v-else-if="treeData.length > 0" class="bg-white border rounded-lg p-6">
      <a-empty description="请在上方树形结构中选择要配置的字段" />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  DeleteOutlined,
  FolderOutlined,
  UnorderedListOutlined,
  TableOutlined,
  FileTextOutlined,
  CheckCircleFilled
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

// 清洗规则
const cleaningRules = ref([])

// 校验规则
const validationRules = ref([])

// 将schema转换为树形数据
const treeData = computed(() => {
  const buildTree = (schema, prefix = '') => {
    if (!schema || typeof schema !== 'object') return []
    
    const nodes = []
    for (const [key, value] of Object.entries(schema)) {
      if (!value || typeof value !== 'object') continue
      
      const fullKey = prefix ? `${prefix}.${key}` : key
      const nodeType = value.nodeType || 'field'
      
      const node = {
        key: fullKey,
        title: value.label || key,
        label: value.label || key,
        nodeType: nodeType,
        type: value.type || 'string',
        description: value.description || '',
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

// 检查字段是否已配置
const isFieldConfigured = (fieldKey) => {
  const config = localConfig.value[fieldKey]
  if (!config) return false
  const hasCleaning = config.cleaning && config.cleaning.length > 0
  const hasValidation = config.validation && config.validation.length > 0
  return hasCleaning || hasValidation
}

// 树形选择处理
const handleTreeSelect = (selectedKeysValue, { node }) => {
  selectedField.value = node.dataRef.key
  currentFieldConfig.value = {
    key: node.dataRef.key,
    label: node.dataRef.label,
    nodeType: node.dataRef.nodeType,
    type: node.dataRef.type,
    description: node.dataRef.description
  }
  
  // 加载该字段的配置
  if (localConfig.value[selectedField.value]) {
    cleaningRules.value = [...(localConfig.value[selectedField.value].cleaning || [])]
    validationRules.value = [...(localConfig.value[selectedField.value].validation || [])]
  } else {
    cleaningRules.value = []
    validationRules.value = []
  }
}

// 添加清洗规则
const handleAddCleaningRule = () => {
  cleaningRules.value.push({
    type: 'regex_replace',
    pattern: '',
    replacement: '',
    trimMode: 'both',
    inputFormat: [],
    outputFormat: '',
    decimalPlaces: 2,
    useThousandSeparator: false,
    caseMode: 'upper'
  })
}

// 删除清洗规则
const handleRemoveCleaningRule = (index) => {
  cleaningRules.value.splice(index, 1)
}

// 添加校验规则
const handleAddValidationRule = () => {
  const nodeType = currentFieldConfig.value?.nodeType || 'field'
  let defaultType = 'required'
  
  if (nodeType === 'object') {
    defaultType = 'not_empty'
  } else if (nodeType === 'array' || nodeType === 'table') {
    defaultType = 'not_empty'
  }
  
  validationRules.value.push({
    type: defaultType,
    message: '',
    patternType: 'email',
    pattern: '',
    min: null,
    max: null,
    minLength: null,
    maxLength: null,
    requiredFields: [],
    uniqueKey: '',
    expression: ''
  })
}

// 删除校验规则
const handleRemoveValidationRule = (index) => {
  validationRules.value.splice(index, 1)
}

// 保存配置
const handleSave = () => {
  if (!selectedField.value) {
    message.warning('请先选择字段')
    return
  }
  
  localConfig.value[selectedField.value] = {
    cleaning: [...cleaningRules.value],
    validation: [...validationRules.value]
  }
  
  emit('update:config', { ...localConfig.value })
  message.success('配置保存成功，请点击顶部"保存"按钮保存到服务器')
}

// 重置配置
const handleReset = () => {
  if (localConfig.value[selectedField.value]) {
    cleaningRules.value = [...(localConfig.value[selectedField.value].cleaning || [])]
    validationRules.value = [...(localConfig.value[selectedField.value].validation || [])]
  } else {
    cleaningRules.value = []
    validationRules.value = []
  }
  message.info('已重置为上次保存的配置')
}

// 获取节点类型颜色
const getNodeTypeColor = (nodeType) => {
  const colorMap = {
    field: 'blue',
    object: 'purple',
    array: 'orange',
    table: 'green'
  }
  return colorMap[nodeType] || 'default'
}

// 获取节点类型标签
const getNodeTypeLabel = (nodeType) => {
  const labelMap = {
    field: '字段',
    object: '对象',
    array: '数组',
    table: '表格'
  }
  return labelMap[nodeType] || nodeType
}
</script>

<style scoped>
.validation-config-container {
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
