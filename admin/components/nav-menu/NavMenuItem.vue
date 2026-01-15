<script setup lang="ts">
/**
 * 导航菜单项组件
 * 递归渲染菜单树，支持展开/折叠、编辑、删除等操作
 */
import type { NavMenuNode } from '~/composables/useNavMenus'

const props = defineProps<{
  menu: NavMenuNode
  level: number
}>()

const emit = defineEmits<{
  edit: [menu: NavMenuNode]
  delete: [menu: NavMenuNode]
  addChild: [parentId: string]
  toggleVisibility: [menu: NavMenuNode]
}>()

// 展开状态
const isExpanded = ref(true)

// 获取菜单显示标题
const menuTitle = computed(() => {
  return props.menu.titles['zh'] || props.menu.titles['en'] || props.menu.titles['vi'] || `菜单 ${props.menu.id.slice(0, 8)}`
})

// 获取菜单类型图标
const typeIcon = computed(() => {
  switch (props.menu.type) {
    case 'link': return 'i-lucide-link'
    case 'dropdown': return 'i-lucide-chevron-down'
    case 'divider': return 'i-lucide-minus'
    default: return 'i-lucide-circle'
  }
})

// 获取菜单类型标签
const typeLabel = computed(() => {
  switch (props.menu.type) {
    case 'link': return '链接'
    case 'dropdown': return '下拉菜单'
    case 'divider': return '分割线'
    default: return props.menu.type
  }
})

// 获取目标描述
const targetDescription = computed(() => {
  if (props.menu.type === 'divider') return ''
  if (props.menu.type === 'dropdown') return `${props.menu.children?.length || 0} 个子项`
  
  switch (props.menu.targetType) {
    case 'category': return '指向栏目'
    case 'document': return '指向文档'
    case 'external': return props.menu.externalUrl || '外部链接'
    case 'none': return '无链接'
    default: return ''
  }
})

// 缩进样式
const indentStyle = computed(() => ({
  paddingLeft: `${props.level * 24 + 16}px`,
}))
</script>

<template>
  <div>
    <!-- 菜单项 -->
    <div
      class="flex items-center gap-3 py-3 px-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors group"
      :style="indentStyle"
    >
      <!-- 展开/折叠按钮 -->
      <button
        v-if="menu.type === 'dropdown' && menu.children?.length"
        class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
        @click="isExpanded = !isExpanded"
      >
        <UIcon
          :name="isExpanded ? 'i-lucide-chevron-down' : 'i-lucide-chevron-right'"
          class="w-4 h-4 text-gray-400"
        />
      </button>
      <div v-else class="w-6" />

      <!-- 类型图标 -->
      <div
        class="p-1.5 rounded-lg"
        :class="{
          'bg-blue-100 dark:bg-blue-500/20': menu.type === 'link',
          'bg-purple-100 dark:bg-purple-500/20': menu.type === 'dropdown',
          'bg-gray-100 dark:bg-gray-700': menu.type === 'divider',
        }"
      >
        <UIcon
          :name="typeIcon"
          class="w-4 h-4"
          :class="{
            'text-blue-600 dark:text-blue-400': menu.type === 'link',
            'text-purple-600 dark:text-purple-400': menu.type === 'dropdown',
            'text-gray-500 dark:text-gray-400': menu.type === 'divider',
          }"
        />
      </div>

      <!-- 标题和描述 -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2">
          <span
            class="font-medium truncate"
            :class="{
              'text-gray-900 dark:text-white': menu.isVisible,
              'text-gray-400 dark:text-gray-500 line-through': !menu.isVisible,
            }"
          >
            {{ menu.type === 'divider' ? '分割线' : menuTitle }}
          </span>
          <span
            class="text-xs px-1.5 py-0.5 rounded-full"
            :class="{
              'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300': menu.type === 'link',
              'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-300': menu.type === 'dropdown',
              'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400': menu.type === 'divider',
            }"
          >
            {{ typeLabel }}
          </span>
          <span v-if="!menu.isVisible" class="text-xs text-gray-400">
            (已隐藏)
          </span>
        </div>
        <p v-if="targetDescription" class="text-sm text-gray-500 dark:text-gray-400 truncate">
          {{ targetDescription }}
        </p>
      </div>

      <!-- 操作按钮 -->
      <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <!-- 添加子菜单（仅下拉菜单） -->
        <UButton
          v-if="menu.type === 'dropdown'"
          variant="ghost"
          color="neutral"
          size="xs"
          icon="i-lucide-plus"
          @click="emit('addChild', menu.id)"
        />
        
        <!-- 切换可见性 -->
        <UButton
          variant="ghost"
          color="neutral"
          size="xs"
          :icon="menu.isVisible ? 'i-lucide-eye' : 'i-lucide-eye-off'"
          @click="emit('toggleVisibility', menu)"
        />
        
        <!-- 编辑 -->
        <UButton
          variant="ghost"
          color="neutral"
          size="xs"
          icon="i-lucide-pencil"
          @click="emit('edit', menu)"
        />
        
        <!-- 删除 -->
        <UButton
          variant="ghost"
          color="error"
          size="xs"
          icon="i-lucide-trash-2"
          @click="emit('delete', menu)"
        />
      </div>
    </div>

    <!-- 子菜单 -->
    <template v-if="menu.children?.length && isExpanded">
      <NavMenuItem
        v-for="child in menu.children"
        :key="child.id"
        :menu="child"
        :level="level + 1"
        @edit="emit('edit', $event)"
        @delete="emit('delete', $event)"
        @add-child="emit('addChild', $event)"
        @toggle-visibility="emit('toggleVisibility', $event)"
      />
    </template>
  </div>
</template>
