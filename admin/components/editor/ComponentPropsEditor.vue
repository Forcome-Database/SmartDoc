<script setup lang="ts">
/**
 * 组件属性编辑器
 * 根据组件类型显示对应的属性编辑表单
 */
import { ref, watch, computed } from 'vue'

const props = defineProps<{
  componentName: string
  props: Record<string, any>
}>()

const emit = defineEmits<{
  save: [props: Record<string, any>]
  cancel: []
}>()

// 本地编辑状态
const localProps = ref<Record<string, any>>({ ...props.props })

// 监听外部 props 变化
watch(() => props.props, (newProps) => {
  localProps.value = { ...newProps }
}, { deep: true })

// 保存
const handleSave = () => {
  emit('save', { ...localProps.value })
}

// 取消
const handleCancel = () => {
  localProps.value = { ...props.props }
  emit('cancel')
}

// 组件编辑器映射
const editorComponents = computed(() => {
  return {
    Quiz: 'QuizPropsEditor',
    MermaidWrapper: 'MermaidPropsEditor',
    Markmap: 'MarkmapPropsEditor',
    Callout: 'CalloutPropsEditor',
  }
})

const currentEditor = computed(() => editorComponents.value[props.componentName as keyof typeof editorComponents.value])
</script>

<template>
  <div class="component-props-editor">
    <!-- Quiz 编辑器 -->
    <QuizPropsEditor
      v-if="componentName === 'Quiz'"
      v-model="localProps"
    />
    
    <!-- Mermaid 编辑器 -->
    <MermaidPropsEditor
      v-else-if="componentName === 'MermaidWrapper'"
      v-model="localProps"
    />
    
    <!-- Markmap 编辑器 -->
    <MarkmapPropsEditor
      v-else-if="componentName === 'Markmap'"
      v-model="localProps"
    />
    
    <!-- Callout 编辑器 -->
    <CalloutPropsEditor
      v-else-if="componentName === 'Callout'"
      v-model="localProps"
    />
    
    <!-- 通用编辑器（JSON） -->
    <div v-else class="space-y-4">
      <UFormGroup label="组件属性 (JSON)">
        <UTextarea
          :model-value="JSON.stringify(localProps, null, 2)"
          @update:model-value="(v) => { try { localProps = JSON.parse(v) } catch {} }"
          :rows="10"
          class="font-mono text-sm"
        />
      </UFormGroup>
    </div>
    
    <!-- 操作按钮 -->
    <div class="flex justify-end gap-2 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
      <UButton
        variant="ghost"
        color="neutral"
        @click="handleCancel"
      >
        取消
      </UButton>
      <UButton
        color="primary"
        @click="handleSave"
      >
        保存
      </UButton>
    </div>
  </div>
</template>

<style scoped>
.component-props-editor {
  @apply space-y-4;
}
</style>
