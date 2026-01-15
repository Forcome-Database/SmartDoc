<script setup lang="ts">
/**
 * 评论面板组件
 * 显示文档评论列表，支持添加、回复、解决评论
 * 
 * Requirements: 13.9
 */
import type { Comment } from '~/composables/useComments'

const props = defineProps<{
  documentId: string
}>()

const toast = useToast()

// 使用评论 composable
const {
  comments,
  total,
  loading,
  error,
  load,
  add,
  update,
  remove,
  resolve,
  unresolve,
} = useComments(() => props.documentId)

// 新评论内容
const newCommentContent = ref('')
const submitting = ref(false)

// 回复状态
const replyingTo = ref<string | null>(null)
const replyContent = ref('')

// 编辑状态
const editingId = ref<string | null>(null)
const editContent = ref('')

// @提及用户搜索
const mentionQuery = ref('')
const showMentionList = ref(false)
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- 头部 -->
    <div class="flex-shrink-0 px-4 py-3 border-b border-gray-200 dark:border-gray-800">
      <div class="flex items-center justify-between">
        <h3 class="font-semibold text-gray-900 dark:text-white">
          评论 <span class="text-gray-500 font-normal">({{ total }})</span>
        </h3>
        <UButton
          size="xs"
          variant="ghost"
          color="neutral"
          icon="i-lucide-refresh-cw"
          :loading="loading"
          @click="load"
        />
      </div>
    </div>
</template>

    <!-- 新评论输入 -->
    <div class="flex-shrink-0 px-4 py-3 border-b border-gray-200 dark:border-gray-800">
      <div class="flex gap-2">
        <UTextarea
          v-model="newCommentContent"
          placeholder="添加评论... 使用 @ 提及用户"
          :rows="2"
          class="flex-1"
          :disabled="submitting"
        />
        <UButton
          color="primary"
          icon="i-lucide-send"
          :loading="submitting"
          :disabled="!newCommentContent.trim()"
          @click="async () => {
            if (!newCommentContent.trim()) return
            submitting = true
            const result = await add(newCommentContent)
            if (result) {
              newCommentContent = ''
              toast.add({ title: '评论已添加', color: 'success' })
            }
            submitting = false
          }"
        />
      </div>
    </div>

    <!-- 评论列表 -->
    <div class="flex-1 overflow-auto">
      <!-- 加载状态 -->
      <div v-if="loading && comments.length === 0" class="flex items-center justify-center py-8">
        <UIcon name="i-lucide-loader-2" class="w-6 h-6 animate-spin text-gray-400" />
      </div>

      <!-- 空状态 -->
      <div v-else-if="comments.length === 0" class="flex flex-col items-center justify-center py-8 text-center">
        <UIcon name="i-lucide-message-square" class="w-12 h-12 text-gray-300 mb-2" />
        <p class="text-gray-500">暂无评论</p>
        <p class="text-sm text-gray-400">成为第一个评论的人</p>
      </div>

      <!-- 评论列表 -->
      <div v-else class="divide-y divide-gray-100 dark:divide-gray-800">
        <CommentItem
          v-for="comment in comments"
          :key="comment.id"
          :comment="comment"
          :editing-id="editingId"
          :replying-to="replyingTo"
          @reply="(id) => { replyingTo = id; replyContent = '' }"
          @cancel-reply="replyingTo = null"
          @submit-reply="async (content) => {
            const result = await add(content, { parentId: replyingTo! })
            if (result) {
              replyingTo = null
              replyContent = ''
            }
          }"
          @edit="(id, content) => { editingId = id; editContent = content }"
          @cancel-edit="editingId = null"
          @submit-edit="async (id, content) => {
            const result = await update(id, { content })
            if (result) {
              editingId = null
              editContent = ''
            }
          }"
          @resolve="resolve"
          @unresolve="unresolve"
          @delete="async (id) => {
            const success = await remove(id)
            if (success) {
              toast.add({ title: '评论已删除', color: 'success' })
            }
          }"
        />
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="flex-shrink-0 px-4 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
      {{ error }}
    </div>
  </div>
</template>
