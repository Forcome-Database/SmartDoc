<template>
  <a-modal
    :open="open"
    title="版本历史"
    width="800px"
    :footer="null"
    @cancel="handleClose"
  >
    <div class="version-dialog-content">
      <!-- 版本时间线 -->
      <a-timeline>
        <a-timeline-item
          v-for="version in sortedVersions"
          :key="version.version"
          :color="getVersionColor(version.status)"
        >
          <template #dot>
            <component :is="getVersionIcon(version.status)" />
          </template>

          <div class="version-item">
            <!-- 版本头部 -->
            <div class="flex justify-between items-start mb-2">
              <div>
                <h4 class="text-base font-medium">
                  {{ version.version }}
                  <a-tag :color="getStatusColor(version.status)" class="ml-2">
                    {{ getStatusLabel(version.status) }}
                  </a-tag>
                </h4>
                <div class="text-sm text-gray-500 mt-1">
                  <span v-if="version.published_at">
                    发布时间：{{ formatDateTime(version.published_at) }}
                  </span>
                  <span v-else>
                    创建时间：{{ formatDateTime(version.created_at) }}
                  </span>
                </div>
                <div v-if="version.published_by" class="text-sm text-gray-500">
                  发布人：{{ version.published_by }}
                </div>
              </div>

              <a-space>
                <a-button
                  size="small"
                  @click="handleViewConfig(version)"
                >
                  查看配置
                </a-button>
                <a-button
                  v-if="version.status === 'archived'"
                  type="primary"
                  size="small"
                  @click="handleRollback(version)"
                >
                  回滚到此版本
                </a-button>
              </a-space>
            </div>

            <!-- 版本描述 -->
            <div v-if="version.description" class="text-sm text-gray-600 mb-2">
              {{ version.description }}
            </div>

            <!-- 配置摘要 -->
            <div class="config-summary p-3 bg-gray-50 rounded">
              <div class="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span class="text-gray-600">OCR引擎：</span>
                  <span class="font-medium">{{ version.config?.basic?.ocrEngine || '-' }}</span>
                </div>
                <div>
                  <span class="text-gray-600">页面策略：</span>
                  <span class="font-medium">{{ version.config?.basic?.pageStrategy || '-' }}</span>
                </div>
                <div>
                  <span class="text-gray-600">字段数量：</span>
                  <span class="font-medium">{{ getFieldCount(version.config?.schema) }}</span>
                </div>
                <div>
                  <span class="text-gray-600">提取规则：</span>
                  <span class="font-medium">{{ getExtractionRuleCount(version.config?.extraction) }}</span>
                </div>
              </div>
            </div>
          </div>
        </a-timeline-item>
      </a-timeline>
    </div>

    <!-- 配置查看对话框 -->
    <a-modal
      v-model:open="configModalVisible"
      title="版本配置详情"
      width="900px"
      :footer="null"
    >
      <div v-if="selectedVersion" class="config-detail">
        <a-tabs>
          <a-tab-pane key="basic" tab="基础配置">
            <pre class="config-viewer">{{ formatJson(selectedVersion.config?.basic) }}</pre>
          </a-tab-pane>
          <a-tab-pane key="schema" tab="Schema定义">
            <pre class="config-viewer">{{ formatJson(selectedVersion.config?.schema) }}</pre>
          </a-tab-pane>
          <a-tab-pane key="extraction" tab="提取策略">
            <pre class="config-viewer">{{ formatJson(selectedVersion.config?.extraction) }}</pre>
          </a-tab-pane>
          <a-tab-pane key="validation" tab="清洗校验">
            <pre class="config-viewer">{{ formatJson(selectedVersion.config?.validation) }}</pre>
          </a-tab-pane>
          <a-tab-pane key="enhancement" tab="增强风控">
            <pre class="config-viewer">{{ formatJson(selectedVersion.config?.enhancement) }}</pre>
          </a-tab-pane>
        </a-tabs>
      </div>
    </a-modal>
  </a-modal>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Modal, message } from 'ant-design-vue'
import {
  CheckCircleOutlined,
  EditOutlined,
  FileOutlined
} from '@ant-design/icons-vue'
import { formatDateTime } from '@/utils/format'

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  ruleId: {
    type: String,
    required: true
  },
  versions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:open', 'rollback'])

// 状态
const configModalVisible = ref(false)
const selectedVersion = ref(null)

// 排序后的版本列表（按版本号降序）
const sortedVersions = computed(() => {
  return [...props.versions].sort((a, b) => {
    // 提取版本号进行比较
    const versionA = parseVersion(a.version)
    const versionB = parseVersion(b.version)
    
    if (versionA.major !== versionB.major) {
      return versionB.major - versionA.major
    }
    return versionB.minor - versionA.minor
  })
})

// 解析版本号
const parseVersion = (versionStr) => {
  const match = versionStr.match(/V?(\d+)\.(\d+)/)
  if (match) {
    return {
      major: parseInt(match[1]),
      minor: parseInt(match[2])
    }
  }
  return { major: 0, minor: 0 }
}

// 获取版本颜色
const getVersionColor = (status) => {
  const colors = {
    published: 'green',
    draft: 'blue',
    archived: 'gray'
  }
  return colors[status] || 'gray'
}

// 获取版本图标
const getVersionIcon = (status) => {
  const icons = {
    published: CheckCircleOutlined,
    draft: EditOutlined,
    archived: FileOutlined
  }
  return icons[status] || FileOutlined
}

// 获取状态颜色
const getStatusColor = (status) => {
  const colors = {
    published: 'success',
    draft: 'processing',
    archived: 'default'
  }
  return colors[status] || 'default'
}

// 获取状态标签
const getStatusLabel = (status) => {
  const labels = {
    published: '已发布',
    draft: '草稿',
    archived: '已归档'
  }
  return labels[status] || status
}

// 获取字段数量
const getFieldCount = (schema) => {
  if (!schema) return 0
  
  let count = 0
  const countFields = (obj) => {
    for (const value of Object.values(obj)) {
      if (value.nodeType === 'field') {
        count++
      }
      if (value.properties) {
        countFields(value.properties)
      }
      if (value.items) {
        countFields(value.items)
      }
      if (value.columns) {
        countFields(value.columns)
      }
    }
  }
  
  countFields(schema)
  return count
}

// 获取提取规则数量
const getExtractionRuleCount = (extraction) => {
  if (!extraction) return 0
  return Object.keys(extraction).length
}

// 查看配置
const handleViewConfig = (version) => {
  selectedVersion.value = version
  configModalVisible.value = true
}

// 回滚版本
const handleRollback = (version) => {
  Modal.confirm({
    title: '确认回滚',
    content: `确定要回滚到版本 ${version.version} 吗？当前版本将被归档。`,
    okText: '确认回滚',
    okType: 'primary',
    cancelText: '取消',
    onOk: () => {
      emit('rollback', version.id)
    }
  })
}

// 格式化JSON
const formatJson = (obj) => {
  if (!obj) return '{}'
  return JSON.stringify(obj, null, 2)
}

// 关闭对话框
const handleClose = () => {
  emit('update:open', false)
}
</script>

<style scoped>
.version-dialog-content {
  max-height: 600px;
  overflow-y: auto;
}

.version-item {
  padding: 12px;
  background-color: white;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  margin-bottom: 16px;
}

.config-summary {
  font-size: 13px;
}

.config-viewer {
  background-color: #f5f5f5;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  padding: 16px;
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
  max-height: 500px;
  overflow-y: auto;
}

:deep(.ant-timeline-item-content) {
  margin-left: 24px;
}
</style>
