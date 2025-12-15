# 公共组件使用文档

本目录包含系统中可复用的公共组件，用于提供统一的用户体验和交互模式。

## 组件列表

### 1. FileUploader - 文件上传器

支持拖拽上传、进度显示、文件验证的文件上传组件。

#### 功能特性

- ✅ 支持点击上传和拖拽上传
- ✅ 实时显示上传进度
- ✅ 文件类型和大小验证
- ✅ 支持单文件和多文件上传
- ✅ 自动上传或手动上传
- ✅ 文件列表管理

#### 基础用法

```vue
<template>
  <FileUploader
    accept=".pdf,.jpg,.jpeg,.png"
    :max-size="20 * 1024 * 1024"
    @upload="handleUpload"
    @error="handleError"
  />
</template>

<script setup>
import FileUploader from '@/components/Common/FileUploader.vue'

const handleUpload = async (file) => {
  // 处理文件上传
  const formData = new FormData()
  formData.append('file', file)
  
  await api.upload(formData)
}

const handleError = (error) => {
  console.error('上传错误:', error)
}
</script>
```

#### Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| accept | 接受的文件类型 | string | '.pdf,.jpg,.jpeg,.png' |
| maxSize | 最大文件大小（字节） | number | 20971520 (20MB) |
| multiple | 是否支持多文件上传 | boolean | false |
| autoUpload | 是否自动上传 | boolean | true |

#### Events

| 事件名 | 说明 | 回调参数 |
|--------|------|----------|
| upload | 文件上传事件 | (file: File) |
| change | 文件选择变化 | (file: File) |
| remove | 文件移除 | (index?: number) |
| error | 错误事件 | (error: string) |

#### 方法

| 方法名 | 说明 | 参数 |
|--------|------|------|
| upload | 手动触发上传 | - |
| clear | 清空所有文件 | - |

#### 多文件上传示例

```vue
<template>
  <FileUploader
    :multiple="true"
    :auto-upload="false"
    ref="uploaderRef"
    @upload="handleUpload"
  />
  <a-button @click="uploadAll">上传所有文件</a-button>
</template>

<script setup>
import { ref } from 'vue'
import FileUploader from '@/components/Common/FileUploader.vue'

const uploaderRef = ref(null)

const handleUpload = async (file) => {
  // 处理单个文件上传
}

const uploadAll = () => {
  uploaderRef.value?.upload()
}
</script>
```

---

### 2. LoadingState - 加载状态组件

提供多种加载状态展示方式的组件，包括Spinner、骨架屏、进度条等。

#### 功能特性

- ✅ 多种加载样式：Spinner、骨架屏、进度条、点状动画
- ✅ 支持全屏加载遮罩
- ✅ 多种骨架屏类型：卡片、列表、表格、表单
- ✅ 自定义加载内容
- ✅ 响应式设计

#### 基础用法 - Spinner

```vue
<template>
  <LoadingState
    type="spinner"
    tip="加载中..."
    size="large"
  />
</template>

<script setup>
import LoadingState from '@/components/Common/LoadingState.vue'
</script>
```

#### 骨架屏用法

```vue
<template>
  <!-- 卡片骨架屏 -->
  <LoadingState
    type="skeleton"
    skeleton-type="card"
    :avatar="true"
    :rows="3"
  />

  <!-- 列表骨架屏 -->
  <LoadingState
    type="skeleton"
    skeleton-type="list"
    :count="5"
  />

  <!-- 表格骨架屏 -->
  <LoadingState
    type="skeleton"
    skeleton-type="table"
    :count="10"
  />

  <!-- 表单骨架屏 -->
  <LoadingState
    type="skeleton"
    skeleton-type="form"
    :count="4"
  />
</template>
```

#### 进度条用法

```vue
<template>
  <LoadingState
    type="progress"
    tip="正在处理..."
    :progress="uploadProgress"
    progress-status="active"
  />
</template>

<script setup>
import { ref } from 'vue'
import LoadingState from '@/components/Common/LoadingState.vue'

const uploadProgress = ref(0)

// 模拟进度更新
setInterval(() => {
  if (uploadProgress.value < 100) {
    uploadProgress.value += 10
  }
}, 500)
</script>
```

#### 全屏加载

