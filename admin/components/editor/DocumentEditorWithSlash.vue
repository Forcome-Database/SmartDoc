<script setup lang="ts">
/**
 * 文档编辑器（带 Slash 命令）
 * 基于 md-editor-v3，增强 "/" 指令插入内容功能
 */
import { MdEditor, MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import type { SlashCommand } from './SlashCommandPanel.vue'

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

// 深色模式
const colorMode = useColorMode()
const theme = computed(() => colorMode.value === 'dark' ? 'dark' : 'light')

// 图片上传
const { upload: uploadImage } = useImageUpload()

// Slash 命令
const slashCommand = useSlashCommand()

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

// 编辑器引用
const editorRef = ref()
const editorElement = ref<HTMLElement>()
const currentCursorPos = ref(0)

// 保存事件
const handleSave = () => {
  emit('save')
}

// 图片上传处理
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
  
  callback(urls)
}

// 内容变化处理
const handleContentChange = (newContent: string) => {
  content.value = newContent
  
  // 检测 slash 命令（延迟执行，确保光标位置已更新）
  if (!props.readOnly) {
    nextTick(() => {
      checkSlashCommand(newContent)
    })
  }
}

// 获取 CodeMirror 光标位置
const getCursorPosition = (): number => {
  try {
    if (!editorElement.value) return 0
    
    // 方法1: 通过 cm-editor 元素获取 view
    const cmEditorEl = editorElement.value.querySelector('.cm-editor') as any
    
    // 尝试多种方式获取 CodeMirror state
    let cmState = null
    
    // 方式1: cmView.state
    if (cmEditorEl?.cmView?.state) {
      cmState = cmEditorEl.cmView.state
    }
    // 方式2: 通过 view 属性
    else if (cmEditorEl?.view?.state) {
      cmState = cmEditorEl.view.state
    }
    // 方式3: 通过 _view 属性
    else if (cmEditorEl?._view?.state) {
      cmState = cmEditorEl._view.state
    }
    
    if (cmState?.selection?.main) {
      return cmState.selection.main.head
    }
    
    // 回退：使用内容长度作为光标位置（假设光标在末尾）
    return content.value.length
  } catch (e) {
    console.warn('Failed to get cursor position:', e)
    return content.value.length
  }
}

// 检测 slash 命令
const checkSlashCommand = (newContent: string) => {
  try {
    // 获取真实光标位置
    const cursorPos = getCursorPosition()
    currentCursorPos.value = cursorPos
    
    // 检测是否触发 slash 命令
    const shouldShow = slashCommand.detectSlashCommand(newContent, cursorPos)
    
    if (shouldShow && editorElement.value) {
      // 获取光标屏幕位置
      const position = slashCommand.getCursorScreenPosition(editorElement.value)
      slashCommand.show(position.x, position.y)
    } else if (!shouldShow && slashCommand.state.visible) {
      slashCommand.hide()
    }
  } catch (e) {
    console.error('Failed to check slash command:', e)
  }
}

// 选择命令
const handleCommandSelect = (command: SlashCommand) => {
  try {
    const currentContent = content.value
    const slashPos = slashCommand.state.slashPosition
    
    if (slashPos === -1) {
      slashCommand.hide()
      return
    }
    
    // 计算要替换的范围（从 "/" 到光标位置）
    const beforeSlash = currentContent.substring(0, slashPos)
    const afterCursor = currentContent.substring(slashCommand.state.cursorPosition)
    
    // 执行命令，获取要插入的内容
    const insertContent = command.action()
    
    // 组合新内容
    const newContent = beforeSlash + insertContent + afterCursor
    
    // 更新内容
    content.value = newContent
    
    // 隐藏面板
    slashCommand.hide()
    
    // 聚焦编辑器
    nextTick(() => {
      focusEditor()
    })
  } catch (e) {
    console.error('Failed to insert command:', e)
    slashCommand.hide()
  }
}

// 关闭命令面板
const handleCommandClose = () => {
  slashCommand.hide()
}

// 聚焦编辑器
const focusEditor = () => {
  try {
    if (editorElement.value) {
      const cmEditor = editorElement.value.querySelector('.cm-content') as HTMLElement
      if (cmEditor) {
        cmEditor.focus()
      }
    }
  } catch (e) {
    console.error('Failed to focus editor:', e)
  }
}

// 监听编辑器挂载
onMounted(() => {
  nextTick(() => {
    if (editorRef.value?.$el) {
      editorElement.value = editorRef.value.$el
    }
  })
})

// 暴露编辑器实例
defineExpose({ 
  editor: editorRef,
  slashCommand,
})
</script>

<template>
  <div class="document-editor-with-slash">
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
      :placeholder="placeholder || '开始输入内容... 输入 / 打开命令面板'"
      previewTheme="vuepress"
      codeTheme="atom"
      language="zh-CN"
      :showCodeRowNumber="true"
      :autoFocus="true"
      :scrollAuto="true"
      class="editor-main"
      @onChange="handleContentChange"
      @onSave="handleSave"
      @onUploadImg="handleUploadImg"
    />

    <!-- Slash 命令面板 -->
    <EditorSlashCommandPanel
      :visible="slashCommand.state.visible"
      :position="slashCommand.state.position"
      :search-query="slashCommand.state.searchQuery"
      @select="handleCommandSelect"
      @close="handleCommandClose"
    />
  </div>
</template>

<style scoped>
@reference "tailwindcss";

.document-editor-with-slash {
  @apply w-full h-full relative;
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
