<template>
  <div class="pipeline-list">
    <a-card title="数据处理管道" :bordered="false">
      <template #extra>
        <a-button type="primary" @click="showCreateModal">
          <template #icon><PlusOutlined /></template>
          新建管道
        </a-button>
      </template>

      <!-- 搜索栏 -->
      <a-row :gutter="16" class="search-bar">
        <a-col :span="6">
          <a-input v-model:value="searchParams.keyword" placeholder="搜索管道名称" allowClear />
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="searchParams.status" placeholder="状态" allowClear style="width: 100%">
            <a-select-option value="draft">草稿</a-select-option>
            <a-select-option value="active">激活</a-select-option>
            <a-select-option value="inactive">停用</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-button type="primary" @click="fetchPipelines">查询</a-button>
          <a-button style="margin-left: 8px" @click="resetSearch">重置</a-button>
        </a-col>
      </a-row>

      <!-- 管道列表 -->
      <a-table
        :columns="columns"
        :data-source="pipelines"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a @click="showEditModal(record)">编辑</a>
              <a @click="showTestModal(record)">测试</a>
              <a-divider type="vertical" />
              <a v-if="record.status !== 'active'" @click="activatePipeline(record)">激活</a>
              <a v-else @click="deactivatePipeline(record)">停用</a>
              <a-divider type="vertical" />
              <a-popconfirm title="确定删除此管道？" @confirm="deletePipeline(record)">
                <a class="danger">删除</a>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 创建/编辑弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="isEdit ? '编辑管道' : '新建管道'"
      width="800px"
      @ok="handleSubmit"
      :confirmLoading="submitLoading"
    >
      <a-form :model="formData" :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
        <a-form-item label="管道名称" required>
          <a-input v-model:value="formData.name" placeholder="请输入管道名称" />
        </a-form-item>
        <a-form-item label="关联规则" required>
          <a-select v-model:value="formData.rule_id" placeholder="选择规则" :disabled="isEdit">
            <a-select-option v-for="rule in rules" :key="rule.id" :value="rule.id">
              {{ rule.name }} ({{ rule.code }})
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="formData.description" :rows="2" placeholder="管道描述" />
        </a-form-item>
        <a-form-item label="Python脚本" required>
          <a-textarea
            v-model:value="formData.script_content"
            :rows="12"
            placeholder="# 可用变量: task_id, extracted_data, ocr_text, meta_info&#10;# 将处理结果赋值给 output_data&#10;&#10;output_data = extracted_data"
            style="font-family: monospace"
          />
        </a-form-item>
        <a-form-item label="依赖包">
          <a-textarea
            v-model:value="formData.requirements"
            :rows="3"
            placeholder="每行一个包，如：&#10;requests==2.31.0&#10;pandas>=2.0.0"
          />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="超时时间" :label-col="{ span: 8 }" :wrapper-col="{ span: 16 }">
              <a-input-number v-model:value="formData.timeout_seconds" :min="10" :max="3600" addon-after="秒" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="最大重试" :label-col="{ span: 8 }" :wrapper-col="{ span: 16 }">
              <a-input-number v-model:value="formData.max_retries" :min="0" :max="5" addon-after="次" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>

    <!-- 测试弹窗 -->
    <a-modal v-model:open="testModalVisible" title="测试管道" width="800px" :footer="null">
      <a-form :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
        <a-form-item label="测试数据">
          <a-textarea
            v-model:value="testData"
            :rows="6"
            placeholder='{"field1": "value1", "field2": "value2"}'
            style="font-family: monospace"
          />
        </a-form-item>
        <a-form-item :wrapper-col="{ offset: 4 }">
          <a-button type="primary" @click="runTest" :loading="testLoading">执行测试</a-button>
        </a-form-item>
      </a-form>
      
      <a-divider v-if="testResult">测试结果</a-divider>
      <div v-if="testResult">
        <a-alert :type="testResult.success ? 'success' : 'error'" :message="testResult.success ? '执行成功' : '执行失败'" />
        <a-collapse style="margin-top: 16px">
          <a-collapse-panel header="输出数据" key="output">
            <pre>{{ JSON.stringify(testResult.output_data, null, 2) }}</pre>
          </a-collapse-panel>
          <a-collapse-panel header="标准输出" key="stdout" v-if="testResult.stdout">
            <pre>{{ testResult.stdout }}</pre>
          </a-collapse-panel>
          <a-collapse-panel header="错误输出" key="stderr" v-if="testResult.stderr || testResult.error_message">
            <pre>{{ testResult.stderr || testResult.error_message }}</pre>
          </a-collapse-panel>
        </a-collapse>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { pipelineApi, ruleApi } from '@/api'

