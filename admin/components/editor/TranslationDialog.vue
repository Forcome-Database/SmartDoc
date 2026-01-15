<script setup lang="ts">
/**
 * AI 翻译对话框
 * 实现源语言/目标语言选择、流式翻译结果展示、翻译结果预览和编辑
 * 
 * Requirements: 6.1, 6.3, 6.4
 */
import { useTranslation } from '~/composables/useTranslation'

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
  content: string
  currentLocale: Locale
}>()

const emit = defineEmits<{
  save: [{ content: string; localeId: string; title: string; document: any; isUpdate: boolean }]
}>()

const open = defineModel<boolean>('open', { default: false })

// 获取可用语言列表
const { data: locales, pending: loadingLocales } = useFetch<Locale[]>('/api/locales')

// 翻译状态
const targetLocaleId = ref('')
const editedResult = ref('')
const isEditing = ref(false)
const translatedTitle = ref('')
const translateTitleEnabled = ref(true) // 是否翻译标题
const isTranslatingTitle = ref(false)

// 翻译 composable
const {
  result,
  isTranslating,
  progress,
  error,
  translate,
  stop,
  reset,
} = useTranslation({
  onFinish: (translatedContent) => {
    editedResult.value = translatedContent
  },
  onError: (err) => {
    console.error('Translation error:', err)
  },
})

// 可选的目标语言（排除当前语言）
const availableTargetLocales = computed(() => {
  if (!locales.value) return []
  return locales.value.filter(
    (locale) => locale.isEnabled && locale.id !== props.currentLocale.id
  )
})

// 转换为 USelectMenu 需要的格式
const targetLocaleOptions = computed(() => {
  return availableTargetLocales.value.map((locale) => ({
    label: `${locale.nativeName} (${locale.code})`,
    value: locale.id,
  }))
})

// 选中的目标语言
const selectedTargetLocale = computed(() => {
  if (!locales.value || !targetLocaleId.value) return null
  return locales.value.find((l) => l.id === targetLocaleId.value)
})

// 是否可以开始翻译
const canTranslate = computed(() => {
  return targetLocaleId.value && props.content && !isTranslating.value
})

// 是否可以保存
const canSave = computed(() => {
  return (editedResult.value || result.value) && 
         targetLocaleId.value && 
         translatedTitle.value &&
         !isTranslating.value
})

// 显示的翻译结果
const displayResult = computed(() => {
  return isEditing.value ? editedResult.value : (result.value || editedResult.value)
})

// 开始翻译
async function startTranslation() {
  if (!canTranslate.value || !selectedTargetLocale.value) return
  
  // 重置编辑状态
  isEditing.value = false
  editedResult.value = ''
  
  // 根据选项决定是否翻译标题
  if (translateTitleEnabled.value) {
    translateTitle()
  } else {
    // 不翻译标题，使用原标题
    translatedTitle.value = props.documentTitle
  }
  
  // 翻译内容
  await translate(
    props.content,
    props.currentLocale.code,
    selectedTargetLocale.value.code
  )
}

// 翻译标题（使用非流式 API）
async function translateTitle() {
  if (!selectedTargetLocale.value) return
  
  isTranslatingTitle.value = true
  try {
    const response = await $fetch<{ translatedText: string }>('/api/translate-title', {
      method: 'POST',
      body: {
        text: props.documentTitle,
        sourceLocale: props.currentLocale.code,
        targetLocale: selectedTargetLocale.value.code,
      },
    })
    
    translatedTitle.value = response.translatedText
  } catch (err) {
    console.error('Title translation error:', err)
    // 如果标题翻译失败，使用原标题
    translatedTitle.value = props.documentTitle
  } finally {
    isTranslatingTitle.value = false
  }
}

// 停止翻译
function stopTranslation() {
  stop()
}

// 切换编辑模式
function toggleEdit() {
  if (!isEditing.value) {
    // 进入编辑模式，复制当前结果
    editedResult.value = result.value || editedResult.value
  }
  isEditing.value = !isEditing.value
}

// 保存状态
const isSaving = ref(false)
const saveError = ref<string | null>(null)

// 保存翻译结果
async function saveTranslation() {
  if (!canSave.value) return
  
  isSaving.value = true
  saveError.value = null
  
  try {
    const response = await $fetch('/api/translations', {
      method: 'POST',
      body: {
        sourceDocumentId: props.documentId,
        targetLocaleId: targetLocaleId.value,
        translatedTitle: translatedTitle.value,
        translatedContent: editedResult.value || result.value,
      },
    })
    
    // 通知父组件
    emit('save', {
      content: editedResult.value || result.value,
      localeId: targetLocaleId.value,
      title: translatedTitle.value,
      document: response.document,
      isUpdate: response.isUpdate,
    })
    
    // 显示成功提示
    const toast = useToast()
    toast.add({
      title: '翻译保存成功',
      description: response.message,
      color: 'success',
    })
    
    // 关闭对话框
    open.value = false
  } catch (err: any) {
    saveError.value = err.data?.message || err.message || '保存失败'
    const toast = useToast()
    toast.add({
      title: '保存失败',
      description: saveError.value,
      color: 'error',
    })
  } finally {
    isSaving.value = false
  }
}

// 重置对话框状态
function resetDialog() {
  targetLocaleId.value = ''
  editedResult.value = ''
  isEditing.value = false
  translatedTitle.value = ''
  translateTitleEnabled.value = true
  isTranslatingTitle.value = false
  saveError.value = null
  reset()
}

// 监听对话框关闭
watch(open, (isOpen) => {
  if (!isOpen) {
    // 如果正在翻译，停止
    if (isTranslating.value) {
      stop()
    }
    // 延迟重置，避免闪烁
    setTimeout(resetDialog, 300)
  }
})

