<template>
  <div class="review-detail">
    <!-- 顶部操作栏 -->
    <div class="detail-header">
      <div class="header-left">
        <a-button @click="goBack">
          <template #icon><ArrowLeftOutlined /></template>
          返回列表
        </a-button>
        <h2>审核详情</h2>
        <a-tag v-if="currentTask" color="blue">
          任务ID: {{ currentTask.id }}
        </a-tag>
        <a-tag v-if="currentTask" :color="getStatusColor(currentTask.status)">
          {{ getStatusText(currentTask.status) }}
        </a-tag>
      </div>
      <div class="header-right">
        <a-space>
          <a-button @click="refreshTask">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="detail-content">
      <a-spin :spinning="loading" tip="加载中..." wrapperClassName="full-height-spin">
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
              <!-- 任务信息卡片 -->
              <div class="task-info-card">
                <a-descriptions :column="2" size="small" bordered>
                  <a-descriptions-item label="文件名">
                    {{ currentTask.file_name }}
                  </a-descriptions-item>
                  <a-descriptions-item label="页数">
                    {{ currentTask.page_count }} 页
                  </a-descriptions-item>
                  <a-descriptions-item label="规则">
                    {{ currentTask.rule_name || '未知规则' }}
                  </a-descriptions-item>
                  <a-descriptions-item label="创建时间">
                    {{ formatDateTime(currentTask.created_at) }}
                  </a-descriptions-item>
                </a-descriptions>
              </div>

              <!-- 审核原因 -->
              <div v-if="currentTask.audit_reasons && currentTask.audit_reasons.length > 0" class="audit-reasons-card">
                <div class="audit-reasons-header">
                  <WarningOutlined class="warning-icon" />
                  <span>触发人工审核原因</span>
                </div>
                <div class="audit-reasons-list">
                  <div v-for="(reason, index) in currentTask.audit_reasons" :key="index" class="audit-reason-item">
                    <span class="reason-index">{{ index + 1 }}</span>
                    <span class="reason-content">{{ formatAuditReason(reason) }}</span>
                  </div>
                </div>
              </div>

              <!-- 数据表单 -->
              <DataFormV2
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
                <DataFormV2
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
        <a-empty v-else description="任务不存在或已处理" />
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
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  ArrowLeftOutlined,
  ReloadOutlined,
  CheckOutlined,
  CloseOutlined,
  SaveOutlined,
  WarningOutlined
} from '@ant-design/icons-vue'
import PDFViewer from '@/components/Audit/PDFViewer.vue'
import DataFormV2 from '@/components/Audit/DataFormV2.vue'
import { auditAPI } from '@/api/audit'
import {
  saveDraftToLocal,
  loadDraftFromLocal,
  removeDraftFromLocal,
  createDebouncedSave,
  cleanExpiredDrafts
} from '@/utils/draftManager'
import dayjs from 'dayjs'

/**
 * 审核详情页面
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
const mobileTab = ref('pdf')

// 组件引用
const pdfViewerRef = ref(null)
const dataFormRef = ref(null)
const mobilePdfViewerRef = ref(null)
const mobileDataFormRef = ref(null)

// 驳回对话框
const rejectModalVisible = ref(false)
const rejectReason = ref('')

/**
 * 返回列表
 */
function goBack() {
  router.push('/audit')
}

/**
 * 规范化提取数据
 * 将对象格式的字段值（如 { value: "xxx", confidence: 0.9 }）转换为简单值
 */
function normalizeExtractedData(data) {
  if (!data || typeof data !== 'object') {
    return {}
  }
  
  const result = {}
  for (const [key, value] of Object.entries(data)) {
    if (value === null || value === undefined) {
      result[key] = ''
    } else if (typeof value === 'object' && !Array.isArray(value)) {
      // 如果是对象且有 value 属性，提取 value
      if ('value' in value) {
        result[key] = value.value
      } else {
        // 否则保持原样（可能是嵌套对象）
        result[key] = value
      }
    } else {
      // 简单值或数组，直接使用
      result[key] = value
    }
  }
  return result
}

/**
 * 加载任务详情
 */
async function loadTaskDetail(taskId) {
  loading.value = true
  console.log('loadTaskDetail started, taskId:', taskId)

  try {
    const response = await auditAPI.getTaskDetail(taskId)
    console.log('Task detail response:', response)
    
    if (!response) {
      throw new Error('返回数据为空')
    }
    
    currentTask.value = response
    console.log('currentTask set:', currentTask.value)

    // 解析Schema（如果有rule_config）
    if (currentTask.value.rule_config && currentTask.value.rule_config.schema) {
      taskSchema.value = currentTask.value.rule_config.schema
    } else {
      taskSchema.value = {}
    }

    // 加载提取数据（确保不为null）
    // 处理可能的对象格式数据（如 { value: "xxx", confidence: 0.9 }）
    const rawData = currentTask.value.extracted_data || {}
    formData.value = normalizeExtractedData(rawData)
    console.log('formData set:', formData.value)

    // 尝试加载草稿
    try {
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
    } catch (draftError) {
      console.error('Draft loading error:', draftError)
    }
  } catch (error) {
    message.error('加载任务详情失败: ' + (error.message || '未知错误'))
    console.error('Load task detail error:', error)
  } finally {
    console.log('loadTaskDetail finally, setting loading to false')
    loading.value = false
    console.log('loading is now:', loading.value)
  }
}

