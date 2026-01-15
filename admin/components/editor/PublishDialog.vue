<script setup lang="ts">
/**
 * 发布确认对话框
 * 显示发布前的确认信息和发布状态
 * 支持单语言或全部语言发布
 * 
 * Requirements: 5.3, 5.6
 */
import { getPublishStatusDisplay, type PublishStatus } from '~/composables/usePublish'

interface Locale {
  id: string
  code: string
  name: string
  nativeName: string
  isEnabled: boolean
}

const props = defineProps<{
  documentId: string
  documentTitle: string
  currentVersion: number
  publishedVersion: number | null
  status: string
  hasUnpublishedChanges?: boolean
  locale?: {
    id?: string
    code: string
    name: string
  }
  categoryPath?: string
}>()

const emit = defineEmits<{
  published: []
}>()

const open = defineModel<boolean>('open', { default: false })

// 获取可用语言列表
const { data: locales } = useFetch<Locale[]>('/api/locales')

// 选中的发布语言：'all' 或具体的 localeId
const selectedLocale = ref<string>('current')

// 发布语言选项
const localeOptions = computed(() => {
  const options = [
    { label: '全部语言', value: 'all' },
  ]
  
  // 添加当前语言作为默认选项
  if (props.locale?.id) {
    options.unshift({ label: `${props.locale.name} (当前)`, value: 'current' })
  }
  
  return options
})

// 发布功能
const { isPublishing, publish, getPublishStatus } = useDocumentPublish(props.documentId)

// 计算发布状态
const publishStatus = computed<PublishStatus>(() => {
  if (isPublishing.value) return 'publishing'
  return getPublishStatus(props.status, props.publishedVersion, props.currentVersion, props.hasUnpublishedChanges)
})

// 发布状态显示
const statusDisplay = computed(() => getPublishStatusDisplay(publishStatus.value))

// 是否可以发布
const canPublish = computed(() => {
  return publishStatus.value !== 'published' && !isPublishing.value
})

// 获取同一文档的所有语言版本
const { data: relatedDocuments } = useFetch<Array<{
  id: string
  title: string
  localeCode: string
  localeName: string
  status: string
  hasUnpublishedChanges: boolean
}>>(() => `/api/documents/${props.documentId}/related`, {
  immediate: true,
})

// 发布文件路径预览（单语言）
const singleFilePath = computed(() => {
  const locale = props.locale?.code || 'zh'
  const category = props.categoryPath || ''
  const slug = props.documentTitle.toLowerCase().replace(/\s+/g, '-')
  
  if (category) {
    return `docs/${locale}/${category}/${slug}.md`
  }
  return `docs/${locale}/${slug}.md`
})

// 发布文件路径预览（全部语言）
const allFilePaths = computed(() => {
  if (!relatedDocuments.value || relatedDocuments.value.length === 0) {
    // 如果没有关联文档数据，只显示当前语言
    return [{ locale: props.locale?.code || 'zh', path: singleFilePath.value, name: props.locale?.name || '中文' }]
  }
  
  const category = props.categoryPath || ''
  return relatedDocuments.value.map(doc => {
    const slug = doc.title.toLowerCase().replace(/\s+/g, '-')
    const path = category 
      ? `docs/${doc.localeCode}/${category}/${slug}.md`
      : `docs/${doc.localeCode}/${slug}.md`
    return { 
      locale: doc.localeCode, 
      path, 
      name: doc.localeName,
      canPublish: doc.status !== 'published' || doc.hasUnpublishedChanges
    }
  })
})

// 显示的路径列表
const displayPaths = computed(() => {
  if (selectedLocale.value === 'current') {
    return [{ locale: props.locale?.code || 'zh', path: singleFilePath.value, name: props.locale?.name || '中文', canPublish: canPublish.value }]
  }
  return allFilePaths.value
})

// 可发布的文档数量
const publishableCount = computed(() => {
  if (selectedLocale.value === 'current') return canPublish.value ? 1 : 0
  return allFilePaths.value.filter(p => p.canPublish).length
})

// 发布范围显示文本
const publishScopeText = computed(() => {
  if (selectedLocale.value === 'current') {
    return props.locale?.name || '中文'
  }
  return `全部语言 (${publishableCount.value} 个待发布)`
})

// 执行发布
const handlePublish = async () => {
  if (selectedLocale.value === 'current') {
    // 单语言发布
    const success = await publish()
    if (success) {
      emit('published')
      open.value = false
    }
  } else {
    // 全部语言发布
    await publishAllLanguages()
  }
}

