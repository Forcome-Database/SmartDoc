<script setup lang="ts">
/**
 * 文档编辑页面
 * 集成 DocumentEditor 组件，实现文档加载、保存和版本管理
 * 
 * Requirements: 3.1, 3.7, 3.9, 5.3, 5.6, 8.5
 */
import type { DocumentStatus } from '~/types'
import { getPublishStatusDisplay, type PublishStatus } from '~/composables/usePublish'
import { getModifierKey } from '~/composables/useKeyboardShortcuts'

definePageMeta({
  middleware: ['auth'],
})

const route = useRoute()
const toast = useToast()

// 获取修饰键显示
const modifierKey = getModifierKey()

// 文档 ID
const documentId = computed(() => route.params.id as string)

// 文档数据
const { data: document, pending: loading, error, refresh } = await useFetch(
  () => `/api/documents/${documentId.value}`,
  {
    key: `document-${documentId.value}`,
  }
)

// 发布功能
const { getPublishStatus } = useDocumentPublish(documentId)

// 发布对话框
const showPublishDialog = ref(false)

// 翻译对话框
const showTranslationDialog = ref(false)

// 编辑器内容
const editorContent = ref('')

// 文档标题（可编辑）
const documentTitle = ref('')

// 是否已初始化（避免保存后刷新导致内容重置）
const isInitialized = ref(false)

// 初始化编辑器内容（仅首次加载时设置）
watch(document, (doc) => {
  if (doc && !isInitialized.value) {
    editorContent.value = doc.content || ''
    documentTitle.value = doc.title || ''
    isInitialized.value = true
  }
}, { immediate: true })

// 自动保存 - 1分钟间隔
const { 
  status: saveStatus, 
  hasUnsavedChanges, 
  statusText, 
  statusIcon, 
  statusColor,
  markChanged,
  save: triggerSave,
  reset: resetSaveStatus,
} = useAutoSave(
  async () => {
    await saveDocument()
  },
  {
    debounceMs: 60000,
    savedDuration: 3000,
  }
)

// 保存文档（仅覆盖当前版本，不产生版本记录）
const saveDocument = async (shouldRefresh = false) => {
  if (!document.value) return

  try {
    const result = await $fetch(`/api/documents/${documentId.value}`, {
      method: 'PATCH',
      body: {
        title: documentTitle.value,
        content: editorContent.value,
        createVersion: false, // 不创建版本记录
      },
    })

    // 更新本地文档状态（保存后 hasUnpublishedChanges 会变为 true）
    if (document.value && result) {
      document.value = { ...document.value, ...result }
    }

    // 仅在需要时刷新文档数据（如手动保存）
    if (shouldRefresh) {
      await refresh()
    }
  } catch (e) {
    const errorMessage = e instanceof Error ? e.message : '保存失败'
    toast.add({
      title: '保存失败',
      description: errorMessage,
      color: 'error',
    })
    throw e
  }
}

// 内容变化处理
const handleContentChange = (content: string) => {
  editorContent.value = content
  markChanged()
}

// 标题变化处理
const handleTitleChange = () => {
  markChanged()
}

// 手动保存（Ctrl+S）
const handleSave = async () => {
  await saveDocument(undefined, true) // 手动保存时刷新
  toast.add({
    title: '保存成功',
    color: 'success',
  })
}

// 版本历史面板
const showVersionHistory = ref(false)

// 计算发布状态 - 基于数据库字段判断，不依赖前端编辑状态
const publishStatus = computed<PublishStatus>(() => {
  if (!document.value) return 'unpublished'
  return getPublishStatus(
    document.value.status,
    document.value.publishedVersion,
    document.value.currentVersion || 1,
    document.value.hasUnpublishedChanges
  )
})

// 发布状态显示
const publishStatusDisplay = computed(() => getPublishStatusDisplay(publishStatus.value))

// 发布成功后刷新
const handlePublished = async () => {
  await refresh()
  toast.add({
    title: '发布成功',
    color: 'success',
  })
}

// 翻译保存成功后处理
const handleTranslationSaved = async (data: { document: any; isUpdate: boolean }) => {
  // 可以选择跳转到翻译后的文档
  // navigateTo(`/documents/${data.document.id}`)
}

// 状态颜色映射
const statusColorMap: Record<DocumentStatus, string> = {
  draft: 'warning',
  published: 'success',
  archived: 'neutral',
}

// 状态文本映射
const statusTextMap: Record<DocumentStatus, string> = {
  draft: '草稿',
  published: '已发布',
  archived: '已归档',
}

// 面包屑导航
const breadcrumbItems = computed(() => {
  const items = [
    { label: '首页', to: '/' },
    { label: '文档', to: '/documents' },
  ]
  
  if (document.value?.category) {
    const categoryTitle = document.value.category.titles?.[document.value.locale?.code || 'zh'] 
      || document.value.category.slug
    items.push({ label: categoryTitle })
  }
  
  if (document.value?.title) {
    items.push({ label: document.value.title })
  }
  
  return items
})
</script>

