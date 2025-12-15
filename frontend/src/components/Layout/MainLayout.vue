<template>
  <a-layout class="main-layout">
    <!-- 顶部导航栏 -->
    <LayoutHeader />

    <a-layout class="layout-body">
      <!-- 侧边菜单 -->
      <LayoutSidebar />

      <!-- 内容区域 -->
      <a-layout-content class="content-wrapper">
        <div class="content">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
/**
 * 主布局组件
 * 包含顶部导航、侧边菜单和内容区域
 * 支持响应式设计
 */
import LayoutHeader from './Header.vue'
import LayoutSidebar from './Sidebar.vue'
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
  background: #f0f2f5;
}

.layout-body {
  min-height: calc(100vh - 64px);
}

.content-wrapper {
  background: #f0f2f5;
}

.content {
  margin: 24px;
  padding: 24px;
  background: #fff;
  min-height: calc(100vh - 64px - 48px);
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式设计 - 平板 */
@media (max-width: 992px) {
  .content {
    margin: 16px;
    padding: 16px;
  }
}

/* 响应式设计 - 移动端 */
@media (max-width: 768px) {
  .content {
    margin: 8px;
    padding: 12px;
    border-radius: 4px;
  }
}
</style>