// 发布全部语言
const publishAllLanguages = async () => {
  if (!relatedDocuments.value) return
  
  const documentIds = relatedDocuments.value
    .filter(doc => doc.status !== 'published' || doc.hasUnpublishedChanges)
    .map(doc => doc.id)
  
  if (documentIds.length === 0) {
    const toast = useToast()
    toast.add({ title: '没有需要发布的文档', color: 'warning' })
    return
  }
  
  try {
    await $fetch('/api/publish/batch', {
      method: 'POST',
      body: { documentIds },
    })
    
    const toast = useToast()
    toast.add({ title: `成功发布 ${documentIds.length} 个语言版本`, color: 'success' })
    emit('published')
    open.value = false
  } catch (err: any) {
    const toast = useToast()
    toast.add({ title: '发布失败', description: err.data?.message || err.message, color: 'error' })
  }
}

// 重置状态
watch(open, (isOpen) => {
  if (isOpen) {
    selectedLocale.value = 'current'
  }
})
</script>

<template>
  <UModal v-model:open="open">
    <template #header>
      <div class="flex items-center gap-2">
        <UIcon name="i-lucide-upload-cloud" class="w-5 h-5 text-primary-500" />
        <span>发布文档</span>
      </div>
    </template>

    <template #body>
      <div class="space-y-4">
        <!-- 文档信息 -->
        <div class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-500">文档标题</span>
            <span class="font-medium">{{ documentTitle }}</span>
          </div>
          
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-500">当前版本</span>
            <span class="font-medium">v{{ currentVersion }}</span>
          </div>
          
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-500">已发布版本</span>
            <span class="font-medium">
              {{ publishedVersion ? `v${publishedVersion}` : '未发布' }}
            </span>
          </div>
          
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-500">发布范围</span>
            <USelectMenu
              v-model="selectedLocale"
              :items="localeOptions"
              value-key="value"
              class="w-40"
              size="sm"
            />
          </div>
          
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-500">发布状态</span>
            <UBadge :color="statusDisplay.color" variant="subtle" size="sm">
              <UIcon :name="statusDisplay.icon" class="w-3.5 h-3.5 mr-1" />
              {{ statusDisplay.label }}
            </UBadge>
          </div>
        </div>

        <!-- 发布路径预览 -->
        <div class="p-3 bg-gray-100 dark:bg-gray-900 rounded-lg">
          <div class="text-xs text-gray-500 mb-2">发布路径</div>
          <div class="space-y-1.5 max-h-32 overflow-y-auto">
            <div v-for="item in displayPaths" :key="item.locale" class="flex items-center gap-2">
              <UBadge variant="subtle" size="xs" :color="item.canPublish ? 'primary' : 'neutral'">
                {{ item.name }}
              </UBadge>
              <code class="text-xs text-primary-600 dark:text-primary-400 truncate flex-1">
                {{ item.path }}
              </code>
              <UIcon 
                v-if="!item.canPublish" 
                name="i-lucide-check-circle" 
                class="w-4 h-4 text-green-500 shrink-0" 
                title="已是最新"
              />
            </div>
          </div>
        </div>

        <!-- 发布说明 -->
        <div v-if="publishStatus === 'has_changes'" class="flex items-start gap-2 p-3 bg-warning-50 dark:bg-warning-900/20 rounded-lg">
          <UIcon name="i-lucide-info" class="w-4 h-4 text-warning-500 mt-0.5" />
          <div class="text-sm text-warning-700 dark:text-warning-300">
            文档内容已更新，发布后将覆盖已发布的版本。
          </div>
        </div>

        <div v-if="publishStatus === 'unpublished'" class="flex items-start gap-2 p-3 bg-info-50 dark:bg-info-900/20 rounded-lg">
          <UIcon name="i-lucide-info" class="w-4 h-4 text-info-500 mt-0.5" />
          <div class="text-sm text-info-700 dark:text-info-300">
            这是首次发布此文档，将在 VitePress 站点中创建新页面。
          </div>
        </div>

        <div v-if="selectedLocale === 'all' && publishableCount === 0" class="flex items-start gap-2 p-3 bg-success-50 dark:bg-success-900/20 rounded-lg">
          <UIcon name="i-lucide-check-circle" class="w-4 h-4 text-success-500 mt-0.5" />
          <div class="text-sm text-success-700 dark:text-success-300">
            所有语言版本都已是最新状态，无需发布。
          </div>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex justify-end gap-2">
        <UButton
          variant="ghost"
          color="neutral"
          :disabled="isPublishing"
          @click="open = false"
        >
          取消
        </UButton>
        <UButton
          color="primary"
          :loading="isPublishing"
          :disabled="publishableCount === 0"
          icon="i-lucide-upload-cloud"
          @click="handlePublish"
        >
          {{ isPublishing ? '发布中...' : (selectedLocale === 'all' ? `发布全部 (${publishableCount})` : '确认发布') }}
        </UButton>
      </div>
    </template>
  </UModal>
</template>
