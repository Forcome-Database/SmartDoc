<template>
  <div class="file-uploader">
    <!-- 拖拽上传区域 -->
    <div
      class="upload-area"
      :class="{
        'is-dragover': isDragOver,
        'is-uploading': isUploading,
        'has-error': error
      }"
      @drop.prevent="handleDrop"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @click="triggerFileInput"
    >
      <input
        ref="fileInput"
        type="file"
        :accept="accept"
        :multiple="multiple"
        class="hidden-input"
        @change="handleFileSelect"
      />

      <!-- 上传图标和提示 -->
      <div v-if="!isUploading && !file" class="upload-prompt">
        <CloudUploadOutlined class="upload-icon" />
        <p class="upload-text">点击或拖拽文件到此区域上传</p>
        <p class="upload-hint">
          支持的文件类型：{{ acceptText }}
          <span v-if="maxSize">，最大 {{ formatSize(maxSize) }}</span>
        </p>
      </div>

      <!-- 上传进度 -->
      <div v-if="isUploading" class="upload-progress">
        <LoadingOutlined class="loading-icon" spin />
        <p class="progress-text">正在上传...</p>
        <a-progress
          :percent="uploadProgress"
          :show-info="true"
          status="active"
        />
      </div>

      <!-- 已选择文件 -->
      <div v-if="file && !isUploading" class="file-info">
        <FileOutlined class="file-icon" />
        <div class="file-details">
          <p class="file-name">{{ file.name }}</p>
          <p class="file-size">{{ formatSize(file.size) }}</p>
        </div>
        <CloseCircleOutlined
          class="remove-icon"
          @click.stop="removeFile"
        />
      </div>

      <!-- 错误提示 -->
      <div v-if="error" class="error-message">
        <ExclamationCircleOutlined class="error-icon" />
        <span>{{ error }}</span>
      </div>
    </div>

    <!-- 文件列表（多文件上传） -->
    <div v-if="multiple && fileList.length > 0" class="file-list">
      <div
        v-for="(item, index) in fileList"
        :key="index"
        class="file-list-item"
      >
        <FileOutlined class="file-icon" />
        <div class="file-details">
          <p class="file-name">{{ item.name }}</p>
          <p class="file-size">{{ formatSize(item.size) }}</p>
        </div>
        <a-progress
          v-if="item.progress < 100"
          :percent="item.progress"
          :show-info="false"
          size="small"
        />
        <CheckCircleOutlined
          v-else
          class="success-icon"
        />
        <CloseCircleOutlined
          class="remove-icon"
          @click="removeFileFromList(index)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  CloudUploadOutlined,
  LoadingOutlined,
  FileOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

// Props定义
const props = defineProps({
  // 接受的文件类型
  accept: {
    type: String,
    default: '.pdf,.jpg,.jpeg,.png'
  },
  // 最大文件大小（字节）
  maxSize: {
    type: Number,
    default: 20 * 1024 * 1024 // 20MB
  },
  // 是否支持多文件上传
  multiple: {
    type: Boolean,
    default: false
  },
  // 自动上传
  autoUpload: {
    type: Boolean,
    default: true
  }
})

// Emits定义
const emit = defineEmits(['upload', 'change', 'remove', 'error'])

// 响应式数据
const fileInput = ref(null)
const file = ref(null)
const fileList = ref([])
const isDragOver = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)
const error = ref('')

// 计算属性
const acceptText = computed(() => {
  return props.accept
    .split(',')
    .map(ext => ext.trim().toUpperCase())
    .join(', ')
})

// 格式化文件大小
const formatSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 验证文件
const validateFile = (file) => {
  // 验证文件类型
  const acceptTypes = props.accept.split(',').map(t => t.trim())
  const fileExt = '.' + file.name.split('.').pop().toLowerCase()
  const fileType = file.type

  const isValidType = acceptTypes.some(type => {
    if (type.startsWith('.')) {
      return fileExt === type.toLowerCase()
    }
    return fileType.startsWith(type.replace('*', ''))
  })

  if (!isValidType) {
    return `不支持的文件类型。请上传 ${acceptText.value} 格式的文件`
  }

  // 验证文件大小
  if (props.maxSize && file.size > props.maxSize) {
    return `文件大小超过限制。最大允许 ${formatSize(props.maxSize)}`
  }

  return null
}

// 触发文件选择
const triggerFileInput = () => {
  if (!isUploading.value) {
    fileInput.value?.click()
  }
}

// 处理文件选择
const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)
  if (files.length > 0) {
    processFiles(files)
  }
  // 清空input，允许重复选择同一文件
  event.target.value = ''
}

// 处理拖拽进入
const handleDragOver = () => {
  isDragOver.value = true
}

