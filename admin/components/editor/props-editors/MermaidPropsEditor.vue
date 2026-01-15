<script setup lang="ts">
/**
 * Mermaid 图表属性编辑器
 */
import { ref, watch } from 'vue'

interface MermaidProps {
  content: string
  title?: string
}

const props = defineProps<{
  modelValue: MermaidProps
}>()

const emit = defineEmits<{
  'update:modelValue': [value: MermaidProps]
}>()

// 本地状态
const localValue = ref<MermaidProps>({
  content: props.modelValue?.content || 'graph TD\n  A[开始] --> B[结束]',
  title: props.modelValue?.title || '',
})

// 同步到父组件
watch(localValue, (newValue) => {
  emit('update:modelValue', { ...newValue })
}, { deep: true })

// 监听外部变化
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    localValue.value = {
      content: newValue.content || 'graph TD\n  A[开始] --> B[结束]',
      title: newValue.title || '',
    }
  }
}, { deep: true })

// 预设模板
const templates = [
  {
    name: '流程图',
    content: `graph TD
  A[开始] --> B{判断条件}
  B -->|是| C[执行操作1]
  B -->|否| D[执行操作2]
  C --> E[结束]
  D --> E`,
  },
  {
    name: '时序图',
    content: `sequenceDiagram
  participant A as 用户
  participant B as 系统
  A->>B: 发送请求
  B-->>A: 返回响应`,
  },
  {
    name: '类图',
    content: `classDiagram
  class Animal {
    +String name
    +int age
    +makeSound()
  }
  class Dog {
    +bark()
  }
  Animal <|-- Dog`,
  },
  {
    name: '状态图',
    content: `stateDiagram-v2
  [*] --> 待处理
  待处理 --> 处理中: 开始处理
  处理中 --> 已完成: 处理完成
  处理中 --> 已取消: 取消
  已完成 --> [*]
  已取消 --> [*]`,
  },
  {
    name: '饼图',
    content: `pie title 项目分布
  "项目A" : 40
  "项目B" : 30
  "项目C" : 20
  "其他" : 10`,
  },
  {
    name: '甘特图',
    content: `gantt
  title 项目计划
  dateFormat YYYY-MM-DD
  section 阶段1
  任务1 :a1, 2024-01-01, 30d
  任务2 :after a1, 20d
  section 阶段2
  任务3 :2024-02-01, 25d`,
  },
]

// 应用模板
const applyTemplate = (template: typeof templates[0]) => {
  localValue.value.content = template.content
}
</script>

<template>
  <div class="mermaid-props-editor space-y-4">
    <!-- 标题 -->
    <UFormGroup label="图表标题（可选）">
      <UInput
        v-model="localValue.title"
        placeholder="输入图表标题..."
      />
    </UFormGroup>

    <!-- 预设模板 -->
    <UFormGroup label="快速模板">
      <div class="flex flex-wrap gap-2">
        <UButton
          v-for="template in templates"
          :key="template.name"
          variant="outline"
          size="xs"
          @click="applyTemplate(template)"
        >
          {{ template.name }}
        </UButton>
      </div>
    </UFormGroup>

    <!-- Mermaid 代码 -->
    <UFormGroup label="Mermaid 代码" required>
      <UTextarea
        v-model="localValue.content"
        placeholder="输入 Mermaid 图表代码..."
        :rows="12"
        class="font-mono text-sm"
      />
    </UFormGroup>
    
    <!-- 帮助链接 -->
    <div class="text-xs text-gray-500 bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
      <UIcon name="i-lucide-info" class="inline-block mr-1" />
      查看 
      <a 
        href="https://mermaid.js.org/syntax/flowchart.html" 
        target="_blank" 
        class="text-primary-500 hover:underline"
      >
        Mermaid 语法文档
      </a>
      了解更多图表类型和语法。
    </div>
  </div>
</template>