```vue
<template>
  <LoadingState
    type="spinner"
    tip="加载中，请稍候..."
    :fullscreen="true"
  />
</template>
```

#### Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| type | 加载类型 | 'spinner' \| 'skeleton' \| 'progress' \| 'dots' \| 'custom' | 'spinner' |
| tip | 加载提示文字 | string | '' |
| size | Spinner大小 | 'small' \| 'default' \| 'large' | 'large' |
| fullscreen | 是否全屏显示 | boolean | false |
| customIcon | 是否使用自定义图标 | boolean | false |
| skeletonType | 骨架屏类型 | 'card' \| 'list' \| 'table' \| 'form' \| 'custom' | 'card' |
| avatar | 骨架屏是否显示头像 | boolean | false |
| rows | 骨架屏段落行数 | number | 3 |
| count | 骨架屏重复次数 | number | 3 |
| progress | 进度条百分比 | number | 0 |
| progressStatus | 进度条状态 | 'active' \| 'success' \| 'exception' \| 'normal' | 'active' |
| showProgressInfo | 是否显示进度信息 | boolean | true |

#### 自定义加载内容

```vue
<template>
  <LoadingState type="custom">
    <template #loading>
      <div class="custom-loading">
        <img src="/loading.gif" alt="Loading" />
        <p>正在加载数据...</p>
      </div>
    </template>
  </LoadingState>
</template>
```

---

### 3. Message - 消息提示工具

封装Ant Design Vue的Message和Notification组件，提供统一的消息提示接口。

#### 功能特性

- ✅ 轻量级消息提示（Message）
- ✅ 详细通知提示（Notification）
- ✅ 统一的API错误处理
- ✅ 预定义的常用提示方法
- ✅ 确认对话框

#### 基础用法

```javascript
import {
  success,
  error,
  warning,
  info,
  loading
} from '@/utils/message'

// 成功提示
success('操作成功')

// 错误提示
error('操作失败')

// 警告提示
warning('请注意')

// 信息提示
info('提示信息')

// 加载提示
const hide = loading('加载中...')
// 完成后关闭
setTimeout(() => hide(), 2000)
```

#### 详细通知

```javascript
import {
  notifySuccess,
  notifyError,
  notifyWarning,
  notifyInfo
} from '@/utils/message'

// 成功通知
notifySuccess({
  message: '任务完成',
  description: '文档处理已成功完成，共处理15页',
  duration: 4.5
})

// 错误通知
notifyError({
  message: '上传失败',
  description: '文件大小超过20MB限制',
  duration: 0 // 不自动关闭
})
```

#### API错误处理

```javascript
import { handleApiError } from '@/utils/message'
import axios from 'axios'

try {
  await axios.post('/api/v1/tasks', data)
} catch (error) {
  // 自动处理并显示错误信息
  handleApiError(error, '创建任务失败')
}
```

#### 确认对话框

```javascript
import { confirm } from '@/utils/message'

const handleDelete = async () => {
  try {
    await confirm({
      title: '确认删除',
      content: '删除后数据将无法恢复，确定要删除吗？',
      okText: '确定删除',
      cancelText: '取消',
      okType: 'danger'
    })
    
    // 用户确认后执行删除
    await deleteTask()
  } catch (error) {
    // 用户取消操作
    console.log('用户取消删除')
  }
}
```

#### 预定义方法

```javascript
import {
  saveSuccess,
  deleteSuccess,
  updateSuccess,
  createSuccess,
  copySuccess,
  exportSuccess,
  importSuccess,
  fileUploadSuccess,
  fileUploadError,
  taskSuccess,
  taskError
} from '@/utils/message'

// 保存成功
saveSuccess()

// 删除成功
deleteSuccess()

// 文件上传成功
fileUploadSuccess('document.pdf')

// 文件上传失败
fileUploadError('document.pdf', '文件格式不支持')

// 任务成功
taskSuccess('T_20251214_0001')

// 任务失败
taskError('T_20251214_0001', 'OCR识别失败')
```

#### API参考

##### 轻量级提示

| 方法 | 说明 | 参数 |
|------|------|------|
| success(content, duration?, onClose?) | 成功提示 | content: 提示内容<br>duration: 持续时间（秒）<br>onClose: 关闭回调 |
| error(content, duration?, onClose?) | 错误提示 | 同上 |
| warning(content, duration?, onClose?) | 警告提示 | 同上 |
| info(content, duration?, onClose?) | 信息提示 | 同上 |
| loading(content, duration?, onClose?) | 加载提示 | 同上 |

