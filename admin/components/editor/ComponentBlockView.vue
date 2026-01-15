<script setup lang="ts">
/**
 * 组件块视图
 * 在编辑器中渲染实际的 Vue 组件
 */
import { NodeViewWrapper, nodeViewProps } from '@tiptap/vue-3'
import { computed, ref, markRaw, defineAsyncComponent } from 'vue'

const props = defineProps(nodeViewProps)

// 异步加载共享组件（来自 VitePress）- 添加错误处理
const componentMap: Record<string, any> = {}

// 尝试加载组件，失败时返回 null
try {
  componentMap.MermaidWrapper = markRaw(defineAsyncComponent({
    loader: () => import('@docs-components/MermaidWrapper.vue'),
    errorComponent: {
      template: '<div class="text-red-500 p-4">Mermaid 组件加载失败</div>'
    },
    loadingComponent: {
      template: '<div class="text-gray-500 p-4">加载中...</div>'
    }
  }))
  componentMap.Markmap = markRaw(defineAsyncComponent({
    loader: () => import('@docs-components/Markmap.vue'),
    errorComponent: {
      template: '<div class="text-red-500 p-4">Markmap 组件加载失败</div>'
    },
    loadingComponent: {
      template: '<div class="text-gray-500 p-4">加载中...</div>'
    }
  }))
} catch (e) {
  console.warn('Failed to load docs components:', e)
}

// 组件元数据
const componentMeta: Record<string, { label: string; icon: string; description: string }> = {
  Quiz: { 
    label: '选择题', 
    icon: '❓',
    description: '交互式选择题组件',
  },
  MermaidWrapper: { 
    label: 'Mermaid 图表', 
    icon: '📊',
    description: '流程图、时序图等',
  },
  Markmap: { 
    label: '思维导图', 
    icon: '🧠',
    description: 'Markmap 脑图',
  },
  Callout: { 
    label: '提示框', 
    icon: '💡',
    description: '信息提示框',
  },
}

const isEditing = ref(false)
const isPreview = ref(true)

const componentName = computed(() => props.node.attrs.componentName)
const componentProps = computed(() => props.node.attrs.props)
const meta = computed(() => componentMeta[componentName.value] || { 
  label: componentName.value, 
  icon: '📦',
  description: '自定义组件',
})
const CurrentComponent = computed(() => componentMap[componentName.value])

// 更新组件属性
const updateProps = (newProps: Record<string, any>) => {
  props.updateAttributes({ props: newProps })
  isEditing.value = false
  isPreview.value = true
}

// 取消编辑
const cancelEdit = () => {
  isEditing.value = false
  isPreview.value = true
}

// 删除组件
const deleteComponent = () => {
  props.deleteNode()
}

// 切换到编辑模式
const startEdit = () => {
  isPreview.value = false
  isEditing.value = true
}
</script>

<template>
  <NodeViewWrapper class="component-block" data-drag-handle>
    <!-- 组件头部 -->
    <div class="component-header">
      <div class="flex items-center gap-2">
        <UIcon name="i-lucide-grip-vertical" class="drag-handle cursor-grab text-gray-400 hover:text-gray-600" />
        <span class="text-lg">{{ meta.icon }}</span>
        <div>
          <span class="font-medium text-sm">{{ meta.label }}</span>
          <span class="text-xs text-gray-500 ml-2">{{ meta.description }}</span>
        </div>
      </div>

      <div class="flex items-center gap-1">
        <!-- 切换预览/编辑 -->
        <UButton
          :variant="isPreview ? 'solid' : 'ghost'"
          size="xs"
          icon="i-lucide-eye"
          title="预览"
          @click="isPreview = true; isEditing = false"
        />
        <UButton
          :variant="isEditing ? 'solid' : 'ghost'"
          size="xs"
          icon="i-lucide-pencil"
          title="编辑"
          @click="startEdit"
        />
        <UButton
          variant="ghost"
          size="xs"
          color="error"
          icon="i-lucide-trash-2"
          title="删除"
          @click="deleteComponent"
        />
      </div>
    </div>

    <!-- 组件内容 -->
    <div class="component-content">
      <!-- 预览模式 -->
      <div v-if="isPreview" class="component-preview">
        <!-- Quiz 组件预览 -->
        <template v-if="componentName === 'Quiz'">
          <QuizPreview :props="componentProps" />
        </template>
        
        <!-- Mermaid 组件预览 -->
        <template v-else-if="componentName === 'MermaidWrapper' && CurrentComponent">
          <Suspense>
            <component 
              :is="CurrentComponent" 
              :content="componentProps.content"
              :title="componentProps.title"
              :height="300"
            />
            <template #fallback>
              <div class="flex items-center justify-center h-40 text-gray-500">
                <UIcon name="i-lucide-loader-2" class="w-5 h-5 animate-spin mr-2" />
                加载中...
              </div>
            </template>
          </Suspense>
        </template>
        
        <!-- Markmap 组件预览 -->
        <template v-else-if="componentName === 'Markmap' && CurrentComponent">
          <Suspense>
            <component 
              :is="CurrentComponent" 
              :content="componentProps.content"
              :height="300"
            />
            <template #fallback>
              <div class="flex items-center justify-center h-40 text-gray-500">
                <UIcon name="i-lucide-loader-2" class="w-5 h-5 animate-spin mr-2" />
                加载中...
              </div>
            </template>
          </Suspense>
        </template>
        
        <!-- Callout 组件预览 -->
        <template v-else-if="componentName === 'Callout'">
          <CalloutPreview :props="componentProps" />
        </template>
        
        <!-- 未知组件 -->
        <template v-else>
          <div class="flex items-center justify-center h-20 text-gray-500 bg-gray-50 dark:bg-gray-800 rounded">
            <UIcon name="i-lucide-box" class="w-5 h-5 mr-2" />
            {{ componentName }} 组件
          </div>
        </template>
      </div>

      <!-- 编辑模式 -->
      <div v-else class="component-editor">
        <ComponentPropsEditor
          :component-name="componentName"
          :props="componentProps"
          @save="updateProps"
          @cancel="cancelEdit"
        />
      </div>
    </div>
  </NodeViewWrapper>
