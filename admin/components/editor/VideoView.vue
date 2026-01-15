<script setup lang="ts">
/**
 * 视频节点视图组件
 * 在编辑器中渲染视频播放器
 */
import { NodeViewWrapper, nodeViewProps } from '@tiptap/vue-3'
import { computed, ref } from 'vue'

const props = defineProps(nodeViewProps)

// 视频属性
const src = computed(() => props.node.attrs.src)
const title = computed(() => props.node.attrs.title)
const controls = computed(() => props.node.attrs.controls)
const autoplay = computed(() => props.node.attrs.autoplay)
const loop = computed(() => props.node.attrs.loop)
const muted = computed(() => props.node.attrs.muted)
const poster = computed(() => props.node.attrs.poster)
const uploading = computed(() => props.node.attrs.uploading)
const uploadProgress = computed(() => props.node.attrs.uploadProgress)

// 选中状态
const isSelected = computed(() => props.selected)

// 视频引用
const videoRef = ref<HTMLVideoElement | null>(null)

// 删除视频
const deleteVideo = () => {
  props.deleteNode()
}

// 更新属性
const updateAttribute = (key: string, value: any) => {
  props.updateAttributes({ [key]: value })
}

// 切换控制选项
const toggleControls = () => updateAttribute('controls', !controls.value)
const toggleAutoplay = () => updateAttribute('autoplay', !autoplay.value)
const toggleLoop = () => updateAttribute('loop', !loop.value)
const toggleMuted = () => updateAttribute('muted', !muted.value)
</script>

<template>
  <NodeViewWrapper
    class="video-wrapper"
    :class="{ 'is-selected': isSelected }"
    data-drag-handle
  >
    <!-- 上传中状态 -->
    <div v-if="uploading" class="video-uploading">
      <div class="upload-overlay">
        <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl" />
        <span class="text-sm mt-2">视频上传中...</span>
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: `${uploadProgress}%` }"
          />
        </div>
      </div>
      <video
        ref="videoRef"
        :src="src"
        class="video-preview opacity-50"
      />
    </div>

    <!-- 正常状态 -->
    <div v-else class="video-container">
      <video
        ref="videoRef"
        :src="src"
        :title="title"
        :controls="controls"
        :autoplay="autoplay"
        :loop="loop"
        :muted="muted"
        :poster="poster"
        class="video-player"
        preload="metadata"
      >
        您的浏览器不支持视频播放
      </video>

      <!-- 工具栏（选中时显示） -->
      <div v-if="isSelected" class="video-toolbar">
        <UButtonGroup size="xs">
          <UTooltip text="显示控制条">
            <UButton
              :variant="controls ? 'solid' : 'ghost'"
              icon="i-lucide-settings-2"
              @click="toggleControls"
            />
          </UTooltip>
          <UTooltip text="自动播放">
            <UButton
              :variant="autoplay ? 'solid' : 'ghost'"
              icon="i-lucide-play"
              @click="toggleAutoplay"
            />
          </UTooltip>
          <UTooltip text="循环播放">
            <UButton
              :variant="loop ? 'solid' : 'ghost'"
              icon="i-lucide-repeat"
              @click="toggleLoop"
            />
          </UTooltip>
          <UTooltip text="静音">
            <UButton
              :variant="muted ? 'solid' : 'ghost'"
              :icon="muted ? 'i-lucide-volume-x' : 'i-lucide-volume-2'"
              @click="toggleMuted"
            />
          </UTooltip>
          <UTooltip text="删除">
            <UButton
              variant="ghost"
              color="error"
              icon="i-lucide-trash-2"
              @click="deleteVideo"
            />
          </UTooltip>
        </UButtonGroup>
      </div>

      <!-- 视频标题 -->
      <div v-if="title" class="video-title">
        {{ title }}
      </div>
    </div>
  </NodeViewWrapper>
</template>

<style scoped>
.video-wrapper {
  @apply relative my-4 rounded-lg overflow-hidden;
}

.video-wrapper.is-selected {
  @apply ring-2 ring-primary-500 ring-offset-2;
}

.video-container {
  @apply relative;
}

.video-player {
  @apply w-full max-h-[500px] bg-black rounded-lg;
}

.video-uploading {
  @apply relative;
}

.video-preview {
  @apply w-full max-h-[500px] bg-black rounded-lg;
}

.upload-overlay {
  @apply absolute inset-0 flex flex-col items-center justify-center bg-black/50 text-white z-10;
}

.progress-bar {
  @apply w-48 h-1 bg-gray-600 rounded-full mt-2 overflow-hidden;
}

.progress-fill {
  @apply h-full bg-primary-500 transition-all duration-300;
}

.video-toolbar {
  @apply absolute top-2 right-2 z-10 bg-white/90 dark:bg-gray-800/90 rounded-lg shadow-lg p-1;
}

.video-title {
  @apply text-sm text-gray-500 dark:text-gray-400 mt-2 text-center;
}
</style>