##### 详细通知

| 方法 | 说明 | 参数 |
|------|------|------|
| notifySuccess(options) | 成功通知 | options: { message, description, duration?, onClose?, onClick? } |
| notifyError(options) | 错误通知 | 同上 |
| notifyWarning(options) | 警告通知 | 同上 |
| notifyInfo(options) | 信息通知 | 同上 |

##### 工具方法

| 方法 | 说明 | 参数 |
|------|------|------|
| handleApiError(error, defaultMessage?) | 处理API错误 | error: 错误对象<br>defaultMessage: 默认错误消息 |
| confirm(options) | 确认对话框 | options: { title, content, onOk?, onCancel?, okText?, cancelText?, okType? } |

---

## 使用建议

### 1. 文件上传场景

- 规则编辑器的沙箱测试：使用FileUploader组件
- 任务上传页面：使用FileUploader组件
- 批量导入：使用FileUploader的多文件模式

### 2. 加载状态场景

- 页面初始加载：使用skeleton类型的LoadingState
- 数据提交中：使用spinner类型的LoadingState
- 文件上传中：使用progress类型的LoadingState
- 全屏操作：使用fullscreen模式的LoadingState

### 3. 消息提示场景

- 操作反馈：使用success/error等轻量级提示
- 重要通知：使用notifySuccess/notifyError等详细通知
- API错误：统一使用handleApiError处理
- 危险操作：使用confirm确认对话框

---

## 示例：完整的文件上传流程

```vue
<template>
  <div class="upload-page">
    <FileUploader
      accept=".pdf"
      :max-size="20 * 1024 * 1024"
      :auto-upload="false"
      ref="uploaderRef"
      @change="handleFileChange"
      @error="handleUploadError"
    />

    <a-button
      type="primary"
      :loading="isUploading"
      :disabled="!selectedFile"
      @click="handleSubmit"
    >
      开始上传
    </a-button>

    <LoadingState
      v-if="isUploading"
      type="progress"
      tip="正在上传文件..."
      :progress="uploadProgress"
      :fullscreen="true"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import FileUploader from '@/components/Common/FileUploader.vue'
import LoadingState from '@/components/Common/LoadingState.vue'
import { success, handleApiError } from '@/utils/message'
import { uploadFile } from '@/api/upload'

const uploaderRef = ref(null)
const selectedFile = ref(null)
const isUploading = ref(false)
const uploadProgress = ref(0)

const handleFileChange = (file) => {
  selectedFile.value = file
}

const handleUploadError = (error) => {
  console.error('文件验证失败:', error)
}

const handleSubmit = async () => {
  if (!selectedFile.value) return

  isUploading.value = true
  uploadProgress.value = 0

  try {
    const formData = new FormData()
    // 统一使用 files 字段名（支持单个或多个文件）
    formData.append('files', selectedFile.value)
    formData.append('rule_id', 'RULE001')

    // 模拟上传进度
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 300)

    const response = await uploadFile(formData)

    clearInterval(progressInterval)
    uploadProgress.value = 100

    success('文件上传成功')
    
    // 清空上传器
    uploaderRef.value?.clear()
    selectedFile.value = null
  } catch (error) {
    handleApiError(error, '文件上传失败')
  } finally {
    isUploading.value = false
    uploadProgress.value = 0
  }
}
</script>
```

---

## 注意事项

1. **文件上传器**
   - 确保设置合适的文件类型和大小限制
   - 处理上传失败的情况
   - 大文件上传时考虑使用分片上传

2. **加载状态**
   - 根据场景选择合适的加载类型
   - 避免过度使用全屏加载
   - 骨架屏应与实际内容结构相似

3. **消息提示**
   - 避免同时显示过多消息
   - 重要信息使用通知而非轻量级提示
   - 错误信息应提供明确的解决建议

---

## 更新日志

### v1.0.0 (2025-12-14)
- ✅ 创建FileUploader组件
- ✅ 创建LoadingState组件
- ✅ 创建Message工具函数
- ✅ 完善组件文档
