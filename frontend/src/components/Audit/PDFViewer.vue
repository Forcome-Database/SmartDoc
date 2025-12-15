<template>
  <div class="pdf-viewer">
    <!-- 工具栏 -->
    <div class="pdf-toolbar">
      <a-space>
        <!-- 缩放控制 -->
        <a-button-group>
          <a-button @click="zoomOut" :disabled="scale <= 0.5">
            <template #icon><ZoomOutOutlined /></template>
          </a-button>
          <a-button disabled>{{ Math.round(scale * 100) }}%</a-button>
          <a-button @click="zoomIn" :disabled="scale >= 2">
            <template #icon><ZoomInOutlined /></template>
          </a-button>
        </a-button-group>

        <!-- 旋转控制 -->
        <a-button @click="rotateLeft">
          <template #icon><RotateLeftOutlined /></template>
        </a-button>
        <a-button @click="rotateRight">
          <template #icon><RotateRightOutlined /></template>
        </a-button>

        <a-divider type="vertical" />

        <!-- 分页控制 -->
        <a-button @click="prevPage" :disabled="currentPage <= 1">
          <template #icon><LeftOutlined /></template>
          上一页
        </a-button>
        
        <a-input-number
          v-model:value="pageInput"
          :min="1"
          :max="totalPages"
          size="small"
          style="width: 60px"
          @pressEnter="goToPage"
        />
        <span class="page-info">/ {{ totalPages }}</span>
        
        <a-button @click="nextPage" :disabled="currentPage >= totalPages">
          下一页
          <template #icon><RightOutlined /></template>
        </a-button>
      </a-space>
    </div>

    <!-- PDF内容区域 -->
    <div class="pdf-content" ref="contentRef">
      <a-spin :spinning="loading" tip="加载中...">
        <div 
          class="pdf-page-container"
          :style="{
            transform: `scale(${scale}) rotate(${rotation}deg)`,
            transformOrigin: 'center top'
          }"
        >
          <!-- PDF页面图片 -->
          <img
            v-if="currentPageUrl"
            :src="currentPageUrl"
            :alt="`Page ${currentPage}`"
            class="pdf-page-image"
            @load="onImageLoad"
            @error="onImageError"
          />

          <!-- OCR高亮区域 -->
          <div
            v-for="(box, index) in highlightBoxes"
            :key="index"
            class="ocr-highlight-box"
            :class="{ active: box.active }"
            :style="getBoxStyle(box)"
            @click="onBoxClick(box)"
          />

          <!-- 文本选择层 -->
          <div
            v-if="enableTextSelection"
            class="text-selection-layer"
            @mousedown="startSelection"
            @mousemove="updateSelection"
            @mouseup="endSelection"
          >
            <div
              v-if="selectionBox"
              class="selection-box"
              :style="getSelectionStyle()"
            />
          </div>
        </div>
      </a-spin>

      <!-- 懒加载占位 -->
      <div v-if="totalPages > 50 && !currentPageUrl" class="lazy-placeholder">
        <a-empty description="点击加载页面" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import {
  ZoomInOutlined,
  ZoomOutOutlined,
  RotateLeftOutlined,
  RotateRightOutlined,
  LeftOutlined,
  RightOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { auditAPI } from '@/api/audit'

/**
 * PDF预览器组件
 * 支持分页、缩放、旋转、OCR高亮、文本选择
 */

const props = defineProps({
  // 任务ID
  taskId: {
    type: String,
    required: true
  },
  // 总页数
  totalPages: {
    type: Number,
    required: true
  },
  // 初始页码
  initialPage: {
    type: Number,
    default: 1
  },
  // OCR结果（用于高亮）
  ocrResult: {
    type: Object,
    default: () => ({})
  },
  // 是否启用文本选择
  enableTextSelection: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['page-change', 'box-click', 'text-selected'])

// 状态
const loading = ref(false)
const currentPage = ref(props.initialPage)
const pageInput = ref(props.initialPage)
const scale = ref(1)
const rotation = ref(0)
const currentPageUrl = ref(null)
const contentRef = ref(null)

// 高亮框
const highlightBoxes = ref([])

// 文本选择
const selectionBox = ref(null)
const isSelecting = ref(false)
const selectionStart = ref(null)

// 图片加载状态
const imageLoaded = ref(false)

// 监听页码变化
watch(currentPage, (newPage) => {
  pageInput.value = newPage
  loadPage(newPage)
  emit('page-change', newPage)
})

// 监听OCR结果变化
watch(() => props.ocrResult, (newResult) => {
  updateHighlightBoxes(newResult)
}, { deep: true })

/**
 * 加载页面
 */
async function loadPage(page) {
  if (page < 1 || page > props.totalPages) return

  loading.value = true
  imageLoaded.value = false

  // 释放之前的blob URL
  if (currentPageUrl.value && currentPageUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(currentPageUrl.value)
  }

  try {
    // 使用auditAPI获取预览图（带认证）
    const blob = await auditAPI.getPagePreview(props.taskId, page)
    currentPageUrl.value = URL.createObjectURL(blob)
  } catch (error) {
    message.error('加载页面失败')
    console.error('Load page error:', error)
    currentPageUrl.value = null
  } finally {
    loading.value = false
  }
}

/**
 * 更新高亮框
 */
function updateHighlightBoxes(ocrResult) {
  if (!ocrResult || !ocrResult.page_results) return

  const pageResult = ocrResult.page_results.find(p => p.page === currentPage.value)
  if (!pageResult || !pageResult.boxes) return

  highlightBoxes.value = pageResult.boxes.map(box => ({
    ...box,
    active: false
  }))
}

/**
 * 获取高亮框样式
 */
function getBoxStyle(box) {
  return {
    left: `${box.x}px`,
    top: `${box.y}px`,
    width: `${box.width}px`,
    height: `${box.height}px`
  }
}

/**
 * 高亮框点击
 */
function onBoxClick(box) {
  // 取消其他框的激活状态
  highlightBoxes.value.forEach(b => b.active = false)
  box.active = true
  
  emit('box-click', {
    text: box.text,
    page: currentPage.value,
    box
  })
}

/**
 * 缩放控制
 */
function zoomIn() {
  scale.value = Math.min(scale.value + 0.1, 2)
}

function zoomOut() {
  scale.value = Math.max(scale.value - 0.1, 0.5)
}

/**
 * 旋转控制
 */
function rotateLeft() {
  rotation.value = (rotation.value - 90) % 360
}

function rotateRight() {
  rotation.value = (rotation.value + 90) % 360
}

/**
 * 分页控制
 */
function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

function nextPage() {
  if (currentPage.value < props.totalPages) {
    currentPage.value++
  }
}

function goToPage() {
  if (pageInput.value >= 1 && pageInput.value <= props.totalPages) {
    currentPage.value = pageInput.value
  } else {
    pageInput.value = currentPage.value
    message.warning('页码超出范围')
  }
}

/**
 * 文本选择
 */
function startSelection(e) {
  if (!props.enableTextSelection) return

  isSelecting.value = true
  const rect = e.currentTarget.getBoundingClientRect()
  selectionStart.value = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  }
  selectionBox.value = {
    x: selectionStart.value.x,
    y: selectionStart.value.y,
    width: 0,
    height: 0
  }
}

function updateSelection(e) {
  if (!isSelecting.value) return

  const rect = e.currentTarget.getBoundingClientRect()
  const currentX = e.clientX - rect.left
  const currentY = e.clientY - rect.top

  selectionBox.value = {
    x: Math.min(selectionStart.value.x, currentX),
    y: Math.min(selectionStart.value.y, currentY),
    width: Math.abs(currentX - selectionStart.value.x),
    height: Math.abs(currentY - selectionStart.value.y)
  }
}

function endSelection() {
  if (!isSelecting.value) return

  isSelecting.value = false

  // 查找选中区域内的文本
  const selectedText = getTextInSelection(selectionBox.value)
  if (selectedText) {
    emit('text-selected', selectedText)
  }

  // 清除选择框
  setTimeout(() => {
    selectionBox.value = null
  }, 100)
}

/**
 * 获取选择区域内的文本
 */
function getTextInSelection(box) {
  if (!box || box.width < 10 || box.height < 10) return null

  const texts = []
  highlightBoxes.value.forEach(ocrBox => {
    // 检查OCR框是否在选择区域内
    if (isBoxIntersect(box, ocrBox)) {
      texts.push(ocrBox.text)
    }
  })

  return texts.join(' ')
}

/**
 * 检查两个框是否相交
 */
function isBoxIntersect(box1, box2) {
  return !(
    box1.x + box1.width < box2.x ||
    box2.x + box2.width < box1.x ||
    box1.y + box1.height < box2.y ||
    box2.y + box2.height < box1.y
  )
}

/**
 * 获取选择框样式
 */
function getSelectionStyle() {
  if (!selectionBox.value) return {}

  return {
    left: `${selectionBox.value.x}px`,
    top: `${selectionBox.value.y}px`,
    width: `${selectionBox.value.width}px`,
    height: `${selectionBox.value.height}px`
  }
}

/**
 * 图片加载完成
 */
function onImageLoad() {
  imageLoaded.value = true
  loading.value = false
}

/**
 * 图片加载失败
 */
function onImageError() {
  // 不显示错误消息，因为后端会返回占位图片
  console.warn('图片加载失败，可能是文件不存在')
  loading.value = false
}

/**
 * 跳转到指定页面
 */
function jumpToPage(page) {
  if (page >= 1 && page <= props.totalPages) {
    currentPage.value = page
  }
}

// 暴露方法给父组件
defineExpose({
  jumpToPage,
  currentPage
})

// 初始化
onMounted(() => {
  loadPage(currentPage.value)
})

// 清理
onUnmounted(() => {
  if (currentPageUrl.value && currentPageUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(currentPageUrl.value)
  }
})
</script>

<style scoped>
.pdf-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f5f5;
}

