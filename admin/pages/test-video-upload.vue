<script setup lang="ts">
/**
 * 视频上传测试页面
 * 测试 MinIO 视频上传功能
 */
import { useVideoUpload } from '~/composables/useUpload'

definePageMeta({
  layout: 'default',
  middleware: ['dev-only', 'auth'],
})

// 视频上传
const videoUpload = useVideoUpload({
  onSuccess: (result) => {
    console.log('视频上传成功:', result)
  },
  onError: (error) => {
    console.error('视频上传失败:', error)
  },
  onProgress: (progress) => {
    console.log('上传进度:', progress)
  },
})

// 上传的视频列表
const uploadedVideos = ref<Array<{
  url: string
  filename: string
  size: number
  mimeType: string
}>>([])

// 处理文件选择
const handleFileSelect = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  
  if (file) {
    const result = await videoUpload.upload(file)
    if (result) {
      uploadedVideos.value.push({
        url: result.url,
        filename: result.filename,
        size: result.size,
        mimeType: result.mimeType,
      })
    }
  }
}

// 打开文件选择器
const openPicker = async () => {
  const result = await videoUpload.openPicker()
  if (result) {
    uploadedVideos.value.push({
      url: result.url,
      filename: result.filename,
      size: result.size,
      mimeType: result.mimeType,
    })
  }
}

// 格式化文件大小
const formatSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}
</script>

<template>
  <div class="container mx-auto p-8 max-w-4xl">
    <div class="mb-8">
      <h1 class="text-3xl font-bold mb-2">视频上传测试</h1>
      <p class="text-gray-600 dark:text-gray-400">
        测试 MinIO 视频上传功能，支持 MP4、WebM、OGG、MOV 格式，最大 100MB
      </p>
    </div>

    <!-- 上传区域 -->
    <UCard class="mb-8">
      <template #header>
        <h2 class="text-xl font-semibold">上传视频</h2>
      </template>

      <div class="space-y-4">
        <!-- 方式 1: 使用 input -->
        <div>
          <label class="block text-sm font-medium mb-2">方式 1: 文件输入</label>
          <input
            type="file"
            accept="video/mp4,video/webm,video/ogg,video/quicktime"
            class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 dark:file:bg-primary-900 dark:file:text-primary-300"
            @change="handleFileSelect"
          />
        </div>

        <!-- 方式 2: 使用按钮 -->
        <div>
          <label class="block text-sm font-medium mb-2">方式 2: 按钮选择</label>
          <UButton
            icon="i-lucide-upload"
            :loading="videoUpload.uploading.value"
            @click="openPicker"
          >
            选择视频文件
          </UButton>
        </div>

        <!-- 上传进度 -->
        <div v-if="videoUpload.uploading.value" class="space-y-2">
          <div class="flex items-center justify-between text-sm">
            <span>上传中...</span>
            <span>{{ videoUpload.progress.value }}%</span>
          </div>
          <UProgress :value="videoUpload.progress.value" />
        </div>

        <!-- 错误信息 -->
        <UAlert
          v-if="videoUpload.error.value"
          color="error"
          icon="i-lucide-alert-circle"
          :title="videoUpload.error.value"
        />
      </div>
    </UCard>

    <!-- 已上传的视频列表 -->
    <UCard v-if="uploadedVideos.length > 0">
      <template #header>
        <h2 class="text-xl font-semibold">已上传的视频 ({{ uploadedVideos.length }})</h2>
      </template>

      <div class="space-y-6">
        <div
          v-for="(video, index) in uploadedVideos"
          :key="index"
          class="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
        >
          <!-- 视频信息 -->
          <div class="mb-3 space-y-1">
            <div class="flex items-center justify-between">
              <span class="font-medium">{{ video.filename }}</span>
              <UBadge color="primary">{{ video.mimeType }}</UBadge>
            </div>
            <div class="text-sm text-gray-500">
              大小: {{ formatSize(video.size) }}
            </div>
            <div class="text-xs text-gray-400 break-all">
              URL: {{ video.url }}
            </div>
          </div>

          <!-- 视频播放器 -->
          <video
            :src="video.url"
            controls
            class="w-full max-h-[400px] bg-black rounded-lg"
            preload="metadata"
          >
            您的浏览器不支持视频播放
          </video>
        </div>
      </div>
    </UCard>

    <!-- 支持的格式说明 -->
    <UCard class="mt-8">
      <template #header>
        <h2 class="text-xl font-semibold">支持的格式</h2>
      </template>

      <div class="space-y-4">
        <div>
          <h3 class="font-medium mb-2">视频格式</h3>
          <div class="flex flex-wrap gap-2">
            <UBadge color="primary">MP4</UBadge>
            <UBadge color="primary">WebM</UBadge>
            <UBadge color="primary">OGG</UBadge>
            <UBadge color="primary">MOV</UBadge>
          </div>
        </div>

        <div>
          <h3 class="font-medium mb-2">MIME 类型</h3>
          <div class="flex flex-wrap gap-2">
            <UBadge variant="subtle">video/mp4</UBadge>
            <UBadge variant="subtle">video/webm</UBadge>
            <UBadge variant="subtle">video/ogg</UBadge>
            <UBadge variant="subtle">video/quicktime</UBadge>
          </div>
        </div>

        <div>
          <h3 class="font-medium mb-2">限制</h3>
          <ul class="list-disc list-inside text-sm text-gray-600 dark:text-gray-400 space-y-1">
            <li>最大文件大小: 100 MB</li>
            <li>支持拖拽上传（在编辑器中）</li>
            <li>自动生成预览图</li>
            <li>支持播放控制（播放、暂停、音量等）</li>
          </ul>
        </div>
      </div>
    </UCard>
  </div>
</template>
