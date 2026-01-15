<script setup lang="ts">
/**
 * Slash 命令测试页面
 * 用于测试和演示 "/" 指令功能
 */

definePageMeta({
  layout: 'default',
  middleware: ['dev-only', 'auth'],
})

const content = ref(`# Slash 命令测试

欢迎使用增强版 Markdown 编辑器！

## 如何使用

1. 在新行输入 \`/\` 打开命令面板
2. 使用 ↑↓ 键导航
3. 按 Enter 选择命令
4. 按 Esc 关闭面板

## 试试这些命令

- \`/h1\` - 插入一级标题
- \`/code\` - 插入代码块
- \`/table\` - 插入表格
- \`/task\` - 插入任务列表

## 开始编辑

在下方输入 \`/\` 试试看...

`)

const toast = useToast()

const handleSave = () => {
  toast.add({
    title: '保存成功',
    description: '文档已保存',
    color: 'success',
  })
  console.log('Content:', content.value)
}
</script>

<template>
  <div class="h-screen flex flex-col bg-gray-50 dark:bg-gray-950">
    <!-- 顶部栏 -->
    <div class="flex-shrink-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
      <div class="px-6 py-4">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
              Slash 命令测试
            </h1>
            <p class="mt-1 text-sm text-gray-500">
              输入 "/" 打开命令面板，快速插入内容
            </p>
          </div>
          
          <div class="flex items-center gap-3">
            <UButton
              variant="ghost"
              color="neutral"
              icon="i-lucide-arrow-left"
              to="/content"
            >
              返回
            </UButton>
            <UButton
              color="primary"
              icon="i-lucide-save"
              @click="handleSave"
            >
              保存
            </UButton>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑器 -->
    <div class="flex-1 min-h-0 p-6">
      <div class="h-full bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden">
        <ClientOnly>
          <EditorDocumentEditorWithSlash
            v-model="content"
            document-id="test-slash"
            placeholder="开始输入... 试试输入 / 打开命令面板"
            class="h-full"
            @save="handleSave"
          />
          <template #fallback>
            <div class="flex items-center justify-center h-full">
              <UIcon name="i-lucide-loader-2" class="w-8 h-8 animate-spin text-primary-500" />
              <p class="ml-3 text-gray-500">加载编辑器...</p>
            </div>
          </template>
        </ClientOnly>
      </div>
    </div>

    <!-- 提示卡片 -->
    <div class="flex-shrink-0 p-6 pt-0">
      <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div class="flex items-start gap-3">
          <UIcon name="i-lucide-lightbulb" class="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div class="flex-1">
            <h3 class="text-sm font-semibold text-blue-900 dark:text-blue-100">
              快捷键提示
            </h3>
            <ul class="mt-2 text-sm text-blue-700 dark:text-blue-300 space-y-1">
              <li><kbd class="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900 rounded text-xs">/</kbd> 打开命令面板</li>
              <li><kbd class="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900 rounded text-xs">↑</kbd> <kbd class="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900 rounded text-xs">↓</kbd> 导航命令</li>
              <li><kbd class="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900 rounded text-xs">Enter</kbd> 选择命令</li>
              <li><kbd class="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900 rounded text-xs">Esc</kbd> 关闭面板</li>
              <li><kbd class="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900 rounded text-xs">Cmd/Ctrl</kbd> + <kbd class="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900 rounded text-xs">S</kbd> 保存文档</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
kbd {
  font-family: 'JetBrains Mono', monospace;
}
</style>
