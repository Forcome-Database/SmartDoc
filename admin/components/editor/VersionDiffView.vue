<script setup lang="ts">
/**
 * 版本对比视图
 * 实现两个版本的 diff 对比，高亮显示变更内容
 * 
 * Requirements: 4.4
 */

const props = defineProps<{
  documentId: string
  leftVersionNum: number
  rightVersionNum: number
}>()

const emit = defineEmits<{
  close: []
}>()

const toast = useToast()

// 加载状态
const loading = ref(true)

// 版本内容
const leftContent = ref('')
const rightContent = ref('')
const leftVersion = ref<any>(null)
const rightVersion = ref<any>(null)

// 差异结果
const diffResult = ref<DiffLine[]>([])

// 差异行类型
interface DiffLine {
  type: 'unchanged' | 'added' | 'removed'
  content: string
  leftLineNum?: number
  rightLineNum?: number
}

// 简单的行级 diff 算法
const computeDiff = (oldText: string, newText: string): DiffLine[] => {
  const oldLines = oldText.split('\n')
  const newLines = newText.split('\n')
  const result: DiffLine[] = []

  // 使用最长公共子序列 (LCS) 算法
  const lcs = computeLCS(oldLines, newLines)
  
  let oldIdx = 0
  let newIdx = 0
  let leftLineNum = 1
  let rightLineNum = 1

  for (const match of lcs) {
    // 添加删除的行
    while (oldIdx < match.oldIdx) {
      result.push({
        type: 'removed',
        content: oldLines[oldIdx],
        leftLineNum: leftLineNum++,
      })
      oldIdx++
    }

    // 添加新增的行
    while (newIdx < match.newIdx) {
      result.push({
        type: 'added',
        content: newLines[newIdx],
        rightLineNum: rightLineNum++,
      })
      newIdx++
    }

    // 添加未变更的行
    result.push({
      type: 'unchanged',
      content: oldLines[oldIdx],
      leftLineNum: leftLineNum++,
      rightLineNum: rightLineNum++,
    })
    oldIdx++
    newIdx++
  }

  // 处理剩余的行
  while (oldIdx < oldLines.length) {
    result.push({
      type: 'removed',
      content: oldLines[oldIdx],
      leftLineNum: leftLineNum++,
    })
    oldIdx++
  }

  while (newIdx < newLines.length) {
    result.push({
      type: 'added',
      content: newLines[newIdx],
      rightLineNum: rightLineNum++,
    })
    newIdx++
  }

  return result
}

// 计算最长公共子序列
interface LCSMatch {
  oldIdx: number
  newIdx: number
}

const computeLCS = (oldLines: string[], newLines: string[]): LCSMatch[] => {
  const m = oldLines.length
  const n = newLines.length
  
  // 创建 DP 表
  const dp: number[][] = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0))
  
  // 填充 DP 表
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (oldLines[i - 1] === newLines[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1])
      }
    }
  }
  
  // 回溯找出 LCS
  const result: LCSMatch[] = []
  let i = m
  let j = n
  
  while (i > 0 && j > 0) {
    if (oldLines[i - 1] === newLines[j - 1]) {
      result.unshift({ oldIdx: i - 1, newIdx: j - 1 })
      i--
      j--
    } else if (dp[i - 1][j] > dp[i][j - 1]) {
      i--
    } else {
      j--
    }
  }
  
  return result
}

// 将 HTML 转换为纯文本用于对比
const htmlToText = (html: string): string => {
  // 简单的 HTML 标签移除
  return html
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
}

// 加载版本内容
const loadVersions = async () => {
  loading.value = true

  try {
    const [left, right] = await Promise.all([
      $fetch<{ content: string; versionNum: number; author: any; createdAt: string }>(
        `/api/documents/${props.documentId}/versions/${props.leftVersionNum}`
      ),
      $fetch<{ content: string; versionNum: number; author: any; createdAt: string }>(
        `/api/documents/${props.documentId}/versions/${props.rightVersionNum}`
      ),
    ])

    leftVersion.value = left
    rightVersion.value = right
    leftContent.value = left.content
    rightContent.value = right.content

    // 计算差异
    const leftText = htmlToText(left.content)
    const rightText = htmlToText(right.content)
    diffResult.value = computeDiff(leftText, rightText)
  } catch (e) {
    toast.add({
      title: '加载失败',
      description: '无法加载版本内容',
      color: 'error',
    })
  } finally {
    loading.value = false
  }
}

