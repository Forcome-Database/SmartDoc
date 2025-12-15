<!--
  @deprecated 此组件已被弃用，请使用以下新组件：
  - ManualReview.vue - 人工审核列表页
  - ReviewDetail.vue - 审核详情页
  保留此文件仅供参考，将在后续版本中删除
-->
<template>
  <div class="audit-workbench">
    <!-- 顶部操作栏 -->
    <div class="workbench-header">
      <div class="header-left">
        <h2>审核工作台</h2>
        <a-tag v-if="currentTask" color="blue">
          任务ID: {{ currentTask.id }}
        </a-tag>
        <a-tag v-if="currentTask" :color="getStatusColor(currentTask.status)">
          {{ getStatusText(currentTask.status) }}
        </a-tag>
      </div>
      <div class="header-right">
        <a-space>
          <a-button @click="loadPrevTask" :disabled="!hasPrevTask">
            <template #icon><LeftOutlined /></template>
            上一个
          </a-button>
          <a-button @click="loadNextTask" :disabled="!hasNextTask">
            下一个
            <template #icon><RightOutlined /></template>
          </a-button>
          <a-button @click="refreshTask">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="workbench-content">
      <a-spin :spinning="loading" tip="加载中...">
        <template v-if="currentTask">
          <!-- 桌面端：左右分栏布局 -->
          <div class="desktop-layout">
            <!-- 左侧：PDF预览 -->
            <div class="left-panel">
              <PDFViewer
                ref="pdfViewerRef"
                :task-id="currentTask.id"
                :total-pages="currentTask.page_count"
                :ocr-result="currentTask.ocr_result"
                @box-click="onOcrBoxClick"
                @text-selected="onTextSelected"
                @page-change="onPageChange"
              />
            </div>

            <!-- 右侧：数据表单 -->
            <div class="right-panel">
              <DataForm
                ref="dataFormRef"
                v-model="formData"
                :schema="taskSchema"
                :confidence-scores="currentTask.confidence_scores"
                :source-pages="getSourcePages()"
                @field-focus="onFieldFocus"
                @jump-to-page="jumpToPage"
                @change="onFormChange"
              />

              <!-- 底部操作按钮 -->
              <div class="form-actions">
                <a-space>
                  <a-button
                    type="primary"
                    size="large"
                    :loading="submitting"
                    @click="handleApprove"
                  >
                    <template #icon><CheckOutlined /></template>
                    确认通过
                  </a-button>
                  <a-button
                    danger
                    size="large"
                    :loading="submitting"
                    @click="showRejectModal"
                  >
                    <template #icon><CloseOutlined /></template>
                    驳回
                  </a-button>
                  <a-button size="large" @click="handleSaveDraft">
                    <template #icon><SaveOutlined /></template>
                    保存草稿
                  </a-button>
                </a-space>
              </div>
            </div>
          </div>

          <!-- 移动端：上下布局 -->
          <div class="mobile-layout">
            <a-tabs v-model:activeKey="mobileTab">
              <a-tab-pane key="pdf" tab="PDF预览">
                <PDFViewer
                  ref="mobilePdfViewerRef"
                  :task-id="currentTask.id"
                  :total-pages="currentTask.page_count"
                  :ocr-result="currentTask.ocr_result"
                  @box-click="onOcrBoxClick"
                  @text-selected="onTextSelected"
                />
              </a-tab-pane>
              <a-tab-pane key="form" tab="数据表单">
                <DataForm
                  ref="mobileDataFormRef"
                  v-model="formData"
                  :schema="taskSchema"
                  :confidence-scores="currentTask.confidence_scores"
                  :source-pages="getSourcePages()"
                  @field-focus="onFieldFocus"
                  @jump-to-page="jumpToPageMobile"
                  @change="onFormChange"
                />
              </a-tab-pane>
            </a-tabs>

            <!-- 移动端操作按钮 -->
            <div class="mobile-actions">
              <a-button
                type="primary"
                block
                size="large"
                :loading="submitting"
                @click="handleApprove"
              >
                <template #icon><CheckOutlined /></template>
                确认通过
              </a-button>
              <a-button
                danger
                block
                size="large"
                class="mt-2"
                :loading="submitting"
                @click="showRejectModal"
              >
                <template #icon><CloseOutlined /></template>
                驳回
              </a-button>
            </div>
          </div>
        </template>

        <!-- 无任务提示 -->
        <a-empty v-else description="暂无待审核任务" />
      </a-spin>
    </div>

    <!-- 驳回对话框 -->
    <a-modal
      v-model:open="rejectModalVisible"
      title="驳回任务"
      @ok="handleReject"
      @cancel="rejectModalVisible = false"
    >
      <a-form :label-col="{ span: 6 }">
        <a-form-item label="驳回原因" required>
          <a-textarea
            v-model:value="rejectReason"
            :rows="4"
            placeholder="请输入驳回原因"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  LeftOutlined,
  RightOutlined,
  ReloadOutlined,
  CheckOutlined,
  CloseOutlined,
  SaveOutlined
} from '@ant-design/icons-vue'
import PDFViewer from '@/components/Audit/PDFViewer.vue'
import DataForm from '@/components/Audit/DataForm.vue'
import { auditAPI } from '@/api/audit'
import {
  saveDraftToLocal,
  loadDraftFromLocal,
  removeDraftFromLocal,
  createDebouncedSave,
  cleanExpiredDrafts
} from '@/utils/draftManager'

