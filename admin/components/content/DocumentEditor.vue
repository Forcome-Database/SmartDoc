<script setup lang="ts">
/**
 * 文档编辑器组件
 * 从 documents/[id].vue 抽取，支持复用
 */
import type { DocumentStatus } from '~/types'
import { getPublishStatusDisplay, type PublishStatus } from '~/composables/usePublish'
import { getModifierKey } from '~/composables/useKeyboardShortcuts'

const props = defineProps<{
  documentId: string
}>()

const emit = defineEmits<{
  titleChange: [documentId: string, newTitle: string]
}>()

const toast = useToast()
const modifierKey = getModifierKey()

// 文档数据 - 使用 useLazyFetch 避免阻塞
const document = ref<any>(null)
const loading = ref(true)
const error = ref<any>(null)

// 获取文档
const fetchDocument = async () => {
  loading.value = true
  error.value = null
  try {
    document.value = await $fetch(`/api/documents/${props.documentId}`)
  } catch (e: any) {
    error.value = e
  } finally {
    loading.value = false
  }
}

// 刷新文档
const refresh = () => fetchDocument()

// 发布功能
const { getPublishStatus } = useDocumentPublish(computed(() => props.documentId))

// 对话框状态
const showPublishDialog = ref(false)
const showTranslationDialog = ref(false)
const showVersionHistory = ref(false)

// 编辑器内容
const editorContent = ref('')
const documentTitle = ref('')
const isInitialized = ref(false)

// 初始化编辑器内容
watch(document, (doc) => {
  if (doc && !isInitialized.value) {
    editorContent.value = doc.content || ''
    documentTitle.value = doc.title || ''
    isInitialized.value = true
  }
}, { immediate: true })

// 自动保存 - 1分钟间隔
const { 
  status: saveStatus, hasUnsavedChanges, statusText, statusIcon, statusColor,
  markChanged, save: triggerSave, reset: resetSaveStatus,
} = useAutoSave(async () => { await saveDocument() }, { debounceMs: 60000, savedDuration: 3000 })

// 保存文档
const saveDocument = async (shouldRefresh = false) => {
  if (!document.value) {
    throw new Error('文档未加载')
  }
  const result = await $fetch(`/api/documents/${props.documentId}`, {
    method: 'PATCH',
    body: { title: documentTitle.value, content: editorContent.value, createVersion: false },
  })
  // 更新本地文档状态（保存后 hasUnpublishedChanges 会变为 true）
  if (document.value && result) {
    document.value = { ...document.value, ...result }
  }
  if (shouldRefresh) {
    await refresh()
  }
}

// 手动保存状态
const manualSaving = ref(false)

// 事件处理
const handleContentChange = (content: string) => { editorContent.value = content; markChanged() }
const handleTitleChange = () => { 
  markChanged()
  // 通知父组件标题变化
  emit('titleChange', props.documentId, documentTitle.value)
}
const handleSave = async () => { 
  if (!document.value) {
    toast.add({ title: '文档未加载', color: 'warning' })
    return
  }
  if (manualSaving.value) return
  
  manualSaving.value = true
  try {
    await saveDocument(true)
    // 手动重置自动保存状态
    resetSaveStatus()
    toast.add({ title: '保存成功', color: 'success' }) 
  } catch (e: any) {
    // 显示详细错误信息
    const errorMsg = e?.data?.message || e?.message || '未知错误'
    toast.add({ title: '保存失败', description: errorMsg, color: 'error' })
    console.error('Save failed:', e)
  } finally {
    manualSaving.value = false
  }
}

// 发布状态 - 基于数据库字段判断，不依赖前端编辑状态
const publishStatus = computed<PublishStatus>(() => {
  if (!document.value) return 'unpublished'
  return getPublishStatus(
    document.value.status,
    document.value.publishedVersion,
    document.value.currentVersion || 1,
    document.value.hasUnpublishedChanges
  )
})
const publishStatusDisplay = computed(() => getPublishStatusDisplay(publishStatus.value))

const handlePublished = async () => { await refresh(); toast.add({ title: '发布成功', color: 'success' }) }
const handleTranslationSaved = async () => {}

// 状态映射
const statusColorMap: Record<DocumentStatus, string> = { draft: 'warning', published: 'success', archived: 'neutral' }
const statusTextMap: Record<DocumentStatus, string> = { draft: '草稿', published: '已发布', archived: '已归档' }

