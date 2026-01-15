<script setup lang="ts">
/**
 * 语言表单组件
 * 用于添加/编辑语言
 * 
 * Requirements: 6.9
 */

interface FormState {
  code: string
  name: string
  nativeName: string
  isDefault: boolean
  isEnabled: boolean
}

interface FormError {
  name: string
  message: string
}

const props = defineProps<{
  formState: FormState
  formErrors: FormError[]
  isSaving: boolean
  isEditing: boolean
}>()

const emit = defineEmits<{
  submit: []
  cancel: []
}>()

// 获取字段错误
const getError = (fieldName: string): string | undefined => {
  return props.formErrors.find(e => e.name === fieldName)?.message
}

// 处理表单提交
const handleSubmit = (e: Event) => {
  e.preventDefault()
  emit('submit')
}
</script>

<template>
  <form @submit="handleSubmit" class="space-y-5">
    <!-- 语言代码 -->
    <div>
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
        语言代码 <span class="text-red-500">*</span>
      </label>
      <UInput
        v-model="formState.code"
        placeholder="例如: zh, en, vi"
        :disabled="isEditing"
        :color="getError('code') ? 'error' : undefined"
        class="w-full"
      />
      <p v-if="getError('code')" class="mt-1 text-sm text-red-500">
        {{ getError('code') }}
      </p>
      <p v-else-if="!isEditing" class="mt-1 text-xs text-gray-500 dark:text-gray-400">
        语言代码创建后不可修改
      </p>
    </div>

    <!-- 语言名称 -->
    <div>
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
        语言名称 <span class="text-red-500">*</span>
      </label>
      <UInput
        v-model="formState.name"
        placeholder="例如: Chinese, English, Vietnamese"
        :color="getError('name') ? 'error' : undefined"
        class="w-full"
      />
      <p v-if="getError('name')" class="mt-1 text-sm text-red-500">
        {{ getError('name') }}
      </p>
    </div>

    <!-- 本地名称 -->
    <div>
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
        本地名称 <span class="text-red-500">*</span>
      </label>
      <UInput
        v-model="formState.nativeName"
        placeholder="例如: 中文, English, Tiếng Việt"
        :color="getError('nativeName') ? 'error' : undefined"
        class="w-full"
      />
      <p v-if="getError('nativeName')" class="mt-1 text-sm text-red-500">
        {{ getError('nativeName') }}
      </p>
    </div>

    <!-- 选项 -->
    <div class="flex items-center gap-6 pt-2">
      <label class="flex items-center gap-2 cursor-pointer">
        <UCheckbox v-model="formState.isDefault" />
        <span class="text-sm text-gray-700 dark:text-gray-300">设为默认语言</span>
      </label>
      
      <label class="flex items-center gap-2 cursor-pointer">
        <UCheckbox v-model="formState.isEnabled" />
        <span class="text-sm text-gray-700 dark:text-gray-300">启用</span>
      </label>
    </div>

    <!-- 按钮 -->
    <div class="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-800">
      <UButton
        type="button"
        variant="ghost"
        color="neutral"
        @click="emit('cancel')"
      >
        取消
      </UButton>
      <UButton
        type="submit"
        color="primary"
        :loading="isSaving"
      >
        {{ isEditing ? '保存' : '添加' }}
      </UButton>
    </div>
  </form>
</template>
