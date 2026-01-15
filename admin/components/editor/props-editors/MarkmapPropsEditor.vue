<script setup lang="ts">
/**
 * Markmap 思维导图属性编辑器
 */
import { ref, watch } from 'vue'

interface MarkmapProps {
  content: string
}

const props = defineProps<{
  modelValue: MarkmapProps
}>()

const emit = defineEmits<{
  'update:modelValue': [value: MarkmapProps]
}>()

// 本地状态
const localValue = ref<MarkmapProps>({
  content: props.modelValue?.content || '# 主题\n## 分支1\n## 分支2',
})

// 同步到父组件
watch(localValue, (newValue) => {
  emit('update:modelValue', { ...newValue })
}, { deep: true })

// 监听外部变化
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    localValue.value = {
      content: newValue.content || '# 主题\n## 分支1\n## 分支2',
    }
  }
}, { deep: true })

// 预设模板
const templates = [
  {
    name: '基础结构',
    content: `# 中心主题

## 分支一
### 子节点 1.1
### 子节点 1.2

## 分支二
### 子节点 2.1
### 子节点 2.2

## 分支三`,
  },
  {
    name: '项目规划',
    content: `# 项目规划

## 需求分析
### 用户调研
### 竞品分析
### 需求文档

## 设计阶段
### UI 设计
### 技术方案
### 数据库设计

## 开发阶段
### 前端开发
### 后端开发
### 测试

## 上线部署
### 环境准备
### 部署上线
### 监控运维`,
  },
  {
    name: '学习笔记',
    content: `# 学习主题

## 核心概念
### 概念一
- 要点 1
- 要点 2
### 概念二

## 实践应用
### 案例一
### 案例二

## 常见问题
### 问题一
### 问题二

## 参考资料
### 书籍
### 网站`,
  },
  {
    name: '会议纪要',
    content: `# 会议主题

## 参会人员
### 主持人
### 与会者

## 议题讨论
### 议题一
- 讨论内容
- 结论
### 议题二
- 讨论内容
- 结论

## 行动项
### 任务一
- 负责人
- 截止日期
### 任务二

## 下次会议
### 时间
### 议题`,
  },
]

// 应用模板
const applyTemplate = (template: typeof templates[0]) => {
  localValue.value.content = template.content
}
</script>

<template>
  <div class="markmap-props-editor space-y-4">
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

    <!-- Markdown 内容 -->
    <UFormGroup label="思维导图内容 (Markdown)" required>
      <UTextarea
        v-model="localValue.content"
        placeholder="使用 Markdown 标题语法创建思维导图...
# 中心主题
## 分支一
### 子节点
## 分支二"
        :rows="12"
        class="font-mono text-sm"
      />
    </UFormGroup>
    
    <!-- 语法说明 -->
    <div class="text-xs text-gray-500 bg-gray-50 dark:bg-gray-800 p-3 rounded-lg space-y-1">
      <div class="font-medium mb-2">
        <UIcon name="i-lucide-info" class="inline-block mr-1" />
        语法说明
      </div>
      <div><code class="bg-gray-200 dark:bg-gray-700 px-1 rounded"># 标题</code> - 中心节点</div>
      <div><code class="bg-gray-200 dark:bg-gray-700 px-1 rounded">## 标题</code> - 一级分支</div>
      <div><code class="bg-gray-200 dark:bg-gray-700 px-1 rounded">### 标题</code> - 二级分支</div>
      <div><code class="bg-gray-200 dark:bg-gray-700 px-1 rounded">- 列表项</code> - 叶子节点</div>
    </div>
  </div>
</template>
