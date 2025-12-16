<template>
  <a-layout-header class="layout-header">
    <!-- Logo和系统名称 -->
    <div class="header-left">
      <div class="logo">
        <FileTextOutlined class="logo-icon" />
        <span class="logo-text">FORCOME文档中台</span>
      </div>
      <div class="logo-subtitle">智能文档处理中台</div>
    </div>

    <!-- 右侧用户信息 -->
    <div class="header-right">
      <!-- 用户信息下拉菜单 -->
      <a-dropdown placement="bottomRight">
        <div class="user-info">
          <a-avatar :size="32" class="user-avatar">
            <template #icon>
              <UserOutlined />
            </template>
          </a-avatar>
          <div class="user-details">
            <span class="username">{{ user?.username || '未登录' }}</span>
            <span class="user-role">{{ roleLabel }}</span>
          </div>
          <DownOutlined class="dropdown-icon" />
        </div>
        
        <template #overlay>
          <a-menu class="user-menu">
            <a-menu-item key="profile" @click="handleProfile">
              <UserOutlined />
              <span>个人信息</span>
            </a-menu-item>
            <a-menu-item key="api-keys" @click="handleApiKeys" v-if="canManageApiKeys">
              <KeyOutlined />
              <span>API密钥</span>
            </a-menu-item>
            <a-menu-divider />
            <a-menu-item key="logout" @click="handleLogout" class="logout-item">
              <LogoutOutlined />
              <span>退出登录</span>
            </a-menu-item>
          </a-menu>
        </template>
      </a-dropdown>
    </div>
  </a-layout-header>

  <!-- API密钥管理弹窗 -->
  <ApiKeyModal v-model:open="apiKeyModalVisible" />
</template>

<script setup>
/**
 * 顶部导航栏组件
 * 显示系统Logo、名称和用户信息
 * 提供用户下拉菜单（个人信息、API密钥管理、登出）
 */
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  UserOutlined,
  DownOutlined,
  LogoutOutlined,
  FileTextOutlined,
  KeyOutlined
} from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores'
import ApiKeyModal from '@/components/User/ApiKeyModal.vue'

const router = useRouter()
const authStore = useAuthStore()

// 用户信息
const user = computed(() => authStore.user)

// API密钥弹窗可见性
const apiKeyModalVisible = ref(false)

// 角色标签映射
const roleLabels = {
  admin: '超级管理员',
  architect: '规则架构师',
  auditor: '业务审核员',
  visitor: 'API访客'
}

const roleLabel = computed(() => {
  return user.value?.role ? roleLabels[user.value.role] : '未知角色'
})

// 是否可以管理API密钥
const canManageApiKeys = computed(() => {
  return user.value?.role === 'visitor' || user.value?.role === 'admin'
})

/**
 * 处理个人信息点击
 */
const handleProfile = () => {
  message.info('个人信息功能开发中')
}

/**
 * 处理API密钥管理点击
 */
const handleApiKeys = () => {
  apiKeyModalVisible.value = true
}

/**
 * 处理退出登录
 */
const handleLogout = () => {
  Modal.confirm({
    title: '确认退出',
    content: '确定要退出登录吗？',
    okText: '确定',
    cancelText: '取消',
    onOk: async () => {
      try {
        // 调用store的logout方法（内部会调用API并清除本地状态）
        await authStore.logout()
        message.success('已退出登录')
        router.push('/login')
      } catch (error) {
        console.error('退出登录失败:', error)
        message.error('退出登录失败，请重试')
      }
    }
  })
}
</script>

<style scoped>
.layout-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  z-index: 10;
  height: 64px;
  line-height: 64px;
}

/* Logo区域 */
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-icon {
  font-size: 24px;
  color: #1677ff;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #1677ff;
  white-space: nowrap;
}

.logo-subtitle {
  font-size: 12px;
  color: #8c8c8c;
  padding-left: 12px;
  border-left: 1px solid #e8e8e8;
  white-space: nowrap;
}

/* 用户信息区域 */
.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.3s;
}

.user-info:hover {
  background-color: #f5f5f5;
}

.user-avatar {
  background-color: #1677ff;
}

.user-details {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.4;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: #262626;
}

.user-role {
  font-size: 12px;
  color: #8c8c8c;
}

.dropdown-icon {
  font-size: 12px;
  color: #8c8c8c;
  transition: transform 0.3s;
}

.user-info:hover .dropdown-icon {
  transform: translateY(2px);
}

/* 下拉菜单样式 */
.user-menu {
  min-width: 160px;
  padding: 4px 0;
}

.user-menu :deep(.ant-dropdown-menu-item) {
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.logout-item {
  color: #ff4d4f;
}

.logout-item:hover {
  background-color: #fff1f0;
}

/* 响应式设计 - 平板 */
@media (max-width: 992px) {
  .logo-subtitle {
    display: none;
  }
  
  .user-details {
    display: none;
  }
}

/* 响应式设计 - 移动端 */
@media (max-width: 768px) {
  .layout-header {
    padding: 0 16px;
  }
  
  .logo-text {
    font-size: 16px;
  }
  
  .logo-icon {
    font-size: 20px;
  }
}
</style>
