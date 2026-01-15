<script setup lang="ts">
/**
 * 编辑器工具栏
 * 提供格式化按钮和常用操作
 */
import type { Editor } from '@tiptap/vue-3'

const props = defineProps<{
  editor: Editor
}>()

// 设置链接
const setLink = () => {
  const previousUrl = props.editor.getAttributes('link').href
  const url = window.prompt('输入链接地址', previousUrl)
  
  if (url === null) return
  
  if (url === '') {
    props.editor.chain().focus().extendMarkRange('link').unsetLink().run()
    return
  }
  
  props.editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
}

// 添加图片
const addImage = () => {
  const url = window.prompt('输入图片地址')
  
  if (url) {
    props.editor.chain().focus().setImage({ src: url }).run()
  }
}

// 插入表格
const insertTable = () => {
  props.editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
}

// 工具栏按钮组配置
const toolbarGroups = computed(() => [
  // 文本格式
  {
    key: 'format',
    items: [
      {
        icon: 'i-lucide-bold',
        title: '粗体 (Ctrl+B)',
        action: () => props.editor.chain().focus().toggleBold().run(),
        isActive: () => props.editor.isActive('bold'),
      },
      {
        icon: 'i-lucide-italic',
        title: '斜体 (Ctrl+I)',
        action: () => props.editor.chain().focus().toggleItalic().run(),
        isActive: () => props.editor.isActive('italic'),
      },
      {
        icon: 'i-lucide-strikethrough',
        title: '删除线',
        action: () => props.editor.chain().focus().toggleStrike().run(),
        isActive: () => props.editor.isActive('strike'),
      },
      {
        icon: 'i-lucide-code',
        title: '行内代码',
        action: () => props.editor.chain().focus().toggleCode().run(),
        isActive: () => props.editor.isActive('code'),
      },
    ],
  },
  // 标题
  {
    key: 'heading',
    items: [
      {
        icon: 'i-lucide-heading-1',
        title: '标题 1',
        action: () => props.editor.chain().focus().toggleHeading({ level: 1 }).run(),
        isActive: () => props.editor.isActive('heading', { level: 1 }),
      },
      {
        icon: 'i-lucide-heading-2',
        title: '标题 2',
        action: () => props.editor.chain().focus().toggleHeading({ level: 2 }).run(),
        isActive: () => props.editor.isActive('heading', { level: 2 }),
      },
      {
        icon: 'i-lucide-heading-3',
        title: '标题 3',
        action: () => props.editor.chain().focus().toggleHeading({ level: 3 }).run(),
        isActive: () => props.editor.isActive('heading', { level: 3 }),
      },
    ],
  },
  // 列表
  {
    key: 'list',
    items: [
      {
        icon: 'i-lucide-list',
        title: '无序列表',
        action: () => props.editor.chain().focus().toggleBulletList().run(),
        isActive: () => props.editor.isActive('bulletList'),
      },
      {
        icon: 'i-lucide-list-ordered',
        title: '有序列表',
        action: () => props.editor.chain().focus().toggleOrderedList().run(),
        isActive: () => props.editor.isActive('orderedList'),
      },
      {
        icon: 'i-lucide-list-checks',
        title: '任务列表',
        action: () => props.editor.chain().focus().toggleTaskList().run(),
        isActive: () => props.editor.isActive('taskList'),
      },
    ],
  },
  // 块级元素
  {
    key: 'block',
    items: [
      {
        icon: 'i-lucide-quote',
        title: '引用',
        action: () => props.editor.chain().focus().toggleBlockquote().run(),
        isActive: () => props.editor.isActive('blockquote'),
      },
      {
        icon: 'i-lucide-file-code',
        title: '代码块',
        action: () => props.editor.chain().focus().toggleCodeBlock().run(),
        isActive: () => props.editor.isActive('codeBlock'),
      },
      {
        icon: 'i-lucide-minus',
        title: '分割线',
        action: () => props.editor.chain().focus().setHorizontalRule().run(),
        isActive: () => false,
      },
    ],
  },
  // 插入
  {
    key: 'insert',
    items: [
      {
        icon: 'i-lucide-link',
        title: '链接',
        action: setLink,
        isActive: () => props.editor.isActive('link'),
      },
      {
        icon: 'i-lucide-image',
        title: '图片',
        action: addImage,
        isActive: () => false,
      },
      {
        icon: 'i-lucide-table',
        title: '表格',
        action: insertTable,
        isActive: () => props.editor.isActive('table'),
      },
    ],
  },
  // 历史
  {
    key: 'history',
    items: [
      {
        icon: 'i-lucide-undo',
        title: '撤销 (Ctrl+Z)',
        action: () => props.editor.chain().focus().undo().run(),
        isActive: () => false,
        disabled: () => !props.editor.can().undo(),
      },
      {
        icon: 'i-lucide-redo',
        title: '重做 (Ctrl+Shift+Z)',
        action: () => props.editor.chain().focus().redo().run(),
        isActive: () => false,
        disabled: () => !props.editor.can().redo(),
      },
    ],
  },
])
</script>

<template>
  <div class="editor-toolbar">
    <template v-for="(group, groupIndex) in toolbarGroups" :key="group.key">
      <div class="toolbar-group">
        <UButton
          v-for="item in group.items"
          :key="item.icon"
          :variant="item.isActive() ? 'solid' : 'ghost'"
          :icon="item.icon"
          :title="item.title"
          :disabled="item.disabled?.()"
          size="xs"
          color="neutral"
          @click="item.action"
        />
      </div>
      <div
        v-if="groupIndex < toolbarGroups.length - 1"
        class="toolbar-divider"
      />
    </template>
  </div>
</template>

<style scoped>
@reference "tailwindcss";

.editor-toolbar {
  @apply flex items-center gap-1 px-2 py-1.5 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 overflow-x-auto;
}

.toolbar-group {
  @apply flex items-center gap-0.5;
}

.toolbar-divider {
  @apply w-px h-5 bg-gray-300 dark:bg-gray-600 mx-1;
}
</style>