/**
 * 刷新当前任务
 */
async function refreshTask() {
  const taskId = route.query.taskId
  if (taskId) {
    await loadTaskDetail(taskId)
  }
}

/**
 * OCR框点击
 */
function onOcrBoxClick(data) {
  console.log('OCR box clicked:', data)
}

/**
 * 文本选中
 */
function onTextSelected(text) {
  if (!text) return

  Modal.confirm({
    title: '选中文本',
    content: `已选中文本：${text}`,
    okText: '填入当前字段',
    cancelText: '取消',
    onOk: () => {
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
  debouncedSaveDraft()
}

/**
 * 保存草稿（防抖）
 */
const debouncedSaveDraft = createDebouncedSave(async () => {
  if (!currentTask.value) return

  saveDraftToLocal(currentTask.value.id, formData.value)

  try {
    // 后端期望格式: { extracted_data: {...} }
    await auditAPI.saveDraft(currentTask.value.id, { extracted_data: formData.value })
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
    // 后端期望格式: { extracted_data: {...} }
    await auditAPI.saveDraft(currentTask.value.id, { extracted_data: formData.value })
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
    removeDraftFromLocal(currentTask.value.id)
    
    // 返回列表
    router.push('/audit')
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
    removeDraftFromLocal(currentTask.value.id)
    
    // 返回列表
    router.push('/audit')
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

/**
 * 格式化日期时间
 */
function formatDateTime(dateStr) {
  if (!dateStr) return '-'
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

/**
 * 格式化审核原因
 * 支持字符串和对象两种格式
 */
function formatAuditReason(reason) {
  if (!reason) return '-'
  
  // 如果是字符串，直接返回
  if (typeof reason === 'string') {
    return reason
  }
  
  // 如果是对象，提取message或组合字段信息
  if (typeof reason === 'object') {
    if (reason.message) {
      return reason.field ? `${reason.field}: ${reason.message}` : reason.message
    }
    if (reason.reason) {
      return reason.reason
    }
    // 根据type生成描述
    if (reason.type === 'validation_error') {
      return `校验失败: ${reason.field || '未知字段'}`
    }
    if (reason.type === 'confidence_low') {
      return `置信度低: ${reason.field || '未知字段'}`
    }
    // 默认返回JSON字符串
    return JSON.stringify(reason)
  }
  
  return String(reason)
}

// 初始化
onMounted(async () => {
  cleanExpiredDrafts()

  const taskId = route.query.taskId
  if (taskId) {
    await loadTaskDetail(taskId)
  } else {
    message.error('缺少任务ID参数')
    router.push('/audit')
  }
})

// 清理
onUnmounted(() => {
  // 清理逻辑
})
</script>

<style scoped>
.review-detail {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f0f2f5;
}

.detail-header {
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

.detail-content {
  flex: 1;
  overflow: hidden;
}

/* 确保 a-spin 占满高度 */
.detail-content :deep(.ant-spin-nested-loading),
.detail-content :deep(.ant-spin-container) {
  height: 100%;
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
  width: 520px;
  display: flex;
  flex-direction: column;
  background: white;
  overflow: hidden;
  position: relative;
}

.task-info-card {
  padding: 16px 24px;
  border-bottom: 1px solid #e8e8e8;
  flex-shrink: 0;
}

.audit-reasons-card {
  margin: 12px 16px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #fffbe6 0%, #fff7e6 100%);
  border: 1px solid #ffe58f;
  border-radius: 8px;
  flex-shrink: 0;
}

.audit-reasons-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
  color: #d48806;
  margin-bottom: 10px;
}

.audit-reasons-header .warning-icon {
  font-size: 16px;
}

.audit-reasons-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.audit-reason-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 13px;
  color: #8c6d1f;
  line-height: 1.5;
}

.audit-reason-item .reason-index {
  width: 20px;
  height: 20px;
  background: #faad14;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.audit-reason-item .reason-content {
  flex: 1;
}

/* 数据表单区域需要可滚动，并为底部按钮留出空间 */
.right-panel :deep(.data-form-v2) {
  flex: 1;
  overflow: hidden;
  padding-bottom: 80px;
}

.form-actions {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px 24px;
  border-top: 1px solid #e8e8e8;
  background: white;
  display: flex;
  justify-content: center;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.06);
  z-index: 10;
}

/* 移动端布局 */
.mobile-layout {
  display: none;
  flex-direction: column;
  height: 100%;
}

.mobile-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  background: white;
  border-top: 1px solid #e8e8e8;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.06);
  z-index: 10;
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

  .detail-header {
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
    width: 440px;
  }
}
</style>
