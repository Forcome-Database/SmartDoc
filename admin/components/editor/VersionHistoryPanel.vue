<script setup lang="ts">
/**
 * 版本历史面板
 * 显示文档版本列表，支持预览和回滚
 * 
 * Requirements: 4.2, 4.3, 4.5
 */

const props = defineProps<{
  documentId: string
  currentContent: string
}>()

const emit = defineEmits<{
  restore: [content: string]
  close: []
}>()

const toast = useToast()

// 版本列表
const { data: versionsData, pending: loading, refresh } = await useFetch(
  () => `/api/documents/${props.documentId}/versions`,
  {
    key: `versions-${props.documentId}`,
    query: {
      limit: 50,
      sortOrder: 'desc',
    },
  }
)

// 选中的版本（用于预览）
const selectedVersion = ref<number | null>(null)

// 预览内容
const previewContent = ref<string | null>(null)
const loadingPreview = ref(false)

// 回滚确认对话框
const showRollbackConfirm = ref(false)
const rollbackTarget = ref<number | null>(null)
const rollbackLoading = ref(false)

// 对比模式
const showDiff = ref(false)
const diffLeftVersion = ref<number | null>(null)
const diffRightVersion = ref<number | null>(null)

// 开始对比
const startDiff = (versionNum: number) => {
  if (!diffLeftVersion.value) {
    diffLeftVersion.value = versionNum
  } else if (!diffRightVersion.value && versionNum !== diffLeftVersion.value) {
    diffRightVersion.value = versionNum
    showDiff.value = true
  }
}

// 取消对比选择
const cancelDiffSelection = () => {
  diffLeftVersion.value = null
  diffRightVersion.value = null
}

// 关闭对比视图
const closeDiff = () => {
  showDiff.value = false
  diffLeftVersion.value = null
  diffRightVersion.value = null
}

// 加载版本内容
const loadVersionContent = async (versionNum: number) => {
  if (selectedVersion.value === versionNum) {
    // 取消选中
    selectedVersion.value = null
    previewContent.value = null
    return
  }

  loadingPreview.value = true
  selectedVersion.value = versionNum

  try {
    const data = await $fetch<{ content: string }>(
      `/api/documents/${props.documentId}/versions/${versionNum}`
    )
    previewContent.value = data.content
  } catch (e) {
    toast.add({
      title: '加载失败',
      description: '无法加载版本内容',
      color: 'error',
    })
    selectedVersion.value = null
    previewContent.value = null
  } finally {
    loadingPreview.value = false
  }
}

// 确认回滚
const confirmRollback = (versionNum: number) => {
  rollbackTarget.value = versionNum
  showRollbackConfirm.value = true
}

// 执行回滚
const doRollback = async () => {
  if (!rollbackTarget.value) return

  rollbackLoading.value = true

  try {
    const result = await $fetch<{ document: { content: string } }>(
      `/api/documents/${props.documentId}/versions/rollback`,
      {
        method: 'POST',
        body: {
          versionNum: rollbackTarget.value,
        },
      }
    )

    toast.add({
      title: '回滚成功',
      description: `已回滚到版本 ${rollbackTarget.value}`,
      color: 'success',
    })

    // 刷新版本列表
    await refresh()

    // 通知父组件更新内容
    emit('restore', result.document.content)
  } catch (e) {
    toast.add({
      title: '回滚失败',
      description: e instanceof Error ? e.message : '操作失败',
      color: 'error',
    })
  } finally {
    rollbackLoading.value = false
    showRollbackConfirm.value = false
    rollbackTarget.value = null
  }
}

// 恢复到选中版本
const restoreSelected = () => {
  if (previewContent.value !== null) {
    emit('restore', previewContent.value)
  }
}

