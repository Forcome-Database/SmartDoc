<template>
  <div class="loading-state" :class="{ 'is-fullscreen': fullscreen }">
    <!-- Spinner加载动画 -->
    <div v-if="type === 'spinner'" class="spinner-container">
      <a-spin :size="size" :tip="tip">
        <template v-if="customIcon" #indicator>
          <LoadingOutlined style="font-size: 48px" spin />
        </template>
      </a-spin>
    </div>

    <!-- 骨架屏加载 -->
    <div v-else-if="type === 'skeleton'" class="skeleton-container">
      <!-- 卡片骨架屏 -->
      <a-skeleton
        v-if="skeletonType === 'card'"
        :active="true"
        :avatar="avatar"
        :paragraph="{ rows: rows }"
      />

      <!-- 列表骨架屏 -->
      <div v-else-if="skeletonType === 'list'" class="skeleton-list">
        <a-skeleton
          v-for="i in count"
          :key="i"
          :active="true"
          :avatar="avatar"
          :paragraph="{ rows: 2 }"
          class="skeleton-item"
        />
      </div>

      <!-- 表格骨架屏 -->
      <div v-else-if="skeletonType === 'table'" class="skeleton-table">
        <a-skeleton-button
          :active="true"
          :block="true"
          class="skeleton-header"
        />
        <a-skeleton
          v-for="i in count"
          :key="i"
          :active="true"
          :paragraph="{ rows: 1 }"
          class="skeleton-row"
        />
      </div>

      <!-- 表单骨架屏 -->
      <div v-else-if="skeletonType === 'form'" class="skeleton-form">
        <div v-for="i in count" :key="i" class="skeleton-form-item">
          <a-skeleton-input
            :active="true"
            size="small"
            class="skeleton-label"
          />
          <a-skeleton-input
            :active="true"
            :block="true"
            class="skeleton-input"
          />
        </div>
      </div>

      <!-- 自定义骨架屏 -->
      <div v-else class="skeleton-custom">
        <a-skeleton :active="true" :paragraph="{ rows: rows }" />
      </div>
    </div>

    <!-- 进度条加载 -->
    <div v-else-if="type === 'progress'" class="progress-container">
      <div class="progress-content">
        <LoadingOutlined class="progress-icon" spin />
        <p v-if="tip" class="progress-tip">{{ tip }}</p>
        <a-progress
          :percent="progress"
          :status="progressStatus"
          :show-info="showProgressInfo"
        />
      </div>
    </div>

    <!-- 点状加载 -->
    <div v-else-if="type === 'dots'" class="dots-container">
      <div class="dots-wrapper">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </div>
      <p v-if="tip" class="dots-tip">{{ tip }}</p>
    </div>

    <!-- 自定义加载内容 -->
    <div v-else-if="type === 'custom'" class="custom-container">
      <slot name="loading">
        <a-spin :size="size" :tip="tip" />
      </slot>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { LoadingOutlined } from '@ant-design/icons-vue'

// Props定义
const props = defineProps({
  // 加载类型：spinner(旋转器) | skeleton(骨架屏) | progress(进度条) | dots(点状) | custom(自定义)
  type: {
    type: String,
    default: 'spinner',
    validator: (value) => ['spinner', 'skeleton', 'progress', 'dots', 'custom'].includes(value)
  },
  // 加载提示文字
  tip: {
    type: String,
    default: ''
  },
  // Spinner大小
  size: {
    type: String,
    default: 'large',
    validator: (value) => ['small', 'default', 'large'].includes(value)
  },
  // 是否全屏显示
  fullscreen: {
    type: Boolean,
    default: false
  },
  // 是否使用自定义图标
  customIcon: {
    type: Boolean,
    default: false
  },
  // 骨架屏类型
  skeletonType: {
    type: String,
    default: 'card',
    validator: (value) => ['card', 'list', 'table', 'form', 'custom'].includes(value)
  },
  // 骨架屏是否显示头像
  avatar: {
    type: Boolean,
    default: false
  },
  // 骨架屏段落行数
  rows: {
    type: Number,
    default: 3
  },
  // 骨架屏重复次数（用于列表、表格等）
  count: {
    type: Number,
    default: 3
  },
  // 进度条百分比
  progress: {
    type: Number,
    default: 0
  },
  // 进度条状态
  progressStatus: {
    type: String,
    default: 'active',
    validator: (value) => ['active', 'success', 'exception', 'normal'].includes(value)
  },
  // 是否显示进度信息
  showProgressInfo: {
    type: Boolean,
    default: true
  }
})
</script>

<style scoped>
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  width: 100%;
}

.loading-state.is-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  z-index: 9999;
  min-height: 100vh;
}

/* Spinner样式 */
.spinner-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

/* 骨架屏样式 */
.skeleton-container {
  width: 100%;
  padding: 20px;
}

.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skeleton-item {
  padding: 16px;
  background-color: #fafafa;
  border-radius: 4px;
}

.skeleton-table {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skeleton-header {
  height: 40px;
  margin-bottom: 8px;
}

.skeleton-row {
  padding: 12px;
  background-color: #fafafa;
  border-radius: 4px;
}

.skeleton-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.skeleton-form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-label {
  width: 100px;
}

.skeleton-input {
  width: 100%;
}

.skeleton-custom {
  padding: 20px;
}

/* 进度条样式 */
.progress-container {
  width: 100%;
  max-width: 400px;
  padding: 20px;
}

.progress-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.progress-icon {
  font-size: 48px;
  color: #1890ff;
}

.progress-tip {
  font-size: 16px;
  color: #262626;
  margin: 0;
}

/* 点状加载样式 */
.dots-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.dots-wrapper {
  display: flex;
  gap: 8px;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #1890ff;
  animation: dot-pulse 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes dot-pulse {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.dots-tip {
  font-size: 14px;
  color: #8c8c8c;
  margin: 0;
}

/* 自定义容器样式 */
.custom-container {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .loading-state {
    min-height: 150px;
  }

  .progress-container {
    max-width: 300px;
  }

  .skeleton-container {
    padding: 12px;
  }
}
</style>