// 状态
const loading = ref(false)
const pipelines = ref([])
const rules = ref([])
const modalVisible = ref(false)
const testModalVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const testLoading = ref(false)
const testData = ref('{}')
const testResult = ref(null)
const currentPipeline = ref(null)

// 搜索参数
const searchParams = reactive({
  keyword: '',
  status: undefined
})

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

// 表单数据
const formData = reactive({
  name: '',
  description: '',
  rule_id: '',
  script_content: '',
  requirements: '',
  timeout_seconds: 300,
  max_retries: 1
})

// 表格列
const columns = [
  { title: '管道名称', dataIndex: 'name', key: 'name' },
  { title: '关联规则', dataIndex: 'rule_id', key: 'rule_id' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '超时时间', dataIndex: 'timeout_seconds', key: 'timeout', customRender: ({ text }) => `${text}秒` },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
  { title: '操作', key: 'action', width: 250 }
]

// 方法
const getStatusColor = (status) => {
  const colors = { draft: 'default', active: 'green', inactive: 'orange' }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = { draft: '草稿', active: '激活', inactive: '停用' }
  return texts[status] || status
}

const fetchPipelines = async () => {
  loading.value = true
  try {
    const res = await pipelineApi.list({
      page: pagination.current,
      page_size: pagination.pageSize,
      ...searchParams
    })
    pipelines.value = res.items
    pagination.total = res.total
  } catch (e) {
    message.error('获取管道列表失败')
  } finally {
    loading.value = false
  }
}

const fetchRules = async () => {
  try {
    const res = await ruleApi.list({ page_size: 100 })
    rules.value = res.items
  } catch (e) {
    console.error('获取规则列表失败', e)
  }
}

const resetSearch = () => {
  searchParams.keyword = ''
  searchParams.status = undefined
  pagination.current = 1
  fetchPipelines()
}

const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchPipelines()
}

const showCreateModal = () => {
  isEdit.value = false
  Object.assign(formData, {
    name: '', description: '', rule_id: '', script_content: '',
    requirements: '', timeout_seconds: 300, max_retries: 1
  })
  modalVisible.value = true
}

const showEditModal = (record) => {
  isEdit.value = true
  currentPipeline.value = record
  Object.assign(formData, record)
  modalVisible.value = true
}

const handleSubmit = async () => {
  submitLoading.value = true
  try {
    if (isEdit.value) {
      await pipelineApi.update(currentPipeline.value.id, formData)
      message.success('更新成功')
    } else {
      await pipelineApi.create(formData)
      message.success('创建成功')
    }
    modalVisible.value = false
    fetchPipelines()
  } catch (e) {
    message.error(e.response?.data?.detail || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

const activatePipeline = async (record) => {
  try {
    await pipelineApi.activate(record.id)
    message.success('激活成功')
    fetchPipelines()
  } catch (e) {
    message.error('激活失败')
  }
}

const deactivatePipeline = async (record) => {
  try {
    await pipelineApi.deactivate(record.id)
    message.success('停用成功')
    fetchPipelines()
  } catch (e) {
    message.error('停用失败')
  }
}

const deletePipeline = async (record) => {
  try {
    await pipelineApi.delete(record.id)
    message.success('删除成功')
    fetchPipelines()
  } catch (e) {
    message.error('删除失败')
  }
}

const showTestModal = (record) => {
  currentPipeline.value = record
  testData.value = '{}'
  testResult.value = null
  testModalVisible.value = true
}

const runTest = async () => {
  testLoading.value = true
  try {
    const data = JSON.parse(testData.value)
    testResult.value = await pipelineApi.test(currentPipeline.value.id, { test_data: data })
  } catch (e) {
    if (e instanceof SyntaxError) {
      message.error('测试数据JSON格式错误')
    } else {
      message.error('测试执行失败')
    }
  } finally {
    testLoading.value = false
  }
}

onMounted(() => {
  fetchPipelines()
  fetchRules()
})
</script>

<style scoped>
.search-bar { margin-bottom: 16px; }
.danger { color: #ff4d4f; }
pre { background: #f5f5f5; padding: 12px; border-radius: 4px; overflow: auto; max-height: 300px; }
</style>
