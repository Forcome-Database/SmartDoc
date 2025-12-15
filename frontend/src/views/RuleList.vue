<template>
  <div class="rule-list-container p-6">
    <!-- 页面标题和操作栏 -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">规则管理</h1>
        <p class="text-gray-500 mt-1">管理文档处理规则的配置和版本</p>
      </div>
      <a-button type="primary" size="large" @click="handleCreate">
        <template #icon><PlusOutlined /></template>
        新建规则
      </a-button>
    </div>

    <!-- 搜索和筛选 -->
    <div class="bg-white p-4 rounded-lg shadow-sm mb-4">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-input-search
            v-model:value="searchText"
            placeholder="搜索规则名称或编码"
            allow-clear
            @search="handleSearch"
          >
            <template #prefix><SearchOutlined /></template>
          </a-input-search>
        </a-col>
        <a-col :span="6">
          <a-select
            v-model:value="filters.documentType"
            placeholder="文档类型"
            allow-clear
            style="width: 100%"
            @change="handleSearch"
          >
            <a-select-option value="">全部类型</a-select-option>
            <a-select-option value="invoice">发票</a-select-option>
            <a-select-option value="contract">合同</a-select-option>
            <a-select-option value="id_card">身份证</a-select-option>
            <a-select-option value="other">其他</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select
            v-model:value="filters.status"
            placeholder="状态"
            allow-clear
            style="width: 100%"
            @change="handleSearch"
          >
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="published">已发布</a-select-option>
            <a-select-option value="draft">草稿</a-select-option>
            <a-select-option value="archived">已归档</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-button @click="handleReset" style="width: 100%">重置</a-button>
        </a-col>
      </a-row>
    </div>

    <!-- 规则列表表格 -->
    <div class="bg-white rounded-lg shadow-sm">
      <a-table
        :columns="columns"
        :data-source="rules"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
      >
        <!-- 规则名称 -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <div>
              <div class="font-medium text-gray-900">{{ record.name }}</div>
              <div class="text-sm text-gray-500">{{ record.code }}</div>
            </div>
          </template>

          <!-- 文档类型 -->
          <template v-else-if="column.key === 'documentType'">
            <a-tag :color="getDocumentTypeColor(record.document_type)">
              {{ getDocumentTypeLabel(record.document_type) }}
            </a-tag>
          </template>

          <!-- 当前版本 -->
          <template v-else-if="column.key === 'currentVersion'">
            <a-tag color="blue">{{ record.current_version || '未发布' }}</a-tag>
          </template>

          <!-- 状态 -->
          <template v-else-if="column.key === 'status'">
            <a-badge
              :status="getStatusBadge(record.status)"
              :text="getStatusLabel(record.status)"
            />
          </template>

          <!-- 创建时间 -->
          <template v-else-if="column.key === 'createdAt'">
            {{ formatDateTime(record.created_at) }}
          </template>

          <!-- 操作 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="handleEdit(record)">
                编辑
              </a-button>
              <a-button type="link" size="small" @click="handleViewVersions(record)">
                版本
              </a-button>
              <a-dropdown>
                <a-button type="link" size="small">
                  更多 <DownOutlined />
                </a-button>
                <template #overlay>
                  <a-menu>
                    <a-menu-item @click="handleCopy(record)">
                      <CopyOutlined /> 复制
                    </a-menu-item>
                    <a-menu-item @click="handleExport(record)">
                      <ExportOutlined /> 导出
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item danger @click="handleDelete(record)">
                      <DeleteOutlined /> 删除
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 新建规则对话框 -->
    <a-modal
      v-model:open="createModalVisible"
      title="新建规则"
      @ok="handleCreateSubmit"
      @cancel="handleCreateCancel"
      :confirm-loading="createLoading"
    >
      <a-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        layout="vertical"
      >
        <a-form-item label="规则名称" name="name">
          <a-input
            v-model:value="createForm.name"
            placeholder="请输入规则名称"
          />
        </a-form-item>
        <a-form-item label="规则编码" name="code">
          <a-input
            v-model:value="createForm.code"
            placeholder="请输入规则编码（唯一标识）"
          />
        </a-form-item>
        <a-form-item label="文档类型" name="documentType">
          <a-select
            v-model:value="createForm.documentType"
            placeholder="请选择文档类型"
          >
            <a-select-option value="invoice">发票</a-select-option>
            <a-select-option value="contract">合同</a-select-option>
            <a-select-option value="id_card">身份证</a-select-option>
            <a-select-option value="other">其他</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="描述" name="description">
          <a-textarea
            v-model:value="createForm.description"
            placeholder="请输入规则描述"
            :rows="3"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  PlusOutlined,
  SearchOutlined,
  DownOutlined,
  CopyOutlined,
  ExportOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'
import { ruleAPI } from '@/api/rule'
import { formatDateTime } from '@/utils/format'

const router = useRouter()

