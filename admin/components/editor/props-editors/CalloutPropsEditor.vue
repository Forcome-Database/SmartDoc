<script setup lang="ts">
/**
 * 提示框属性编辑器
 */
import { ref, watch } from 'vue'

interface CalloutProps {
  type: string
  title?: string
  content: string
}

const props = defineProps<{
  modelValue: CalloutProps
}>()

const emit = defineEmits<{
  'update:modelValue': [value: CalloutProps]
}>()

// 本地状态
const localValue = ref<CalloutProps>({
  type: props.modelValue?.type || 'info',
  title: props.modelValue?.title || '',
  content: props.modelValue?.content || '',
})

// 同步到父组件
watch(localValue, (newValue) => {
  emit('update:modelValue', { ...newValue })
}, { deep: true })

// 监听外部变化
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    localValue.value = {
      type: newValue.type || 'info',
      title: newValue.title || '',
      content: newValue.content || '',
    }
  }
}, { deep: true })

// 提示框类型选项
const typeOptions = [
  {
    value: 'info',
    label: '信息',
    icon: 'i-lucide-info',
    color: 'text-blue-600',
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    description: '用于一般性信息提示',
  },
  {
    value: 'tip',
    label: '提示',
    icon: 'i-lucide-lightbulb',
    color: 'text-green-600',
    bg: 'bg-green-50 dark:bg-green-900/20',
    description: '用于有用的建议或技巧',
  },
  {
    value: 'warning',
    label: '警告',
    icon: 'i-lucide-alert-triangle',
    color: 'text-yellow-600',
    bg: 'bg-yellow-50 dark:bg-yellow-900/20',
    description: '用于需要注意的内容',
  },
  {
    value: 'danger',
    label: '危险',
    icon: 'i-lucide-alert-circle',
    color: 'text-red-600',
    bg: 'bg-red-50 dark:bg-red-900/20',
    description: '用于重要警告或错误',
  },
]

// 当前选中的类型配置
const currentType = computed(() => {
  return typeOptions.find(t => t.value === localValue.value.type) || typeOptions[0]
})
</script>

<template>
  <div class="callout-props-editor space-y-4">
    <!-- 类型选择 -->
    <UFormGroup label="提示框类型" required>
      <div class="grid grid-cols-2 gap-2">
        <button
          v-for="option in typeOptions"
          :key="option.value"
          class="flex items-center gap-2 p-3 rounded-lg border-2 transition-all text-left"
          :class="[
            localValue.type === option.value 
              ? 'border-primary-500 ' + option.bg
              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
          ]"
          @click="localValue.type = option.value"
        >
          <UIcon :name="option.icon" class="w-5 h-5" :class="option.color" />
          <div>
            <div class="font-medium text-sm">{{ option.label }}</div>
            <div class="text-xs text-gray-500">{{ option.description }}</div>
          </div>
        </button>
      </div>
    </UFormGroup>

    <!-- 标题 -->
    <UFormGroup label="标题（可选）">
      <UInput
        v-model="localValue.title"
        :placeholder="`默认显示「${currentType.label}」`"
      />
    </UFormGroup>

    <!-- 内容 -->
    <UFormGroup label="内容" required>
      <UTextarea
        v-model="localValue.content"
        placeholder="输入提示框内容..."
        :rows="4"
      />
    </UFormGroup>
    
    <!-- 预览 -->
    <UFormGroup label="预览">
      <div 
        class="p-4 rounded-lg border"
        :class="currentType.bg"
      >
        <div class="flex items-start gap-3">
          <UIcon 
            :name="currentType.icon" 
            class="w-5 h-5 mt-0.5" 
            :class="currentType.color" 
          />
          <div class="flex-1">
            <div v-if="localValue.title" class="font-medium mb-1">
              {{ localValue.title }}
            </div>
            <div v-else class="font-medium mb-1">
              {{ currentType.label }}
            </div>
            <div class="text-sm">
              {{ localValue.content || '提示内容将显示在这里...' }}
            </div>
          </div>
        </div>
      </div>
    </UFormGroup>
  </div>
</template>
