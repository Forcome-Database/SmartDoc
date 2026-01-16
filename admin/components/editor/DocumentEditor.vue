<script setup lang="ts">
/**
 * 文档编辑器
 * 基于 md-editor-v3，支持 Markdown 编辑和预览
 */
import { MdEditor, MdPreview, config } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'

const props = defineProps<{
  modelValue: string
  documentId?: string
  readOnly?: boolean
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'save': []
}>()

// 编辑器唯一标识
const editorId = computed(() => `doc-editor-${props.documentId || 'default'}`)

// 深色模式 - 通过检测 HTML 根元素的 class 来判断实际主题
const colorMode = useColorMode()
const isDark = ref(false)

// 监听主题变化
const updateTheme = () => {
  if (import.meta.client) {
    isDark.value = document.documentElement.classList.contains('dark')
  }
}

// 监听 colorMode 变化
watch(() => colorMode.value, () => {
  nextTick(updateTheme)
}, { immediate: true })

// 初始化时检测
onMounted(() => {
  updateTheme()
  // 监听 class 变化（处理系统主题切换）
  const observer = new MutationObserver(updateTheme)
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
  onUnmounted(() => observer.disconnect())
})

const theme = computed(() => isDark.value ? 'dark' : 'light')

// 图片上传
const { upload: uploadImage, uploading: imageUploading } = useImageUpload()

// 内容双向绑定
const content = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 工具栏配置
const toolbars = [
  'bold',
  'underline',
  'italic',
  'strikeThrough',
  '-',
  'title',
  'sub',
  'sup',
  'quote',
  'unorderedList',
  'orderedList',
  'task',
  '-',
  'codeRow',
  'code',
  'link',
  'image',
  'table',
  'mermaid',
  'katex',
  '-',
  'revoke',
  'next',
  'save',
  '=',
  'pageFullscreen',
  'fullscreen',
  'preview',
  'previewOnly',
  'catalog',
] as const

// 保存事件
const handleSave = () => {
  emit('save')
}

// 图片上传处理 - 上传到 MinIO 存储
const handleUploadImg = async (
  files: File[],
  callback: (urls: string[]) => void
) => {
  const urls: string[] = []
  
  for (const file of files) {
    const result = await uploadImage(file)
    if (result?.url) {
      urls.push(result.url)
    }
  }
  
  // 返回上传成功的图片 URL
  callback(urls)
}

// 编辑器引用
const editorRef = ref()

// 暴露编辑器实例
defineExpose({ editor: editorRef })
</script>

<template>
  <div class="document-editor">
    <!-- 只读模式：预览 -->
    <MdPreview
      v-if="readOnly"
      :id="editorId"
      :modelValue="content"
      :theme="theme"
      previewTheme="vuepress"
      codeTheme="atom"
      class="editor-preview"
    />

    <!-- 编辑模式 -->
    <MdEditor
      v-else
      ref="editorRef"
      :id="editorId"
      v-model="content"
      :theme="theme"
      :toolbars="toolbars"
      :placeholder="placeholder || '开始输入内容...'"
      previewTheme="vuepress"
      codeTheme="atom"
      language="zh-CN"
      :showCodeRowNumber="true"
      :autoFocus="true"
      :scrollAuto="true"
      class="editor-main"
      @onSave="handleSave"
      @onUploadImg="handleUploadImg"
    />
  </div>
</template>

<style scoped>
@reference "tailwindcss";

.document-editor {
  @apply w-full h-full;
}

.editor-main,
.editor-preview {
  @apply w-full h-full;
}

/* 编辑器固定高度，内部滚动 */
:deep(.md-editor) {
  width: 100% !important;
  height: 100% !important;
  border: none !important;
}

:deep(.md-editor-dark) {
  --md-bk-color: transparent;
}

/* 去掉输入区域的高亮边框 */
:deep(.md-editor-input-wrapper) {
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
}

:deep(.cm-editor),
:deep(.cm-editor.cm-focused),
:deep(.cm-editor *:focus),
:deep(.cm-editor *:focus-visible) {
  outline: none !important;
  box-shadow: none !important;
  ring: none !important;
  --tw-ring-shadow: none !important;
  --tw-ring-offset-shadow: none !important;
}

:deep(.cm-content),
:deep(.cm-content:focus),
:deep(.cm-content:focus-visible) {
  outline: none !important;
  box-shadow: none !important;
}

:deep(.cm-scroller) {
  outline: none !important;
}
</style>