// 初始化默认目标语言
watch([open, locales], ([isOpen, localeList]) => {
  if (isOpen && localeList && localeList.length > 0 && !targetLocaleId.value) {
    // 选择第一个可用的目标语言
    const firstAvailable = availableTargetLocales.value[0]
    if (firstAvailable) {
      targetLocaleId.value = firstAvailable.id
    }
  }
}, { immediate: true })
</script>

<template>
  <UModal v-model:open="open" :ui="{ width: 'max-w-4xl' }">
    <template #header>
      <div class="flex items-center gap-2">
        <UIcon name="i-lucide-languages" class="w-5 h-5 text-primary-500" />
        <span>AI 翻译</span>
      </div>
    </template>

    <template #body>
      <div class="space-y-4">
        <!-- 语言选择 -->
        <div class="flex items-center gap-4">
          <!-- 源语言 -->
          <div class="flex-1">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              源语言
            </label>
            <div class="px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm">
              {{ currentLocale.nativeName }} ({{ currentLocale.code }})
            </div>
          </div>

          <!-- 箭头 -->
          <div class="pt-6">
            <UIcon name="i-lucide-arrow-right" class="w-5 h-5 text-gray-400" />
          </div>

          <!-- 目标语言 -->
          <div class="flex-1">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              目标语言
            </label>
            <USelectMenu
              v-model="targetLocaleId"
              :items="targetLocaleOptions"
              value-key="value"
              :loading="loadingLocales"
              :disabled="isTranslating"
              placeholder="选择目标语言"
            />
          </div>
        </div>

        <!-- 标题翻译选项 -->
        <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-heading" class="w-4 h-4 text-gray-500" />
            <span class="text-sm text-gray-700 dark:text-gray-300">翻译标题</span>
          </div>
          <USwitch v-model="translateTitleEnabled" :disabled="isTranslating" />
        </div>

        <!-- 翻译标题 -->
        <div v-if="translatedTitle || isTranslatingTitle">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            翻译后标题
            <span v-if="isTranslatingTitle" class="text-xs text-gray-400 ml-2">翻译中...</span>
          </label>
          <UInput
            v-model="translatedTitle"
            :disabled="isTranslatingTitle"
            :loading="isTranslatingTitle"
            placeholder="翻译后的文档标题"
          />
        </div>

        <!-- 翻译进度 -->
        <div v-if="isTranslating" class="space-y-2">
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-600 dark:text-gray-400">翻译中...</span>
            <span class="text-primary-600 dark:text-primary-400">{{ progress }}%</span>
          </div>
          <UProgress :value="progress" color="primary" size="sm" />
        </div>

        <!-- 保存错误提示 -->
        <div v-if="saveError" class="p-3 bg-error-50 dark:bg-error-900/20 rounded-lg">
          <div class="flex items-center gap-2 text-error-600 dark:text-error-400">
            <UIcon name="i-lucide-alert-circle" class="w-4 h-4" />
            <span class="text-sm">{{ saveError }}</span>
          </div>
        </div>

        <!-- 错误提示 -->
        <div v-if="error" class="p-3 bg-error-50 dark:bg-error-900/20 rounded-lg">
          <div class="flex items-center gap-2 text-error-600 dark:text-error-400">
            <UIcon name="i-lucide-alert-circle" class="w-4 h-4" />
            <span class="text-sm">{{ error.message || '翻译失败，请重试' }}</span>
          </div>
        </div>

        <!-- 翻译结果 -->
        <div v-if="displayResult || isTranslating" class="space-y-2">
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
              翻译结果
            </label>
            <div class="flex items-center gap-2">
              <UButton
                v-if="!isTranslating && displayResult"
                variant="ghost"
                size="xs"
                :icon="isEditing ? 'i-lucide-eye' : 'i-lucide-pencil'"
                @click="toggleEdit"
              >
                {{ isEditing ? '预览' : '编辑' }}
              </UButton>
            </div>
          </div>
          
          <!-- 编辑模式 -->
          <UTextarea
            v-if="isEditing"
            v-model="editedResult"
            :rows="15"
            class="font-mono text-sm"
            placeholder="翻译结果..."
          />
          
          <!-- 预览模式 -->
          <div
            v-else
            class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg max-h-96 overflow-y-auto"
          >
            <pre class="whitespace-pre-wrap text-sm font-mono text-gray-700 dark:text-gray-300">{{ displayResult || '等待翻译...' }}</pre>
          </div>
        </div>

        <!-- 空状态 -->
        <div
          v-if="!displayResult && !isTranslating && !error"
          class="p-8 text-center text-gray-500 dark:text-gray-400"
        >
          <UIcon name="i-lucide-languages" class="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>选择目标语言后点击"开始翻译"</p>
          <p class="text-sm mt-1">AI 将保持 Markdown 格式进行翻译</p>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex justify-between">
        <div>
          <UButton
            v-if="isTranslating"
            variant="ghost"
            color="error"
            icon="i-lucide-square"
            @click="stopTranslation"
          >
            停止翻译
          </UButton>
        </div>
        
        <div class="flex gap-2">
          <UButton
            variant="ghost"
            color="neutral"
            :disabled="isTranslating"
            @click="open = false"
          >
            取消
          </UButton>
          
          <UButton
            v-if="!displayResult"
            color="primary"
            :loading="isTranslating"
            :disabled="!canTranslate"
            icon="i-lucide-sparkles"
            @click="startTranslation"
          >
            开始翻译
          </UButton>
          
          <UButton
            v-else
            color="primary"
            :loading="isSaving"
            :disabled="!canSave || isSaving"
            icon="i-lucide-save"
            @click="saveTranslation"
          >
            {{ isSaving ? '保存中...' : '保存为新文档' }}
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