</template>

<!-- Quiz 预览组件 -->
<script lang="ts">
// Quiz 预览子组件
const QuizPreview = defineComponent({
  name: 'QuizPreview',
  props: {
    props: {
      type: Object as PropType<{
        question: string
        options: string[]
        answer: number
        explanation?: string
      }>,
      required: true,
    },
  },
  setup(props) {
    const selectedAnswer = ref<number | null>(null)
    const showResult = ref(false)
    
    const checkAnswer = (index: number) => {
      selectedAnswer.value = index
      showResult.value = true
    }
    
    const reset = () => {
      selectedAnswer.value = null
      showResult.value = false
    }
    
    return { selectedAnswer, showResult, checkAnswer, reset }
  },
  template: `
    <div class="quiz-preview p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
      <div class="font-medium mb-3">{{ props.question || '请输入题目' }}</div>
      <div class="space-y-2">
        <button
          v-for="(option, index) in props.options"
          :key="index"
          class="w-full text-left px-3 py-2 rounded border transition-colors"
          :class="{
            'border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700': !showResult,
            'border-green-500 bg-green-50 dark:bg-green-900/20': showResult && index === props.answer,
            'border-red-500 bg-red-50 dark:bg-red-900/20': showResult && selectedAnswer === index && index !== props.answer,
          }"
          @click="checkAnswer(index)"
          :disabled="showResult"
        >
          <span class="font-medium mr-2">{{ String.fromCharCode(65 + index) }}.</span>
          {{ option || '选项 ' + String.fromCharCode(65 + index) }}
        </button>
      </div>
      <div v-if="showResult && props.explanation" class="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded text-sm">
        <span class="font-medium">解析：</span>{{ props.explanation }}
      </div>
      <button
        v-if="showResult"
        class="mt-3 text-sm text-primary-500 hover:text-primary-600"
        @click="reset"
      >
        重新作答
      </button>
    </div>
  `,
})

// Callout 预览子组件
const CalloutPreview = defineComponent({
  name: 'CalloutPreview',
  props: {
    props: {
      type: Object as PropType<{
        type: string
        title?: string
        content: string
      }>,
      required: true,
    },
  },
  setup(props) {
    const typeConfig = computed(() => {
      const configs: Record<string, { icon: string; color: string; bg: string }> = {
        info: { icon: 'i-lucide-info', color: 'text-blue-600', bg: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800' },
        warning: { icon: 'i-lucide-alert-triangle', color: 'text-yellow-600', bg: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800' },
        danger: { icon: 'i-lucide-alert-circle', color: 'text-red-600', bg: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800' },
        tip: { icon: 'i-lucide-lightbulb', color: 'text-green-600', bg: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' },
      }
      return configs[props.props?.type || 'info'] || configs.info
    })
    
    return { typeConfig }
  },
  template: `
    <div class="callout-preview p-4 rounded-lg border" :class="typeConfig.bg">
      <div class="flex items-start gap-3">
        <UIcon :name="typeConfig.icon" class="w-5 h-5 mt-0.5" :class="typeConfig.color" />
        <div class="flex-1">
          <div v-if="props.title" class="font-medium mb-1">{{ props.title }}</div>
          <div class="text-sm">{{ props.content || '提示内容' }}</div>
        </div>
      </div>
    </div>
  `,
})
</script>

<style scoped>
@reference "tailwindcss";

.component-block {
  @apply my-4 border-2 border-dashed rounded-lg;
  border-color: color-mix(in srgb, var(--ui-primary) 40%, transparent);
  background-color: color-mix(in srgb, var(--ui-primary) 5%, transparent);
}

.component-header {
  @apply flex items-center justify-between px-3 py-2 border-b;
  border-color: color-mix(in srgb, var(--ui-primary) 30%, transparent);
  background-color: color-mix(in srgb, var(--ui-primary) 10%, transparent);
}

.component-content {
  @apply p-4;
}

.component-preview {
  @apply pointer-events-auto;
}

.component-editor {
  @apply bg-white dark:bg-gray-900 rounded-lg p-4;
}
</style>
