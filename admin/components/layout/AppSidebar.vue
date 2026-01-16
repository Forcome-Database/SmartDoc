<script setup lang="ts">
/**
 * 应用侧边栏组件
 * 包含导航菜单、新建文档/设置入口
 * 
 * Requirements: 8.1, 8.5
 */
import { useUserStore } from '~/stores/user'

const props = defineProps<{
  isMobile: boolean
  isMobileOpen: boolean
}>()

const emit = defineEmits<{
  close: []
  openShortcutsHelp: []
}>()

const route = useRoute()
const userStore = useUserStore()

// 导航菜单项
const navItems = computed(() => [
  {
    label: '首页',
    icon: 'i-lucide-home',
    to: '/',
  },
  {
    label: '文档',
    icon: 'i-lucide-files',
    to: '/content',
  },
  {
    label: '导航菜单',
    icon: 'i-lucide-menu-square',
    to: '/nav-menus',
  },
])

// 设置菜单项
const settingsItems = computed(() => {
  return [
    {
      label: '语言管理',
      icon: 'i-lucide-languages',
      to: '/settings/locales',
    },
    {
      label: '用户管理',
      icon: 'i-lucide-users',
      to: '/settings/users',
      show: userStore.isAdmin,
    },
  ]
})

// 检查是否为当前路由
const isActive = (path: string) => {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}

// 处理导航点击（移动端关闭侧边栏）
const handleNavClick = () => {
  if (props.isMobile) {
    emit('close')
  }
}
</script>

<template>
  <!-- 桌面端侧边栏 -->
  <aside 
    v-if="!isMobile"
    class="fixed left-0 top-14 bottom-0 w-16 border-r border-gray-200/80 dark:border-gray-800 bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm flex flex-col"
  >
    <!-- 主导航 -->
    <nav class="flex-1 p-2 space-y-1">
      <UTooltip 
        v-for="item in navItems" 
        :key="item.to"
        :text="item.label"
        :popper="{ placement: 'right' }"
      >
        <NuxtLink
          :to="item.to"
          class="flex items-center justify-center w-12 h-12 rounded-xl transition-all duration-200"
          :class="isActive(item.to) 
            ? 'bg-primary-100 dark:bg-primary-500/20 text-primary-600 dark:text-primary-400 shadow-sm' 
            : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white'"
        >
          <UIcon :name="item.icon" class="w-5 h-5" />
        </NuxtLink>
      </UTooltip>
    </nav>

    <!-- 底部操作 -->
    <div class="p-2 space-y-1 border-t border-gray-200/80 dark:border-gray-800">
      <!-- 新建文档 -->
      <UTooltip text="新建文档" :popper="{ placement: 'right' }">
        <UButton
          variant="ghost"
          color="neutral"
          class="w-12 h-12 rounded-xl flex items-center justify-center"
          icon="i-lucide-plus"
        />
      </UTooltip>

      <!-- 设置 -->
      <UDropdownMenu 
        :items="[[
          ...settingsItems.filter(item => item.show !== false).map(item => ({
            label: item.label,
            icon: item.icon,
            onSelect: () => navigateTo(item.to),
          }))
        ]]"
        :popper="{ placement: 'right-start' }"
      >
        <UButton
          variant="ghost"
          color="neutral"
          class="w-12 h-12 rounded-xl flex items-center justify-center"
          :class="route.path.startsWith('/settings') 
            ? 'bg-primary-100 dark:bg-primary-500/20 text-primary-600 dark:text-primary-400' 
            : ''"
          icon="i-lucide-settings"
        />
      </UDropdownMenu>

      <!-- 快捷键帮助 -->
      <UTooltip text="快捷键 (?)" :popper="{ placement: 'right' }">
        <UButton
          variant="ghost"
          color="neutral"
          class="w-12 h-12 rounded-xl flex items-center justify-center"
          icon="i-lucide-keyboard"
          @click="emit('openShortcutsHelp')"
        />
      </UTooltip>
    </div>
  </aside>

  <!-- 移动端侧边栏 -->
  <Transition name="slide">
    <aside 
      v-if="isMobile && isMobileOpen"
      class="fixed left-0 top-14 bottom-0 w-72 border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 z-50 flex flex-col shadow-xl"
    >
      <!-- 主导航 -->
      <nav class="flex-1 p-4 space-y-1">
        <NuxtLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200"
          :class="isActive(item.to) 
            ? 'bg-primary-100 dark:bg-primary-500/20 text-primary-600 dark:text-primary-400' 
            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white'"
          @click="handleNavClick"
        >
          <UIcon :name="item.icon" class="w-5 h-5" />
          <span class="text-sm font-medium">{{ item.label }}</span>
        </NuxtLink>
      </nav>

      <!-- 设置区域 -->
      <div class="p-4 space-y-1 border-t border-gray-200 dark:border-gray-800">
        <p class="px-4 py-2 text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
          设置
        </p>
        <NuxtLink
          v-for="item in settingsItems.filter(i => i.show !== false)"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200"
          :class="isActive(item.to) 
            ? 'bg-primary-100 dark:bg-primary-500/20 text-primary-600 dark:text-primary-400' 
            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white'"
          @click="handleNavClick"
        >
          <UIcon :name="item.icon" class="w-5 h-5" />
          <span class="text-sm font-medium">{{ item.label }}</span>
        </NuxtLink>
      </div>

      <!-- 新建文档按钮 -->
      <div class="p-4 border-t border-gray-200 dark:border-gray-800">
        <UButton
          block
          color="primary"
          size="lg"
          class="shadow-lg shadow-primary-500/25"
          @click="handleNavClick"
        >
          <UIcon name="i-lucide-plus" class="w-4 h-4 mr-2" />
          新建文档
        </UButton>
        
        <!-- 快捷键帮助按钮 -->
        <UButton
          block
          variant="ghost"
          color="neutral"
          size="sm"
          class="mt-2"
          @click="emit('openShortcutsHelp'); handleNavClick()"
        >
          <UIcon name="i-lucide-keyboard" class="w-4 h-4 mr-2" />
          快捷键帮助
        </UButton>
      </div>
    </aside>
  </Transition>
</template>

<style scoped>
/* 滑入滑出动画 - 0.2s 符合 Requirements 8.7 */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.2s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(-100%);
}
</style>