/**
 * 审核工作台主页面
 * 左右分栏布局：左侧PDF预览，右侧结构化表单
 * 移动端响应式：上下布局
 */

const route = useRoute()
const router = useRouter()

// 状态
const loading = ref(false)
const submitting = ref(false)
const currentTask = ref(null)
const formData = ref({})
const taskSchema = ref({})
const pendingTasks = ref([])
const currentTaskIndex = ref(0)
const mobileTab = ref('pdf')

// 组件引用
const pdfViewerRef = ref(null)
const dataFormRef = ref(null)
const mobilePdfViewerRef = ref(null)
const mobileDataFormRef = ref(null)

// 驳回对话框
const rejectModalVisible = ref(false)
const rejectReason = ref('')

// 计算属性
const hasPrevTask = computed(() => currentTaskIndex.value > 0)
const hasNextTask = computed(() => currentTaskIndex.value < pendingTasks.value.length - 1)

/**
 * 加载待审核任务列表
 */
async function loadPendingTasks() {
  try {
    const response = await auditAPI.getPendingTasks({
      page: 1,
      page_size: 100
    })
    pendingTasks.value = response.items || []
    return pendingTasks.value
  } catch (error) {
    message.error('加载任务列表失败')
    console.error('Load pending tasks error:', error)
    return []
  }
}

/**
 * 加载任务详情
 */