// 格式化时间
const formatTime = (date: string | Date) => {
  const d = new Date(date)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  
  // 小于 1 分钟
  if (diff < 60 * 1000) {
    return '刚刚'
  }
  
  // 小于 1 小时
  if (diff < 60 * 60 * 1000) {
    const minutes = Math.floor(diff / (60 * 1000))
    return `${minutes} 分钟前`
  }
  
  // 小于 24 小时
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000))
    return `${hours} 小时前`
  }
  
  // 小于 7 天
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const days = Math.floor(diff / (24 * 60 * 60 * 1000))
    return `${days} 天前`
  }
  
  // 其他情况显示日期
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- 加载状态 -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <UIcon name="i-lucide-loader-2" class="w-6 h-6 animate-spin text-gray-400" />
    </div>

    <!-- 空状态 -->
    <div 
      v-else-if="!versionsData?.items?.length" 
      class="flex-1 flex items-center justify-center text-center p-4"
    >
      <div>
        <UIcon name="i-lucide-history" class="w-12 h-12 text-gray-300 mx-auto" />
        <p class="mt-2 text-gray-500">暂无版本历史</p>
        <p class="text-sm text-gray-400">保存文档后将自动创建版本</p>
      </div>
    </div>

    <!-- 版本列表 -->
    <template v-else>
      <!-- 工具栏 -->
      <div class="flex-shrink-0 px-4 py-3 border-b border-gray-200 dark:border-gray-800">
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-500">
            共 {{ versionsData.pagination?.total || 0 }} 个版本
          </span>
          <div class="flex items-center gap-2">
            <!-- 对比选择提示 -->
            <template v-if="diffLeftVersion && !diffRightVersion">
              <span class="text-xs text-primary-600 dark:text-primary-400">
                已选 v{{ diffLeftVersion }}，请选择另一个版本
              </span>
              <UButton
                size="xs"
                variant="ghost"
                color="neutral"
                @click="cancelDiffSelection"
              >
                取消
              </UButton>
            </template>
            <UButton
              v-else
              size="xs"
              variant="ghost"
              color="neutral"
              icon="i-lucide-git-compare"
              @click="diffLeftVersion = null; diffRightVersion = null"
            >
              对比版本
            </UButton>
          </div>
        </div>
      </div>

      <!-- 版本列表 -->
      <div class="flex-1 overflow-auto">
        <div class="divide-y divide-gray-100 dark:divide-gray-800">
          <div
            v-for="version in versionsData.items"
            :key="version.id"
            :class="[
              'px-4 py-3 cursor-pointer transition-colors',
              selectedVersion === version.versionNum
                ? 'bg-primary-50 dark:bg-primary-900/20'
                : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
            ]"
            @click="loadVersionContent(version.versionNum)"
          >
            <div class="flex items-start justify-between gap-2">
              <div class="flex-1 min-w-0">
                <!-- 版本号和标签 -->
                <div class="flex items-center gap-2">
                  <span class="font-medium text-gray-900 dark:text-white">
                    v{{ version.versionNum }}
                  </span>
                  <UBadge 
                    v-if="version.isPublished" 
                    color="success" 
                    variant="subtle" 
                    size="xs"
                  >
                    已发布
                  </UBadge>
                </div>

                <!-- 变更说明 -->
                <p 
                  v-if="version.changeLog" 
                  class="text-sm text-gray-600 dark:text-gray-400 mt-0.5 truncate"
                >
                  {{ version.changeLog }}
                </p>

                <!-- 作者和时间 -->
                <div class="flex items-center gap-2 mt-1.5 text-xs text-gray-500">
                  <div class="flex items-center gap-1">
                    <UAvatar
                      :src="version.author?.avatar"
                      :alt="version.author?.name"
                      size="3xs"
                    />
                    <span>{{ version.author?.name || '未知' }}</span>
                  </div>
                  <span>·</span>
                  <span>{{ formatTime(version.createdAt) }}</span>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="flex-shrink-0">
                <UDropdownMenu
                  :items="[
                    [
                      {
                        label: '预览',
                        icon: 'i-lucide-eye',
                        onSelect: () => loadVersionContent(version.versionNum),
                      },
                      {
                        label: diffLeftVersion ? '与此版本对比' : '选择对比',
                        icon: 'i-lucide-git-compare',
                        onSelect: () => startDiff(version.versionNum),
                      },
                      {
                        label: '回滚到此版本',
                        icon: 'i-lucide-rotate-ccw',
                        onSelect: () => confirmRollback(version.versionNum),
                      },
                    ],
                  ]"
                >
                  <UButton
                    variant="ghost"
                    color="neutral"
                    size="xs"
                    icon="i-lucide-more-vertical"
                    @click.stop
                  />
                </UDropdownMenu>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 预览区域 -->
      <div 
        v-if="selectedVersion && previewContent !== null" 
        class="flex-shrink-0 border-t border-gray-200 dark:border-gray-800"
      >
        <div class="px-4 py-3 bg-gray-50 dark:bg-gray-900">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
              版本 {{ selectedVersion }} 预览
            </span>
            <div class="flex items-center gap-2">
              <UButton
                size="xs"
                variant="ghost"
                color="neutral"
                @click="selectedVersion = null; previewContent = null"
              >
                关闭
              </UButton>
              <UButton
                size="xs"
                color="primary"
                @click="restoreSelected"
              >
                使用此版本
              </UButton>
            </div>
          </div>

          <!-- 预览内容 -->
          <div 
            v-if="loadingPreview" 
            class="h-32 flex items-center justify-center"
          >
            <UIcon name="i-lucide-loader-2" class="w-5 h-5 animate-spin text-gray-400" />
          </div>
          <div 
            v-else 
            class="max-h-48 overflow-auto rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-3"
          >
            <div 
              class="prose prose-sm dark:prose-invert max-w-none"
              v-html="previewContent"
            />
          </div>
        </div>
      </div>
    </template>

    <!-- 回滚确认对话框 -->
    <UModal v-model:open="showRollbackConfirm">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-alert-triangle" class="w-5 h-5 text-amber-500" />
              <span class="font-semibold">确认回滚</span>
            </div>
          </template>

          <p class="text-gray-600 dark:text-gray-400">
            确定要回滚到版本 {{ rollbackTarget }} 吗？
          </p>
          <p class="text-sm text-gray-500 mt-2">
            回滚操作会创建一个新版本，当前内容不会丢失。
          </p>

          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton
                variant="ghost"
                color="neutral"
                @click="showRollbackConfirm = false"
              >
                取消
              </UButton>
              <UButton
                color="primary"
                :loading="rollbackLoading"
                @click="doRollback"
              >
                确认回滚
              </UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>

    <!-- 版本对比对话框 -->
    <UModal 
      v-model:open="showDiff" 
      :ui="{ width: 'max-w-4xl' }"
    >
      <template #content>
        <div class="h-[600px]">
          <VersionDiffView
            v-if="diffLeftVersion && diffRightVersion"
            :document-id="documentId"
            :left-version-num="Math.min(diffLeftVersion, diffRightVersion)"
            :right-version-num="Math.max(diffLeftVersion, diffRightVersion)"
            @close="closeDiff"
          />
        </div>
      </template>
    </UModal>
  </div>
</template>
