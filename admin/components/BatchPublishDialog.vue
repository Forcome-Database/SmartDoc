<script setup lang="ts">
/**
 * 批量发布对话框
 * 支持选择多个文档进行批量发布
 * 
 * Requirements: 5.7
 */

interface Document {
  id: string
  title: string
  status: string
  publishedVersion: number | null
  currentVersion: number
  locale?: {
    code: string
    name: string
  }
}

const props = defineProps<{
  documents: Document[]
}>()

const emit = defineEmits<{
  published: [documentIds: string[]]
}>()

const open = defineModel<boolean>('open', { default: false })

// 批量发布功能
const { isPublishing, publishBatch } = useBatchPublish()

// 选中的文档 ID
const selectedIds = ref<string[]>([])

// 全选状态
const isAllSelected = computed(() => {
  return selectedIds.value.length === props.documents.length && props.documents.length > 0
})

const isPartialSelected = computed(() => {
  return selectedIds.value.length > 0 && selectedIds.value.length < props.documents.length
})

// 切换全选
const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = props.documents.map(d => d.id)
  }
}

// 切换单个选择
const toggleSelect = (id: string) => {
  const index = selectedIds.value.indexOf(id)
  if (index === -1) {
    selectedIds.value.push(id)
  } else {
    selectedIds.value.splice(index, 1)
  }
}

// 获取文档状态显示
const getStatusDisplay = (doc: Document) => {
  if (doc.status === 'draft' || doc.publishedVersion === null) {
    return { label: '未发布', color: 'neutral' }
  }
  if (doc.publishedVersion < doc.currentVersion) {
    return { label: '有更改', color: 'warning' }
  }
  return { label: '已发布', color: 'success' }
}

// 执行批量发布
const handlePublish = async () => {
  if (selectedIds.value.length === 0) return

  const result = await publishBatch(selectedIds.value)
  
  if (result.success || result.publishedCount > 0) {
    emit('published', selectedIds.value)
    selectedIds.value = []
    open.value = false
  }
}

// 重置选择
watch(open, (isOpen) => {
  if (!isOpen) {
    selectedIds.value = []
  }
})
</script>

<template>
  <UModal v-model:open="open" size="lg">
    <template #header>
      <div class="flex items-center gap-2">
        <UIcon name="i-lucide-upload-cloud" class="w-5 h-5 text-primary-500" />
        <span>批量发布</span>
      </div>
    </template>

    <template #body>
      <div class="space-y-4">
        <!-- 选择提示 -->
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-500">
            已选择 {{ selectedIds.length }} / {{ documents.length }} 个文档
          </span>
          <UButton
            variant="ghost"
            size="xs"
            @click="toggleSelectAll"
          >
            {{ isAllSelected ? '取消全选' : '全选' }}
          </UButton>
        </div>

        <!-- 文档列表 -->
        <div class="border rounded-lg divide-y dark:border-gray-700 dark:divide-gray-700 max-h-96 overflow-y-auto">
          <div
            v-for="doc in documents"
            :key="doc.id"
            class="flex items-center gap-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
            @click="toggleSelect(doc.id)"
          >
            <UCheckbox
              :model-value="selectedIds.includes(doc.id)"
              @update:model-value="toggleSelect(doc.id)"
              @click.stop
            />
            
            <div class="flex-1 min-w-0">
              <div class="font-medium truncate">{{ doc.title }}</div>
              <div class="flex items-center gap-2 text-xs text-gray-500 mt-0.5">
                <span>v{{ doc.currentVersion }}</span>
                <span>·</span>
                <span>{{ doc.locale?.name || '中文' }}</span>
              </div>
            </div>
            
            <UBadge
              :color="getStatusDisplay(doc).color"
              variant="subtle"
              size="xs"
            >
              {{ getStatusDisplay(doc).label }}
            </UBadge>
          </div>

          <div v-if="documents.length === 0" class="p-8 text-center text-gray-500">
            暂无可发布的文档
          </div>
        </div>

        <!-- 发布说明 -->
        <div class="flex items-start gap-2 p-3 bg-info-50 dark:bg-info-900/20 rounded-lg">
          <UIcon name="i-lucide-info" class="w-4 h-4 text-info-500 mt-0.5" />
          <div class="text-sm text-info-700 dark:text-info-300">
            批量发布将把选中的文档同时发布到 VitePress 站点，并创建一个合并的 Git 提交。
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
          :disabled="selectedIds.length === 0"
          icon="i-lucide-upload-cloud"
          @click="handlePublish"
        >
          {{ isPublishing ? '发布中...' : `发布 ${selectedIds.length} 个文档` }}
        </UButton>
      </div>
    </template>
  </UModal>
</template>