// 面包屑
const breadcrumbItems = computed(() => {
  const items: Array<{ label: string; to?: string }> = [{ label: '文档', to: '/content' }]
  
  // 添加完整栏目路径
  if (document.value?.categoryPath && document.value.categoryPath.length > 0) {
    const localeCode = document.value.locale?.code || 'zh'
    for (const cat of document.value.categoryPath) {
      items.push({ 
        label: cat.titles?.[localeCode] || cat.titles?.zh || cat.slug 
      })
    }
  }
  
  // 添加文档标题
  if (document.value?.title) {
    items.push({ label: document.value.title })
  }
  
  return items
})

// 组件挂载时获取文档
onMounted(() => {
  fetchDocument()
})

// 监听 documentId 变化
watch(() => props.documentId, () => {
  isInitialized.value = false
  fetchDocument()
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
        <UButton class="mt-4" @click="refresh()">重试</UButton>
      </div>
    </div>

    <!-- 文档编辑器 -->
    <template v-else-if="document">
      <!-- 顶部工具栏 -->
      <div class="flex-shrink-0 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div class="px-4 py-3">
          <UBreadcrumb :items="breadcrumbItems" class="mb-3" />
          
          <div class="flex items-center justify-between gap-4">
            <div class="flex-1 min-w-0">
              <input
                v-model="documentTitle"
                type="text"
                class="w-full text-xl font-semibold bg-transparent border-none outline-none text-gray-900 dark:text-white placeholder-gray-400 focus:ring-0"
                placeholder="文档标题"
                @input="handleTitleChange"
              />
              
              <div class="flex items-center gap-4 mt-1 text-sm text-gray-500">
                <UBadge :color="statusColorMap[document.status as DocumentStatus]" variant="subtle" size="xs">
                  {{ statusTextMap[document.status as DocumentStatus] }}
                </UBadge>
                <span v-if="document.locale" class="flex items-center gap-1">
                  <UIcon name="i-lucide-globe" class="w-3.5 h-3.5" />
                  {{ document.locale.nativeName || document.locale.name }}
                </span>
                <span class="flex items-center gap-1">
                  <UIcon name="i-lucide-git-branch" class="w-3.5 h-3.5" />
                  v{{ document.currentVersion || 1 }}
                </span>
                <span v-if="document.author" class="flex items-center gap-1">
                  <UAvatar :src="document.author.avatar" :alt="document.author.name" size="2xs" />
                  {{ document.author.name }}
                </span>
              </div>
            </div>
            
            <div class="flex items-center gap-2">
              <div v-if="saveStatus !== 'idle'" :class="['flex items-center gap-1.5 text-sm', statusColor]">
                <UIcon :name="statusIcon" :class="['w-4 h-4', saveStatus === 'saving' ? 'animate-spin' : '']" />
                <span>{{ statusText }}</span>
              </div>
              
              <UBadge :color="publishStatusDisplay.color" variant="subtle" size="sm" class="cursor-pointer" @click="showPublishDialog = true">
                <UIcon :name="publishStatusDisplay.icon" class="w-3.5 h-3.5 mr-1" />
                {{ publishStatusDisplay.label }}
              </UBadge>
              
              <UButton variant="ghost" color="neutral" icon="i-lucide-history" @click="showVersionHistory = true">历史</UButton>
              <UButton variant="ghost" color="neutral" icon="i-lucide-languages" @click="showTranslationDialog = true">翻译</UButton>
              <UButton variant="outline" color="primary" icon="i-lucide-upload-cloud" :disabled="publishStatus === 'published'" @click="showPublishDialog = true">发布</UButton>
              
              <UTooltip :text="`保存 (${modifierKey}S)`">
                <UButton color="primary" icon="i-lucide-save" :loading="manualSaving || saveStatus === 'saving'" @click="handleSave">保存</UButton>
              </UTooltip>
            </div>
          </div>
        </div>
      </div>

      <!-- 编辑器主体 -->
      <div class="flex-1 min-h-0">
        <ClientOnly>
          <EditorDocumentEditorWithSlash 
            :model-value="editorContent" 
            :document-id="documentId" 
            class="h-full" 
            @update:model-value="handleContentChange" 
            @save="handleSave" 
          />
          <template #fallback>
            <div class="flex items-center justify-center h-full bg-white dark:bg-gray-900">
              <UIcon name="i-lucide-loader-2" class="w-6 h-6 animate-spin text-gray-400" />
              <p class="mt-2 text-sm text-gray-500">加载编辑器...</p>
            </div>
          </template>
        </ClientOnly>
      </div>

      <!-- 版本历史 -->
      <USlideover v-model:open="showVersionHistory" title="版本历史" side="right">
        <template #body>
          <EditorVersionHistoryPanel 
            :document-id="documentId" 
            :current-content="editorContent" 
            @restore="(c: string) => { editorContent = c; markChanged(); showVersionHistory = false }" 
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