// 表格列定义
const columns = [
  {
    title: '规则名称',
    key: 'name',
    width: 250
  },
  {
    title: '文档类型',
    key: 'documentType',
    width: 120
  },
  {
    title: '当前版本',
    key: 'currentVersion',
    width: 120
  },
  {
    title: '状态',
    key: 'status',
    width: 100
  },
  {
    title: '创建时间',
    key: 'createdAt',
    width: 180
  },
  {
    title: '操作',
    key: 'action',
    width: 200,
    fixed: 'right'
  }
]

// 数据状态
const loading = ref(false)
const rules = ref([])
const searchText = ref('')
const filters = reactive({
  documentType: '',
  status: ''
})

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total) => `共 ${total} 条记录`
})

// 新建规则表单
const createModalVisible = ref(false)
const createLoading = ref(false)
const createFormRef = ref()
const createForm = reactive({
  name: '',
  code: '',
  documentType: '',
  description: ''
})

const createRules = {
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入规则编码', trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: '编码只能包含大写字母、数字和下划线', trigger: 'blur' }
  ],
  documentType: [{ required: true, message: '请选择文档类型', trigger: 'change' }]
}

// 获取规则列表
const fetchRules = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchText.value,
      document_type: filters.documentType,
      status: filters.status
    }
    
    const response = await ruleAPI.list(params)
    rules.value = response.items || []
    pagination.total = response.total || 0
  } catch (error) {
    message.error('获取规则列表失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  pagination.current = 1
  fetchRules()
}

// 重置筛选
const handleReset = () => {
  searchText.value = ''
  filters.documentType = ''
  filters.status = ''
  pagination.current = 1
  fetchRules()
}

// 表格变化处理
const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchRules()
}

// 新建规则
const handleCreate = () => {
  createModalVisible.value = true
}

// 提交新建
const handleCreateSubmit = async () => {
  try {
    await createFormRef.value.validate()
    createLoading.value = true
    
    const response = await ruleAPI.create({
      name: createForm.name,
      code: createForm.code,
      document_type: createForm.documentType,
      description: createForm.description
    })
    
    message.success('规则创建成功')
    createModalVisible.value = false
    
    // 跳转到编辑页面
    router.push(`/rules/${response.id}/edit`)
  } catch (error) {
    if (error.errorFields) {
      // 表单验证错误
      return
    }
    message.error('创建规则失败：' + (error.message || '未知错误'))
  } finally {
    createLoading.value = false
  }
}

// 取消新建
const handleCreateCancel = () => {
  createFormRef.value.resetFields()
  createModalVisible.value = false
}

// 编辑规则
const handleEdit = (record) => {
  router.push(`/rules/${record.id}/edit`)
}

// 查看版本
const handleViewVersions = (record) => {
  router.push(`/rules/${record.id}/versions`)
}

// 复制规则
const handleCopy = async (record) => {
  try {
    const response = await ruleAPI.get(record.id)
    const ruleData = response
    
    // 创建副本
    await ruleAPI.create({
      name: `${ruleData.name} (副本)`,
      code: `${ruleData.code}_COPY_${Date.now()}`,
      document_type: ruleData.document_type,
      description: ruleData.description
    })
    
    message.success('规则复制成功')
    fetchRules()
  } catch (error) {
    message.error('复制规则失败：' + (error.message || '未知错误'))
  }
}

// 导出规则
const handleExport = async (record) => {
  try {
    const response = await ruleAPI.get(record.id)
    const ruleData = response
    
    // 导出为JSON文件
    const dataStr = JSON.stringify(ruleData, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `rule_${record.code}_${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)
    
    message.success('规则导出成功')
  } catch (error) {
    message.error('导出规则失败：' + (error.message || '未知错误'))
  }
}

// 删除规则
const handleDelete = (record) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除规则"${record.name}"吗？此操作不可恢复。`,
    okText: '确认',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await ruleAPI.delete(record.id)
        message.success('规则删除成功')
        fetchRules()
      } catch (error) {
        message.error('删除规则失败：' + (error.message || '未知错误'))
      }
    }
  })
}

// 获取文档类型颜色
const getDocumentTypeColor = (type) => {
  const colors = {
    invoice: 'blue',
    contract: 'green',
    id_card: 'orange',
    other: 'default'
  }
  return colors[type] || 'default'
}

// 获取文档类型标签
const getDocumentTypeLabel = (type) => {
  const labels = {
    invoice: '发票',
    contract: '合同',
    id_card: '身份证',
    other: '其他'
  }
  return labels[type] || type
}

// 获取状态徽章
const getStatusBadge = (status) => {
  const badges = {
    published: 'success',
    draft: 'processing',
    archived: 'default'
  }
  return badges[status] || 'default'
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

// 页面加载时获取数据
onMounted(() => {
  fetchRules()
})
</script>

<style scoped>
.rule-list-container {
  min-height: calc(100vh - 64px);
  background-color: #f5f5f5;
}
</style>
