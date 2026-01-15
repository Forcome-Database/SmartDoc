<script setup lang="ts">
/**
 * 选择题属性编辑器
 */
import { ref, watch } from 'vue'

interface QuizProps {
  question: string
  options: string[]
  answer: number
  explanation?: string
}

const props = defineProps<{
  modelValue: QuizProps
}>()

const emit = defineEmits<{
  'update:modelValue': [value: QuizProps]
}>()

// 本地状态
const localValue = ref<QuizProps>({
  question: props.modelValue?.question || '',
  options: props.modelValue?.options || ['', '', '', ''],
  answer: props.modelValue?.answer || 0,
  explanation: props.modelValue?.explanation || '',
})

// 同步到父组件
watch(localValue, (newValue) => {
  emit('update:modelValue', { ...newValue })
}, { deep: true })

// 监听外部变化
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    localValue.value = {
      question: newValue.question || '',
      options: newValue.options || ['', '', '', ''],
      answer: newValue.answer || 0,
      explanation: newValue.explanation || '',
    }
  }
}, { deep: true })

// 添加选项
const addOption = () => {
  localValue.value.options.push('')
}

// 删除选项
const removeOption = (index: number) => {
  if (localValue.value.options.length <= 2) return
  localValue.value.options.splice(index, 1)
  // 调整正确答案索引
  if (localValue.value.answer >= index && localValue.value.answer > 0) {
    localValue.value.answer--
  }
  if (localValue.value.answer >= localValue.value.options.length) {
    localValue.value.answer = localValue.value.options.length - 1
  }
}

// 设置正确答案
const setAnswer = (index: number) => {
  localValue.value.answer = index
}

// 移动选项
const moveOption = (index: number, direction: 'up' | 'down') => {
  const newIndex = direction === 'up' ? index - 1 : index + 1
  if (newIndex < 0 || newIndex >= localValue.value.options.length) return
  
  const options = [...localValue.value.options]
  const temp = options[index]
  options[index] = options[newIndex]
  options[newIndex] = temp
  localValue.value.options = options
  
  // 调整正确答案索引
  if (localValue.value.answer === index) {
    localValue.value.answer = newIndex
  } else if (localValue.value.answer === newIndex) {
    localValue.value.answer = index
  }
}
</script>

<template>
  <div class="quiz-props-editor space-y-4">
    <!-- 题目 -->
    <UFormGroup label="题目" required>
      <UTextarea
        v-model="localValue.question"
        placeholder="请输入题目内容..."
        :rows="2"
      />
    </UFormGroup>

    <!-- 选项列表 -->
    <UFormGroup label="选项">
      <p class="text-xs text-gray-500 mb-2">点击单选按钮设置正确答案</p>
      <div class="space-y-2">
        <div
          v-for="(option, index) in localValue.options"
          :key="index"
          class="flex items-center gap-2 p-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800"
        >
          <!-- 排序按钮 -->
          <div class="flex flex-col gap-0.5">
            <UButton
              variant="ghost"
              size="xs"
              icon="i-lucide-chevron-up"
              :disabled="index === 0"
              @click="moveOption(index, 'up')"
            />
            <UButton
              variant="ghost"
              size="xs"
              icon="i-lucide-chevron-down"
              :disabled="index === localValue.options.length - 1"
              @click="moveOption(index, 'down')"
            />
          </div>
          
          <!-- 正确答案选择 -->
          <URadio
            :model-value="localValue.answer === index"
            @update:model-value="setAnswer(index)"
            :ui="{ wrapper: 'flex items-center' }"
          />
          
          <!-- 选项标签 -->
          <span class="w-6 text-sm font-medium text-gray-500">
            {{ String.fromCharCode(65 + index) }}.
          </span>
          
          <!-- 选项内容 -->
          <UInput
            v-model="localValue.options[index]"
            :placeholder="`选项 ${String.fromCharCode(65 + index)}`"
            class="flex-1"
          />
          
          <!-- 删除按钮 -->
          <UButton
            variant="ghost"
            size="xs"
            color="error"
            icon="i-lucide-trash-2"
            :disabled="localValue.options.length <= 2"
            @click="removeOption(index)"
          />
        </div>
      </div>

      <UButton
        variant="outline"
        size="sm"
        icon="i-lucide-plus"
        class="mt-2"
        @click="addOption"
      >
        添加选项
      </UButton>
    </UFormGroup>

    <!-- 答案解析 -->
    <UFormGroup label="答案解析（可选）">
      <UTextarea
        v-model="localValue.explanation"
        placeholder="解释为什么这个答案是正确的..."
        :rows="2"
      />
    </UFormGroup>
    
    <!-- 预览提示 -->
    <div class="text-xs text-gray-500 bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
      <UIcon name="i-lucide-info" class="inline-block mr-1" />
      当前正确答案：<span class="font-medium">{{ String.fromCharCode(65 + localValue.answer) }}</span>
    </div>
  </div>
</template>
