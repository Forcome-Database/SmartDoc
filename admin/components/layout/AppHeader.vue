<script setup lang="ts">
/**
 * 应用头部组件
 * 包含 Logo、面包屑导航、同步状态、用户菜单
 * 
 * Requirements: 8.5, 8.6, 5.5, 9.1
 */
import { useUserStore } from '~/stores/user'
import { getModifierKey } from '~/composables/useKeyboardShortcuts'

const props = defineProps<{
  isMobile: boolean
}>()

const emit = defineEmits<{
  toggleSidebar: []
  openSearch: []
}>()

const userStore = useUserStore()
const route = useRoute()

// 获取修饰键显示
const modifierKey = getModifierKey()

// 面包屑导航
const breadcrumbs = computed(() => {
  const paths = route.path.split('/').filter(Boolean)
  const items: { label: string; to?: string }[] = [
    { label: '首页', to: '/' }
  ]
  
  let currentPath = ''
  const pathLabels: Record<string, string> = {
    documents: '文档',
    categories: '栏目',
    settings: '设置',
    locales: '语言',
    users: '用户',
    'nav-menus': '导航菜单',
  }
  
  paths.forEach((path, index) => {
    currentPath += `/${path}`
    const label = pathLabels[path] || path
    
    // 最后一个不需要链接
    if (index === paths.length - 1) {
      items.push({ label })
    } else {
      items.push({ label, to: currentPath })
    }
  })
  
  return items
})

// 用户菜单项
const userMenuItems = computed(() => [
  [
    {
      label: userStore.displayName,
      slot: 'account',
      disabled: true,
    },
  ],
  [
    {
      label: '个人设置',
      icon: 'i-lucide-user',
      click: () => navigateTo('/settings/profile'),
    },
  ],
  [
    {
      label: '退出登录',
      icon: 'i-lucide-log-out',
      click: () => userStore.logout(),
    },
  ],
])

// 处理登出
const handleLogout = async () => {
  await userStore.logout()
}
</script>

<template>
  <header class="fixed top-0 left-0 right-0 h-14 border-b border-gray-200/80 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md z-50">
    <div class="flex items-center justify-between h-full px-4">
      <!-- 左侧：Logo 和面包屑 -->
      <div class="flex items-center gap-4">
        <!-- 移动端菜单按钮 -->
        <UButton
          v-if="isMobile"
          variant="ghost"
          color="neutral"
          size="sm"
          icon="i-lucide-menu"
          @click="emit('toggleSidebar')"
        />
        
        <!-- Logo -->
        <NuxtLink to="/" class="flex items-center gap-2.5 font-semibold text-gray-900 dark:text-white">
          <div class="w-8 h-8 bg-gradient-to-br from-primary-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-sm shadow-primary-500/30">
            <UIcon name="i-lucide-book-open" class="w-4 h-4 text-white" />
          </div>
          <span v-if="!isMobile" class="text-sm font-semibold">FORCOME 知识库</span>
        </NuxtLink>

        <!-- 面包屑导航（桌面端） -->
        <nav v-if="!isMobile && breadcrumbs.length > 1" class="flex items-center text-sm">
          <template v-for="(item, index) in breadcrumbs" :key="index">
            <UIcon 
              v-if="index > 0" 
              name="i-lucide-chevron-right" 
              class="w-4 h-4 mx-1.5 text-gray-300 dark:text-gray-600" 
            />
            <NuxtLink
              v-if="item.to"
              :to="item.to"
              class="text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
            >
              {{ item.label }}
            </NuxtLink>
            <span v-else class="text-gray-900 dark:text-white font-medium">
              {{ item.label }}
            </span>
          </template>
        </nav>
      </div>

      <!-- 右侧：同步状态、搜索、用户菜单 -->
      <div class="flex items-center gap-1">
        <!-- Git 同步状态 -->
        <LayoutSyncStatusIndicator />

        <!-- 搜索按钮 -->
        <UTooltip :text="`搜索 (${modifierKey}K)`">
          <UButton
            variant="ghost"
            color="neutral"
            size="sm"
            class="rounded-lg gap-2"
            @click="emit('openSearch')"
          >
            <UIcon name="i-lucide-search" class="w-4 h-4" />
            <span v-if="!isMobile" class="text-xs text-gray-400 dark:text-gray-500">
              {{ modifierKey }}K
            </span>
          </UButton>
        </UTooltip>

        <!-- 主题切换 -->
        <LayoutThemeToggle />

        <!-- 用户菜单 -->
        <UDropdownMenu :items="userMenuItems">
          <UButton variant="ghost" color="neutral" size="sm" class="p-1 rounded-lg">
            <UAvatar
              :src="userStore.avatarUrl"
              :alt="userStore.displayName"
              size="xs"
              class="ring-2 ring-gray-200 dark:ring-gray-700"
            >
              <template #fallback>
                <span class="text-xs font-medium">{{ userStore.displayName?.charAt(0) || 'U' }}</span>
              </template>
            </UAvatar>
          </UButton>
          
          <template #account>
            <div class="flex items-center gap-3 px-3 py-2">
              <UAvatar
                :src="userStore.avatarUrl"
                :alt="userStore.displayName"
                size="sm"
              >
                <template #fallback>
                  <span class="text-sm font-medium">{{ userStore.displayName?.charAt(0) || 'U' }}</span>
                </template>
              </UAvatar>
              <div class="flex flex-col">
                <span class="text-sm font-medium text-gray-900 dark:text-white">
                  {{ userStore.displayName }}
                </span>
                <span class="text-xs text-gray-500 dark:text-gray-400">
                  {{ userStore.user?.role === 'admin' ? '管理员' : '编辑者' }}
                </span>
              </div>
            </div>
          </template>
        </UDropdownMenu>
      </div>
    </div>
  </header>
</template>
