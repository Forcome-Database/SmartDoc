<script setup lang="ts">
/**
 * 单个评论项组件
 * 
 * Requirements: 13.9
 */
import type { Comment } from '~/composables/useComments'

const props = defineProps<{
  comment: Comment
  editingId: string | null
  replyingTo: string | null
  depth?: number
}>()

const emit = defineEmits<{
  'reply': [id: string]
  'cancel-reply': []
  'submit-reply': [content: string]
  'edit': [id: string, content: string]
  'cancel-edit': []
  'submit-edit': [id: string, content: string]
  'resolve': [id: string]
  'unresolve': [id: string]
  'delete': [id: string]
}>()

const depth = computed(() => props.depth || 0)
const isEditing = computed(() => props.editingId === props.comment.id)
const isReplying = computed(() => props.replyingTo === props.comment.id)

// 编辑内容
const editContent = ref(props.comment.content)

// 回复内容
const replyContent = ref('')

// 格式化时间
const formatTime = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60 * 1000) return '刚刚'
  if (diff < 60 * 60 * 1000) return `${Math.floor(diff / (60 * 1000))} 分钟前`
  if (diff < 24 * 60 * 60 * 1000) return `${Math.floor(diff / (60 * 60 * 1000))} 小时前`
  if (diff < 7 * 24 * 60 * 60 * 1000) return `${Math.floor(diff / (24 * 60 * 60 * 1000))} 天前`
  
  return date.toLocaleDateString('zh-CN')
}

// 确认删除
const showDeleteConfirm = ref(false)
</script>

<template>
  <div :class="['px-4 py-3', depth > 0 ? 'ml-8 border-l-2 border-gray-100 dark:border-gray-800' : '']">
    <!-- 评论头部 -->
    <div class="flex items-start gap-3">
      <UAvatar
        :src="comment.author.avatar || undefined"
        :alt="comment.author.name"
        size="sm"
      />
      
      <div class="flex-1 min-w-0">
        <!-- 作者和时间 -->
        <div class="flex items-center gap-2">
          <span class="font-medium text-gray-900 dark:text-white text-sm">
            {{ comment.author.name }}
          </span>
          <span class="text-xs text-gray-500">
            {{ formatTime(comment.createdAt) }}
          </span>
          <UBadge v-if="comment.isResolved" color="success" variant="subtle" size="xs">
            已解决
          </UBadge>
        </div>
</template>

        <!-- 评论内容 -->
        <div v-if="!isEditing" class="mt-1 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
          {{ comment.content }}
        </div>

        <!-- 编辑模式 -->
        <div v-else class="mt-2">
          <UTextarea
            v-model="editContent"
            :rows="2"
            class="w-full"
          />
          <div class="flex justify-end gap-2 mt-2">
            <UButton size="xs" variant="ghost" color="neutral" @click="emit('cancel-edit')">
              取消
            </UButton>
            <UButton 
              size="xs" 
              color="primary" 
              :disabled="!editContent.trim()"
              @click="emit('submit-edit', comment.id, editContent)"
            >
              保存
            </UButton>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div v-if="!isEditing" class="flex items-center gap-2 mt-2">
          <UButton
            v-if="depth === 0"
            size="xs"
            variant="ghost"
            color="neutral"
            icon="i-lucide-reply"
            @click="emit('reply', comment.id)"
          >
            回复
          </UButton>
          <UButton
            size="xs"
            variant="ghost"
            color="neutral"
            icon="i-lucide-pencil"
            @click="emit('edit', comment.id, comment.content)"
          >
            编辑
          </UButton>
          <UButton
            v-if="!comment.isResolved"
            size="xs"
            variant="ghost"
            color="success"
            icon="i-lucide-check"
            @click="emit('resolve', comment.id)"
          >
            解决
          </UButton>
          <UButton
            v-else
            size="xs"
            variant="ghost"
            color="warning"
            icon="i-lucide-rotate-ccw"
            @click="emit('unresolve', comment.id)"
          >
            重新打开
          </UButton>
          <UButton
            size="xs"
            variant="ghost"
            color="error"
            icon="i-lucide-trash-2"
            @click="showDeleteConfirm = true"
          />
        </div>

        <!-- 回复输入框 -->
        <div v-if="isReplying" class="mt-3">
          <UTextarea
            v-model="replyContent"
            placeholder="回复..."
            :rows="2"
            class="w-full"
          />
          <div class="flex justify-end gap-2 mt-2">
            <UButton size="xs" variant="ghost" color="neutral" @click="emit('cancel-reply')">
              取消
            </UButton>
            <UButton 
              size="xs" 
              color="primary" 
              :disabled="!replyContent.trim()"
              @click="emit('submit-reply', replyContent)"
            >
              回复
            </UButton>
          </div>
        </div>
      </div>
    </div>

    <!-- 回复列表 -->
    <div v-if="comment.replies && comment.replies.length > 0" class="mt-2">
      <CommentItem
        v-for="reply in comment.replies"
        :key="reply.id"
        :comment="reply"
        :editing-id="editingId"
        :replying-to="replyingTo"
        :depth="depth + 1"
        @reply="emit('reply', $event)"
        @cancel-reply="emit('cancel-reply')"
        @submit-reply="emit('submit-reply', $event)"
        @edit="emit('edit', $event[0], $event[1])"
        @cancel-edit="emit('cancel-edit')"
        @submit-edit="emit('submit-edit', $event[0], $event[1])"
        @resolve="emit('resolve', $event)"
        @unresolve="emit('unresolve', $event)"
        @delete="emit('delete', $event)"
      />
    </div>

    <!-- 删除确认对话框 -->
    <UModal v-model:open="showDeleteConfirm">
      <template #content>
        <UCard>
          <template #header>
            <span class="font-semibold">确认删除</span>
          </template>
          <p class="text-gray-600 dark:text-gray-400">确定要删除这条评论吗？此操作不可撤销。</p>
          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton variant="ghost" color="neutral" @click="showDeleteConfirm = false">取消</UButton>
              <UButton color="error" @click="() => { emit('delete', comment.id); showDeleteConfirm = false }">删除</UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>
  </div>
</template>