// 统计变更
const stats = computed(() => {
  const added = diffResult.value.filter(l => l.type === 'added').length
  const removed = diffResult.value.filter(l => l.type === 'removed').length
  const unchanged = diffResult.value.filter(l => l.type === 'unchanged').length
  return { added, removed, unchanged }
})

// 格式化时间
const formatTime = (date: string) => {
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 初始化
onMounted(() => {
  loadVersions()
})

// 监听版本变化
watch(
  () => [props.leftVersionNum, props.rightVersionNum],
  () => loadVersions()
)
</script>

<template>
  <div class="h-full flex flex-col bg-white dark:bg-gray-900">
    <!-- 头部 -->
    <div class="flex-shrink-0 px-4 py-3 border-b border-gray-200 dark:border-gray-800">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <h3 class="font-semibold text-gray-900 dark:text-white">版本对比</h3>
          <div class="flex items-center gap-2 text-sm">
            <span class="text-emerald-600 dark:text-emerald-400">
              +{{ stats.added }} 行
            </span>
            <span class="text-red-600 dark:text-red-400">
              -{{ stats.removed }} 行
            </span>
          </div>
        </div>
        <UButton
          variant="ghost"
          color="neutral"
          icon="i-lucide-x"
          size="sm"
          @click="emit('close')"
        />
      </div>

      <!-- 版本信息 -->
      <div v-if="!loading" class="flex items-center gap-4 mt-2 text-sm text-gray-500">
        <div class="flex items-center gap-2">
          <span class="font-medium text-red-600 dark:text-red-400">v{{ leftVersionNum }}</span>
          <span v-if="leftVersion?.author">
            {{ leftVersion.author.name }}
          </span>
          <span v-if="leftVersion?.createdAt">
            {{ formatTime(leftVersion.createdAt) }}
          </span>
        </div>
        <UIcon name="i-lucide-arrow-right" class="w-4 h-4" />
        <div class="flex items-center gap-2">
          <span class="font-medium text-emerald-600 dark:text-emerald-400">v{{ rightVersionNum }}</span>
          <span v-if="rightVersion?.author">
            {{ rightVersion.author.name }}
          </span>
          <span v-if="rightVersion?.createdAt">
            {{ formatTime(rightVersion.createdAt) }}
          </span>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <UIcon name="i-lucide-loader-2" class="w-8 h-8 animate-spin text-gray-400" />
    </div>

    <!-- 差异视图 -->
    <div v-else class="flex-1 overflow-auto">
      <div class="font-mono text-sm">
        <div
          v-for="(line, index) in diffResult"
          :key="index"
          :class="[
            'flex',
            line.type === 'added' && 'bg-emerald-50 dark:bg-emerald-900/20',
            line.type === 'removed' && 'bg-red-50 dark:bg-red-900/20',
          ]"
        >
          <!-- 行号 -->
          <div class="flex-shrink-0 w-20 flex text-xs text-gray-400 select-none border-r border-gray-200 dark:border-gray-700">
            <span class="w-10 px-2 py-1 text-right border-r border-gray-200 dark:border-gray-700">
              {{ line.leftLineNum || '' }}
            </span>
            <span class="w-10 px-2 py-1 text-right">
              {{ line.rightLineNum || '' }}
            </span>
          </div>

          <!-- 变更标记 -->
          <div 
            :class="[
              'flex-shrink-0 w-6 flex items-center justify-center text-xs font-bold',
              line.type === 'added' && 'text-emerald-600 dark:text-emerald-400',
              line.type === 'removed' && 'text-red-600 dark:text-red-400',
            ]"
          >
            <span v-if="line.type === 'added'">+</span>
            <span v-else-if="line.type === 'removed'">-</span>
          </div>

          <!-- 内容 -->
          <div 
            :class="[
              'flex-1 px-2 py-1 whitespace-pre-wrap break-all',
              line.type === 'added' && 'text-emerald-800 dark:text-emerald-200',
              line.type === 'removed' && 'text-red-800 dark:text-red-200',
              line.type === 'unchanged' && 'text-gray-700 dark:text-gray-300',
            ]"
          >
            {{ line.content || ' ' }}
          </div>
        </div>

        <!-- 空状态 -->
        <div 
          v-if="diffResult.length === 0" 
          class="p-8 text-center text-gray-500"
        >
          两个版本内容相同
        </div>
      </div>
    </div>
  </div>
</template>