<template>
  <div class="h-full flex flex-col overflow-hidden">
    <!-- 加载状态 -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <UIcon name="i-lucide-loader-2" class="w-8 h-8 animate-spin text-primary-500" />
        <p class="mt-2 text-gray-500">加载中...</p>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <UIcon name="i-lucide-alert-circle" class="w-12 h-12 text-red-500 mx-auto" />
        <h2 class="mt-4 text-lg font-semibold text-gray-900 dark:text-white">加载失败</h2>
        <p class="mt-2 text-gray-500">{{ error.message || '无法加载文档' }}</p>
        <UButton class="mt-4" @click="refresh()">
          重试
        </UButton>
      </div>
    </div>

    <!-- 文档编辑器 -->
    <template v-else-if="document">
      <!-- 顶部工具栏 -->
      <div class="flex-shrink-0 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div class="px-4 py-3">
          <!-- 面包屑 -->
          <UBreadcrumb :items="breadcrumbItems" class="mb-3" />
          
          <!-- 标题和操作 -->
          <div class="flex items-center justify-between gap-4">
            <div class="flex-1 min-w-0">
              <!-- 可编辑标题 -->
              <input
                v-model="documentTitle"
                type="text"
                class="w-full text-xl font-semibold bg-transparent border-none outline-none text-gray-900 dark:text-white placeholder-gray-400 focus:ring-0"
                placeholder="文档标题"
                @input="handleTitleChange"
              />
              
              <!-- 元信息 -->
              <div class="flex items-center gap-4 mt-1 text-sm text-gray-500">
                <!-- 状态 -->
                <UBadge 
                  :color="statusColorMap[document.status as DocumentStatus]" 
                  variant="subtle"
                  size="xs"
                >
                  {{ statusTextMap[document.status as DocumentStatus] }}
                </UBadge>
                
                <!-- 语言 -->
                <span class="flex items-center gap-1">
                  <UIcon name="i-lucide-globe" class="w-3.5 h-3.5" />
                  {{ document.locale?.nativeName || document.locale?.name }}
                </span>
                
                <!-- 版本 -->
                <span class="flex items-center gap-1">
                  <UIcon name="i-lucide-git-branch" class="w-3.5 h-3.5" />
                  v{{ document.currentVersion || 1 }}
                </span>
                
                <!-- 作者 -->
                <span class="flex items-center gap-1">
                  <UAvatar 
                    :src="document.author?.avatar" 
                    :alt="document.author?.name"
                    size="2xs"
                  />
                  {{ document.author?.name }}
                </span>
              </div>
            </div>
            
            <!-- 操作按钮 -->
            <div class="flex items-center gap-2">
              <!-- 保存状态 -->
              <div 
                v-if="saveStatus !== 'idle'" 
                :class="['flex items-center gap-1.5 text-sm', statusColor]"
              >
                <UIcon 
                  :name="statusIcon" 
                  :class="['w-4 h-4', saveStatus === 'saving' ? 'animate-spin' : '']" 
                />
                <span>{{ statusText }}</span>
              </div>
              
              <!-- 发布状态指示 -->
              <UBadge
                :color="publishStatusDisplay.color"
                variant="subtle"
                size="sm"
                class="cursor-pointer"
                @click="showPublishDialog = true"
              >
                <UIcon :name="publishStatusDisplay.icon" class="w-3.5 h-3.5 mr-1" />
                {{ publishStatusDisplay.label }}
              </UBadge>
              
              <!-- 版本历史 -->
              <UButton
                variant="ghost"
                color="neutral"
                icon="i-lucide-history"
                @click="showVersionHistory = true"
              >
                历史
              </UButton>
              
              <!-- AI 翻译 -->
              <UButton
                variant="ghost"
                color="neutral"
                icon="i-lucide-languages"
                @click="showTranslationDialog = true"
              >
                翻译
              </UButton>
              
              <!-- 发布按钮 -->
              <UButton
                variant="outline"
                color="primary"
                icon="i-lucide-upload-cloud"
                :disabled="publishStatus === 'published'"
                @click="showPublishDialog = true"
              >
                发布
              </UButton>
              
              <!-- 保存按钮 -->
              <UTooltip :text="`保存 (${modifierKey}S)`">
                <UButton
                  color="primary"
                  icon="i-lucide-save"
                  :loading="saveStatus === 'saving'"
                  :disabled="!hasUnsavedChanges && saveStatus !== 'error'"
                  @click="handleSave"
                >
                  保存
                </UButton>
              </UTooltip>
            </div>
          </div>
        </div>
      </div>

      <!-- 编辑器主体 -->
      <div class="flex-1 min-h-0">
        <!-- 使用 ClientOnly 包裹，确保编辑器只在客户端渲染 -->
        <ClientOnly>
          <EditorDocumentEditor
            :model-value="editorContent"
            :document-id="documentId"
            class="h-full"
            @update:model-value="handleContentChange"
            @save="handleSave"
          />
          <template #fallback>
            <div class="flex items-center justify-center h-full bg-white dark:bg-gray-900">
              <div class="text-center">
                <UIcon name="i-lucide-loader-2" class="w-6 h-6 animate-spin text-gray-400" />
                <p class="mt-2 text-sm text-gray-500">加载编辑器...</p>
              </div>
            </div>
          </template>
        </ClientOnly>
      </div>

      <!-- 版本历史侧边栏 -->
      <USlideover v-model:open="showVersionHistory" title="版本历史" side="right">
        <template #body>
          <EditorVersionHistoryPanel
            :document-id="documentId"
            :current-content="editorContent"
            @restore="(content) => { editorContent = content; markChanged(); showVersionHistory = false; }"
            @close="showVersionHistory = false"
          />
        </template>
      </USlideover>

      <!-- 发布对话框 -->
      <EditorPublishDialog
        v-model:open="showPublishDialog"
        :document-id="documentId"
        :document-title="document.title"
        :current-version="document.currentVersion || 1"
        :published-version="document.publishedVersion"
        :status="document.status"
        :has-unpublished-changes="document.hasUnpublishedChanges"
        :locale="document.locale"
        :category-path="document.category?.slug"
        @published="handlePublished"
      />

      <!-- 翻译对话框 -->
      <EditorTranslationDialog
        v-model:open="showTranslationDialog"
        :document-id="documentId"
        :document-title="document.title"
        :content="editorContent"
        :current-locale="document.locale"
        @save="handleTranslationSaved"
      />
    </template>
  </div>
</template>