.pdf-toolbar {
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: center;
}

.page-info {
  margin: 0 8px;
  color: #666;
}

.pdf-content {
  flex: 1;
  overflow: auto;
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.pdf-page-container {
  position: relative;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.pdf-page-image {
  display: block;
  max-width: 100%;
  height: auto;
}

/* OCR高亮框 */
.ocr-highlight-box {
  position: absolute;
  border: 2px solid rgba(24, 144, 255, 0.5);
  background: rgba(24, 144, 255, 0.1);
  cursor: pointer;
  transition: all 0.2s;
}

.ocr-highlight-box:hover {
  border-color: rgba(24, 144, 255, 0.8);
  background: rgba(24, 144, 255, 0.2);
}

.ocr-highlight-box.active {
  border-color: #1890ff;
  background: rgba(24, 144, 255, 0.3);
  z-index: 10;
}

/* 文本选择层 */
.text-selection-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  cursor: crosshair;
  z-index: 5;
}

.selection-box {
  position: absolute;
  border: 2px dashed #52c41a;
  background: rgba(82, 196, 26, 0.1);
  pointer-events: none;
}

/* 懒加载占位 */
.lazy-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

/* 响应式 */
@media (max-width: 768px) {
  .pdf-toolbar {
    flex-wrap: wrap;
    gap: 8px;
  }

  .pdf-content {
    padding: 10px;
  }
}
</style>
