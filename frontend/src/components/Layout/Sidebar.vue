<template>
  <a-layout-sider
    v-model:collapsed="collapsed"
    :trigger="null"
    collapsible
    :width="220"
    :collapsed-width="80"
    class="layout-sider"
    :breakpoint="breakpoint"
    @breakpoint="onBreakpoint"
  >
    <!-- 折叠按钮 -->
    <div class="collapse-trigger" @click="toggleCollapsed">
      <MenuUnfoldOutlined v-if="collapsed" />
      <MenuFoldOutlined v-else />
    </div>

    <!-- 菜单 -->
    <a-menu
      v-model:selectedKeys="selectedKeys"
      v-model:openKeys="openKeys"
      mode="inline"
      theme="dark"
      :inline-collapsed="collapsed"
      class="sidebar-menu"
    >
      <template v-for="item in visibleMenuItems" :key="item.key">
        <!-- 单级菜单项 -->
        <a-menu-item
          v-if="!item.children"
          :key="item.key"
          @click="handleMenuClick(item)"
        >
          <component :is="item.icon" v-if="item.icon" />
          <span>{{ item.label }}</span>
        </a-menu-item>

        <!-- 多级菜单项 -->
        <a-sub-menu v-else :key="item.key">
          <template #icon>
            <component :is="item.icon" v-if="item.icon" />
          </template>
          <template #title>{{ item.label }}</template>
          <a-menu-item
            v-for="child in item.children"
            :key="child.key"
            @click="handleMenuClick(child)"
          >
            <component :is="child.icon" v-if="child.icon" />
            <span>{{ child.label }}</span>
          </a-menu-item>
        </a-sub-menu>
      </template>
    </a-menu>
  </a-layout-sider>
</template>

<script setup>
/**
 * 侧边菜单组件
 * 根据用户角色显示菜单项
 * 支持菜单折叠/展开
 * 高亮当前激活菜单
 */
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  DashboardOutlined,
  FileTextOutlined,
  UnorderedListOutlined,
  AuditOutlined,
  ApiOutlined,
  TeamOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  CloudUploadOutlined
} from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 折叠状态
const collapsed = ref(false)
const breakpoint = ref('lg')

// 选中的菜单项
const selectedKeys = ref([route.path])
const openKeys = ref([])

// 用户角色
const userRole = computed(() => authStore.user?.role || 'visitor')

/**
 * 菜单配置
 * 根据角色权限过滤菜单项
 */
const menuConfig = [
  {
    key: '/dashboard',
    label: '仪表盘',
    icon: DashboardOutlined,
    roles: ['admin', 'architect', 'auditor', 'visitor']
  },
  {
    key: '/rules',
    label: '规则管理',
    icon: FileTextOutlined
    // 临时移除角色限制用于测试
    // roles: ['admin', 'architect']
  },
  {
    key: '/pipelines',
    label: '数据管道',
    icon: ApiOutlined
    // 临时移除角色限制用于测试
    // roles: ['admin', 'architect']
  },
  {
    key: '/upload',
    label: '文档上传',
    icon: CloudUploadOutlined,
    roles: ['admin', 'architect', 'auditor', 'visitor']
  },
  {
    key: '/tasks',
    label: '任务列表',
    icon: UnorderedListOutlined,
    roles: ['admin', 'architect', 'auditor', 'visitor']
  },
  {
    key: '/audit',
    label: '人工审核',
    icon: AuditOutlined,
    roles: ['admin', 'auditor']
  },
  {
    key: '/webhooks',
    label: 'Webhook配置',
    icon: ApiOutlined
    // 临时移除角色限制用于测试
    // roles: ['admin']
  },
  {
    key: '/users',
    label: '用户管理',
    icon: TeamOutlined,
    roles: ['admin']
  },
  {
    key: '/settings',
    label: '系统设置',
    icon: SettingOutlined,
    roles: ['admin']
  }
]

/**
 * 根据用户角色过滤可见的菜单项
 */
const visibleMenuItems = computed(() => {
  return menuConfig.filter(item => {
    // 如果没有定义roles，默认所有角色可见
    if (!item.roles || item.roles.length === 0) {
      return true
    }
    // 检查当前用户角色是否在允许的角色列表中
    return item.roles.includes(userRole.value)
  })
})

/**
 * 监听路由变化，更新选中的菜单项
 */
watch(
  () => route.path,
  (newPath) => {
    // 更新选中的菜单项
    selectedKeys.value = [newPath]
    
    // 如果是子路由，需要展开父菜单
    const parentPath = '/' + newPath.split('/')[1]
    if (parentPath !== newPath && !collapsed.value) {
      openKeys.value = [parentPath]
    }
  },
  { immediate: true }
)

/**
 * 切换折叠状态
 */
const toggleCollapsed = () => {
  collapsed.value = !collapsed.value
  
  // 折叠时关闭所有子菜单
  if (collapsed.value) {
    openKeys.value = []
  }
}

/**
 * 响应式断点变化
 */
const onBreakpoint = (broken) => {
  if (broken) {
    collapsed.value = true
  }
}

/**
 * 处理菜单点击
 */
const handleMenuClick = (item) => {
  router.push(item.key)
}
</script>

<style scoped>
.layout-sider {
  background: #001529;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  position: relative;
  overflow: hidden;
}

/* 折叠按钮 */
.collapse-trigger {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.05);
  transition: all 0.3s;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.collapse-trigger:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.collapse-trigger :deep(.anticon) {
  font-size: 18px;
}

/* 菜单样式 */
.sidebar-menu {
  border-right: none;
  height: calc(100vh - 64px - 48px);
  overflow-y: auto;
  overflow-x: hidden;
}

/* 自定义滚动条 */
.sidebar-menu::-webkit-scrollbar {
  width: 6px;
}

.sidebar-menu::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

.sidebar-menu::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.sidebar-menu::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* 菜单项样式优化 */
.sidebar-menu :deep(.ant-menu-item),
.sidebar-menu :deep(.ant-menu-submenu-title) {
  display: flex;
  align-items: center;
  height: 48px;
  line-height: 48px;
  margin: 4px 8px;
  border-radius: 4px;
  transition: all 0.3s;
}

.sidebar-menu :deep(.ant-menu-item:hover),
.sidebar-menu :deep(.ant-menu-submenu-title:hover) {
  background: rgba(255, 255, 255, 0.1);
}

.sidebar-menu :deep(.ant-menu-item-selected) {
  background: #1677ff !important;
}

.sidebar-menu :deep(.ant-menu-item .anticon),
.sidebar-menu :deep(.ant-menu-submenu-title .anticon) {
  font-size: 16px;
  margin-right: 10px;
}

/* 折叠状态下的样式 */
.layout-sider.ant-layout-sider-collapsed .sidebar-menu :deep(.ant-menu-item),
.layout-sider.ant-layout-sider-collapsed .sidebar-menu :deep(.ant-menu-submenu-title) {
  padding: 0 calc(50% - 16px / 2);
}

/* 响应式设计 - 移动端 */
@media (max-width: 768px) {
  .layout-sider {
    position: fixed;
    left: 0;
    top: 64px;
    bottom: 0;
    z-index: 999;
  }
  
  .layout-sider.ant-layout-sider-collapsed {
    left: -80px;
  }
}
</style>