async function loadTaskDetail(taskId) {
  loading.value = true

  try {
    const response = await auditAPI.getTaskDetail(taskId)
    currentTask.value = response

    // 解析Schema
    if (currentTask.value.rule_config && currentTask.value.rule_config.schema) {
      taskSchema.value = currentTask.value.rule_config.schema
    }

    // 加载提取数据
    formData.value = { ...currentTask.value.extracted_data }

    // 尝试加载草稿
    const draft = loadDraftFromLocal(taskId)
    if (draft) {
      Modal.confirm({
        title: '发现未保存的草稿',
        content: '是否加载之前保存的草稿数据？',
        onOk: () => {
          formData.value = draft
          message.success('草稿已加载')
        },
        onCancel: () => {
          removeDraftFromLocal(taskId)
        }
      })
    }
  } catch (error) {
    message.error('加载任务详情失败')
    console.error('Load task detail error:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 刷新当前任务
 */
async function refreshTask() {
  if (currentTask.value) {
    await loadTaskDetail(currentTask.value.id)
  }
}

/**
 * 加载上一个任务
 */
async function loadPrevTask() {
  if (hasPrevTask.value) {
    currentTaskIndex.value--
    const task = pendingTasks.value[currentTaskIndex.value]
    await loadTaskDetail(task.id)
  }
}

/**
 * 加载下一个任务
 */
async function loadNextTask() {
  if (hasNextTask.value) {
    currentTaskIndex.value++
    const task = pendingTasks.value[currentTaskIndex.value]
    await loadTaskDetail(task.id)
  }
}

/**
 * OCR框点击
 */
function onOcrBoxClick(data) {
  // 可以在这里实现点击OCR框后的逻辑
  console.log('OCR box clicked:', data)
}

/**
 * 文本选中
 */
function onTextSelected(text) {
  if (!text) return

  // 询问用户要填入哪个字段
  Modal.confirm({
    title: '选中文本',
    content: `已选中文本：${text}`,
    okText: '填入当前字段',
    cancelText: '取消',
    onOk: () => {
      // 这里需要知道当前聚焦的字段
      // 可以通过全局状态或事件来实现
      message.success('文本已填入')
    }
  })
}

/**
 * 页面变化
 */
function onPageChange(page) {
  console.log('Page changed:', page)
}

/**
 * 字段获得焦点
 */
function onFieldFocus(field) {
  // 如果字段有来源页码，跳转到对应页面
  if (field.sourcePage) {
    jumpToPage(field.sourcePage)
  }
}

/**
 * 跳转到指定页面
 */
function jumpToPage(page) {
  if (pdfViewerRef.value) {
    pdfViewerRef.value.jumpToPage(page)
  }
}

/**
 * 移动端跳转页面
 */
function jumpToPageMobile(page) {
  mobileTab.value = 'pdf'
  setTimeout(() => {
    if (mobilePdfViewerRef.value) {
      mobilePdfViewerRef.value.jumpToPage(page)
    }
  }, 100)
}

/**
 * 表单数据变化
 */
function onFormChange() {
  // 自动保存草稿（防抖）
  debouncedSaveDraft()
}

/**
 * 保存草稿（防抖）
 */
const debouncedSaveDraft = createDebouncedSave(async () => {
  if (!currentTask.value) return

  // 保存到本地
  saveDraftToLocal(currentTask.value.id, formData.value)

  // 保存到服务器
  try {
    await auditAPI.saveDraft(currentTask.value.id, formData.value)
    if (dataFormRef.value) {
      dataFormRef.value.markDraftSaved()
    }
    if (mobileDataFormRef.value) {
      mobileDataFormRef.value.markDraftSaved()
    }
  } catch (error) {
    console.error('Save draft to server failed:', error)
  }
}, 3000)

/**
 * 手动保存草稿
 */
async function handleSaveDraft() {
  if (!currentTask.value) return

  saveDraftToLocal(currentTask.value.id, formData.value)

  try {
    await auditAPI.saveDraft(currentTask.value.id, formData.value)
    message.success('草稿已保存')
    if (dataFormRef.value) {
      dataFormRef.value.markDraftSaved()
    }
  } catch (error) {
    message.error('保存草稿失败')
    console.error('Save draft error:', error)
  }
}

/**
 * 确认通过
 */
async function handleApprove() {
  if (!currentTask.value) return

  // 验证表单
  const formRef = dataFormRef.value || mobileDataFormRef.value
  if (formRef) {
    const valid = await formRef.validate()
    if (!valid) {
      message.error('请检查表单数据')
      return
    }
  }

  submitting.value = true

  try {
    await auditAPI.submitAudit(currentTask.value.id, {
      action: 'approve',
      data: formData.value
    })

    message.success('审核通过，任务已提交')

    // 清除草稿
    removeDraftFromLocal(currentTask.value.id)

    // 加载下一个任务
    if (hasNextTask.value) {
      await loadNextTask()
    } else {
      // 重新加载任务列表
      await loadPendingTasks()
      if (pendingTasks.value.length > 0) {
        currentTaskIndex.value = 0
        await loadTaskDetail(pendingTasks.value[0].id)
      } else {
        currentTask.value = null
        message.info('所有任务已审核完成')
      }
    }
  } catch (error) {
    message.error('提交失败')
    console.error('Submit approve error:', error)
  } finally {
    submitting.value = false
  }
}

/**
 * 显示驳回对话框
 */
function showRejectModal() {
  rejectReason.value = ''
  rejectModalVisible.value = true
}

/**
 * 驳回任务
 */
async function handleReject() {
  if (!rejectReason.value.trim()) {
    message.warning('请输入驳回原因')
    return
  }

  submitting.value = true

  try {
    await auditAPI.submitAudit(currentTask.value.id, {
      action: 'reject',
      reason: rejectReason.value
    })

    message.success('任务已驳回')
    rejectModalVisible.value = false

    // 清除草稿
    removeDraftFromLocal(currentTask.value.id)

    // 加载下一个任务
    if (hasNextTask.value) {
      await loadNextTask()
    } else {
      await loadPendingTasks()
      if (pendingTasks.value.length > 0) {
        currentTaskIndex.value = 0
        await loadTaskDetail(pendingTasks.value[0].id)
      } else {
        currentTask.value = null
        message.info('所有任务已审核完成')
      }
    }
  } catch (error) {
    message.error('驳回失败')
    console.error('Submit reject error:', error)
  } finally {
    submitting.value = false
  }
}

/**
 * 获取来源页码
 */
function getSourcePages() {
  if (!currentTask.value || !currentTask.value.extracted_data) return {}

  const sourcePages = {}
  // 这里需要根据实际的数据结构来提取来源页码
  // 假设extracted_data中每个字段都有source_page属性
  Object.keys(currentTask.value.extracted_data).forEach(key => {
    const field = currentTask.value.extracted_data[key]
    if (field && field.source_page) {
      sourcePages[key] = field.source_page
    }
  })

  return sourcePages
}

/**
 * 获取状态颜色
 */
function getStatusColor(status) {
  const colorMap = {
    pending_audit: 'orange',
    completed: 'green',
    rejected: 'red'
  }
  return colorMap[status] || 'default'
}

/**
 * 获取状态文本
 */
function getStatusText(status) {
  const textMap = {
    pending_audit: '待审核',
    completed: '已完成',
    rejected: '已驳回'
  }
  return textMap[status] || status
}

// 初始化
onMounted(async () => {
  // 清理过期草稿
  cleanExpiredDrafts()

  // 加载任务列表
  await loadPendingTasks()

  // 如果URL中有taskId，加载指定任务
  const taskId = route.query.taskId
  if (taskId) {
    const index = pendingTasks.value.findIndex(t => t.id === taskId)
    if (index >= 0) {
      currentTaskIndex.value = index
    }
    await loadTaskDetail(taskId)
  } else if (pendingTasks.value.length > 0) {
    // 否则加载第一个任务
    await loadTaskDetail(pendingTasks.value[0].id)
  }
})

// 清理
onUnmounted(() => {
  // 可以在这里添加清理逻辑
})
</script>

<style scoped>
.audit-workbench {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f0f2f5;
}

.workbench-header {
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.workbench-content {
  flex: 1;
  overflow: hidden;
}

/* 桌面端布局 */
.desktop-layout {
  display: flex;
  height: 100%;
}

.left-panel {
  flex: 1;
  min-width: 0;
  border-right: 1px solid #e8e8e8;
}

.right-panel {
  width: 480px;
  display: flex;
  flex-direction: column;
  background: white;
}

.form-actions {
  padding: 16px 24px;
  border-top: 1px solid #e8e8e8;
  background: white;
  display: flex;
  justify-content: center;
}

/* 移动端布局 */
.mobile-layout {
  display: none;
  flex-direction: column;
  height: 100%;
}

.mobile-actions {
  padding: 16px;
  background: white;
  border-top: 1px solid #e8e8e8;
}

.mt-2 {
  margin-top: 8px;
}

/* 响应式 */
@media (max-width: 768px) {
  .desktop-layout {
    display: none;
  }

  .mobile-layout {
    display: flex;
  }

  .workbench-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .header-left,
  .header-right {
    width: 100%;
  }

  .header-right {
    display: flex;
    justify-content: flex-end;
  }
}

@media (max-width: 1200px) {
  .right-panel {
    width: 400px;
  }
}
</style>