// 处理拖拽离开
const handleDragLeave = () => {
  isDragOver.value = false
}

// 处理文件拖放
const handleDrop = (event) => {
  isDragOver.value = false
  const files = Array.from(event.dataTransfer.files)
  if (files.length > 0) {
    processFiles(files)
  }
}

// 处理文件
const processFiles = (files) => {
  error.value = ''

  if (props.multiple) {
    // 多文件上传
    files.forEach(f => {
      const validationError = validateFile(f)
      if (validationError) {
        error.value = validationError
        emit('error', validationError)
        message.error(validationError)
        return
      }

      const fileItem = {
        file: f,
        name: f.name,
        size: f.size,
        progress: 0
      }

      fileList.value.push(fileItem)

      if (props.autoUpload) {
        uploadFile(fileItem)
      }
    })
  } else {
    // 单文件上传
    const f = files[0]
    const validationError = validateFile(f)
    if (validationError) {
      error.value = validationError
      emit('error', validationError)
      message.error(validationError)
      return
    }

    file.value = f
    emit('change', f)

    if (props.autoUpload) {
      uploadFile(f)
    }
  }
}

// 上传文件
const uploadFile = async (fileItem) => {
  isUploading.value = true
  uploadProgress.value = 0

  try {
    // 模拟上传进度
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
        if (props.multiple && fileItem.progress !== undefined) {
          fileItem.progress = uploadProgress.value
        }
      }
    }, 200)

    // 触发上传事件
    await emit('upload', props.multiple ? fileItem.file : fileItem)

    // 完成上传
    clearInterval(progressInterval)
    uploadProgress.value = 100
    if (props.multiple && fileItem.progress !== undefined) {
      fileItem.progress = 100
    }

    message.success('文件上传成功')
  } catch (err) {
    error.value = err.message || '上传失败'
    emit('error', error.value)
    message.error(error.value)
  } finally {
    isUploading.value = false
  }
}

// 移除文件
const removeFile = () => {
  file.value = null
  error.value = ''
  uploadProgress.value = 0
  emit('remove')
}

// 从列表中移除文件
const removeFileFromList = (index) => {
  fileList.value.splice(index, 1)
  emit('remove', index)
}

// 手动上传（当autoUpload为false时）
const upload = () => {
  if (props.multiple) {
    fileList.value.forEach(item => {
      if (item.progress === 0) {
        uploadFile(item)
      }
    })
  } else if (file.value) {
    uploadFile(file.value)
  }
}

// 清空所有文件
const clear = () => {
  file.value = null
  fileList.value = []
  error.value = ''
  uploadProgress.value = 0
  isUploading.value = false
}

// 暴露方法给父组件
defineExpose({
  upload,
  clear
})
</script>

<style scoped>
.file-uploader {
  width: 100%;
}

.upload-area {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background-color: #fafafa;
}

.upload-area:hover {
  border-color: #1890ff;
  background-color: #f0f7ff;
}

.upload-area.is-dragover {
  border-color: #1890ff;
  background-color: #e6f7ff;
}

.upload-area.is-uploading {
  cursor: not-allowed;
  opacity: 0.8;
}

.upload-area.has-error {
  border-color: #ff4d4f;
  background-color: #fff2f0;
}

.hidden-input {
  display: none;
}

.upload-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.upload-icon {
  font-size: 48px;
  color: #1890ff;
}

.upload-text {
  font-size: 16px;
  color: #262626;
  margin: 0;
}

.upload-hint {
  font-size: 14px;
  color: #8c8c8c;
  margin: 0;
}

.upload-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.loading-icon {
  font-size: 48px;
  color: #1890ff;
}

.progress-text {
  font-size: 16px;
  color: #262626;
  margin: 0;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background-color: #fff;
  border-radius: 4px;
}

.file-icon {
  font-size: 32px;
  color: #1890ff;
}

.file-details {
  flex: 1;
  text-align: left;
}

.file-name {
  font-size: 14px;
  color: #262626;
  margin: 0 0 4px 0;
  word-break: break-all;
}

.file-size {
  font-size: 12px;
  color: #8c8c8c;
  margin: 0;
}

.remove-icon {
  font-size: 20px;
  color: #ff4d4f;
  cursor: pointer;
  transition: color 0.3s;
}

.remove-icon:hover {
  color: #ff7875;
}

.error-message {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #ff4d4f;
  font-size: 14px;
  margin-top: 12px;
}

.error-icon {
  font-size: 16px;
}

.file-list {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-list-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background-color: #fafafa;
  border-radius: 4px;
  border: 1px solid #d9d9d9;
}

.success-icon {
  font-size: 20px;
  color: #52c41a;
}
</style>
