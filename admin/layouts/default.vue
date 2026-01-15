<script setup lang="ts">
/**
 * 默认布局
 * 三栏布局：侧边栏导航 + 文件树（可选） + 主内容区
 * Mintlify 风格：简约大气，平滑过渡
 * 
 * Requirements: 8.1, 8.3, 8.4, 8.5, 8.7, 9.1
 */
import { useUserStore } from '~/stores/user'
import { getModifierKey } from '~/composables/useKeyboardShortcuts'

// 用户状态
const userStore = useUserStore()

// 初始化用户信息
onMounted(async () => {
  await userStore.fetchUser()
})

// 侧边栏状态
const isSidebarCollapsed = ref(false)
const isMobileSidebarOpen = ref(false)

// 搜索模态框状态
const isSearchOpen = ref(false)

// 快捷键帮助对话框状态
const isShortcutsHelpOpen = ref(false)

// 获取修饰键显示
const modifierKey = getModifierKey()

// 检测文件树插槽是否有内容
const slots = useSlots()
const hasFileTree = computed(() => !!slots['file-tree'])

// 全局快捷键注册
// Ctrl+K / Cmd+K 打开搜索（已在 SearchModal 中通过 defineShortcuts 实现）
// Shift+? 打开快捷键帮助（已在 KeyboardShortcutsHelp 中实现）

// 文件树宽度（可拖拽调整）
const fileTreeWidth = ref(280)
const isResizing = ref(false)
const minFileTreeWidth = 200
const maxFileTreeWidth = 400

// 响应式断点
const isMobile = ref(false)
const isTablet = ref(false)

// 监听窗口大小变化
const updateResponsiveState = () => {
  if (typeof window !== 'undefined') {
    const width = window.innerWidth
    isMobile.value = width < 768
    isTablet.value = width >= 768 && width < 1024
    
    if (!isMobile.value) {
      isMobileSidebarOpen.value = false
    }
  }
}

onMounted(() => {
  updateResponsiveState()
  window.addEventListener('resize', updateResponsiveState)
  
  // 从 localStorage 恢复文件树宽度
  const savedWidth = localStorage.getItem('fileTreeWidth')
  if (savedWidth) {
    fileTreeWidth.value = Math.min(Math.max(parseInt(savedWidth), minFileTreeWidth), maxFileTreeWidth)
  }
})

onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', updateResponsiveState)
  }
})

// 文件树拖拽调整
const startResize = (e: MouseEvent) => {
  isResizing.value = true
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

const handleResize = (e: MouseEvent) => {
  if (!isResizing.value) return
  const sidebarWidth = 64 // 侧边栏宽度
  const newWidth = e.clientX - sidebarWidth
  fileTreeWidth.value = Math.min(Math.max(newWidth, minFileTreeWidth), maxFileTreeWidth)
}

const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  
  // 保存到 localStorage
  localStorage.setItem('fileTreeWidth', fileTreeWidth.value.toString())
}

// 切换移动端侧边栏
const toggleMobileSidebar = () => {
  isMobileSidebarOpen.value = !isMobileSidebarOpen.value
}

// 提供给子组件的状态
provide('isMobile', isMobile)
provide('isTablet', isTablet)
provide('fileTreeWidth', fileTreeWidth)
provide('toggleMobileSidebar', toggleMobileSidebar)
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-950 transition-colors duration-200">
    <!-- 头部 -->
    <LayoutAppHeader 
      :is-mobile="isMobile" 
      @toggle-sidebar="toggleMobileSidebar"
      @open-search="isSearchOpen = true"
    />

    <!-- 搜索模态框 -->
    <SearchModal v-model:open="isSearchOpen" />

    <!-- 快捷键帮助对话框 -->
    <KeyboardShortcutsHelp v-model:open="isShortcutsHelpOpen" />

    <!-- 主体容器 -->
    <div class="pt-14 flex">
      <!-- 侧边栏导航 -->
      <LayoutAppSidebar 
        :is-mobile="isMobile"
        :is-mobile-open="isMobileSidebarOpen"
        @close="isMobileSidebarOpen = false"
        @open-shortcuts-help="isShortcutsHelpOpen = true"
      />

      <!-- 文件树区域（桌面端，仅当有内容时显示） -->
      <aside 
        v-if="!isMobile && hasFileTree"
        class="fixed left-16 top-14 bottom-0 border-r border-gray-200/80 dark:border-gray-800 bg-white/60 dark:bg-gray-900/60 backdrop-blur-md overflow-hidden flex flex-col transition-all duration-200"
        :style="{ width: `${fileTreeWidth}px` }"
      >
        <!-- 文件树内容插槽 -->
        <div class="flex-1 overflow-y-auto scrollbar-thin">
          <slot name="file-tree" />
        </div>
        
        <!-- 拖拽调整手柄 -->
        <div 
          class="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize transition-colors duration-150"
          :class="isResizing ? 'bg-primary-500' : 'hover:bg-primary-500/50'"
          @mousedown="startResize"
        />
      </aside>

      <!-- 主内容区 -->
      <main 
        class="flex-1 h-[calc(100vh-56px)] overflow-hidden transition-[margin] duration-200 ease-out"
        :class="isMobile ? 'ml-0' : 'ml-16'"
        :style="!isMobile && hasFileTree ? { marginLeft: `${64 + fileTreeWidth}px` } : {}"
      >
        <slot />
      </main>
    </div>

    <!-- 移动端遮罩 -->
    <Transition name="fade">
      <div 
        v-if="isMobile && isMobileSidebarOpen"
        class="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
        @click="isMobileSidebarOpen = false"
      />
    </Transition>
  </div>
</template>

<style scoped>
/* 淡入淡出动画 - 0.15s 符合 Requirements 8.7 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
