# 视频上传功能说明

## 功能概述

FORCOME 知识库平台已完整支持视频上传功能，基于 MinIO 对象存储实现。

## 支持的视频格式

| 格式 | MIME 类型 | 扩展名 |
|------|-----------|--------|
| MP4 | video/mp4 | .mp4 |
| WebM | video/webm | .webm |
| OGG | video/ogg | .ogg |
| QuickTime | video/quicktime | .mov |

## 文件限制

- **最大文件大小**: 100 MB
- **存储路径**: `video/{year}/{month}/{timestamp}-{random}{ext}`
- **示例**: `video/2025/01/1736123456789-abc123.mp4`

## 使用方式

### 1. 在编辑器中使用

编辑器已集成视频上传扩展，支持：

- 点击工具栏视频按钮上传
- 拖拽视频文件到编辑器
- 使用斜杠命令 `/video` 插入视频

**视频节点功能**：
- ✅ 播放控制（播放、暂停、音量）
- ✅ 自动播放开关
- ✅ 循环播放开关
- ✅ 静音开关
- ✅ 上传进度显示
- ✅ 删除视频

### 2. 使用 Composable

```typescript
import { useVideoUpload } from '~/composables/useUpload'

const videoUpload = useVideoUpload({
  onSuccess: (result) => {
    console.log('上传成功:', result.url)
  },
  onError: (error) => {
    console.error('上传失败:', error)
  },
  onProgress: (progress) => {
    console.log('进度:', progress)
  },
})

// 方式 1: 直接上传文件
await videoUpload.upload(file)

// 方式 2: 打开文件选择器
await videoUpload.openPicker()
```

### 3. 使用 API

```typescript
// POST /api/upload?type=video
const formData = new FormData()
formData.append('file', videoFile)

const response = await fetch('/api/upload?type=video', {
  method: 'POST',
  body: formData,
})

const result = await response.json()
console.log('视频 URL:', result.data.url)
```

## 测试页面

访问 `/test-video-upload` 页面测试视频上传功能：

```bash
# 启动开发服务器
pnpm dev:admin

# 访问测试页面
http://localhost:3000/test-video-upload
```

## MinIO 配置

确保 `.env` 文件中配置了 MinIO 相关环境变量：

```bash
# MinIO 服务器地址
MINIO_ENDPOINT=localhost

# MinIO 端口
MINIO_PORT=9000

# 是否使用 SSL
MINIO_USE_SSL=false

# MinIO 访问密钥
MINIO_ACCESS_KEY=your-access-key

# MinIO 密钥
MINIO_SECRET_KEY=your-secret-key

# Bucket 名称
MINIO_BUCKET=forcome-docs

# 公开访问 URL（可选）
MINIO_PUBLIC_URL=https://cdn.example.com
```

## 技术实现

### 后端

- **ORM**: Drizzle ORM
- **存储**: MinIO Client
- **验证**: 文件类型、大小验证
- **路径**: 自动生成唯一对象名称

### 前端

- **编辑器**: TipTap Video Extension
- **上传**: XMLHttpRequest (支持进度跟踪)
- **UI**: Nuxt UI v3 组件
- **状态**: Composable 封装

### 文件结构

```
admin/
├── server/
│   ├── api/
│   │   └── upload.post.ts          # 上传 API
│   └── utils/
│       └── minio.ts                # MinIO 工具函数
├── components/
│   └── editor/
│       ├── extensions/
│       │   └── Video.ts            # 视频扩展
│       └── VideoView.vue           # 视频节点视图
├── composables/
│   └── useUpload.ts                # 上传 Composable
└── pages/
    └── test-video-upload.vue       # 测试页面
```

## 安全性

- ✅ 文件类型白名单验证
- ✅ 文件大小限制
- ✅ 用户认证检查
- ✅ 上传元数据记录
- ✅ Bucket 公开读取策略

## 性能优化

- ✅ 流式上传
- ✅ 进度跟踪
- ✅ 预加载元数据
- ✅ 临时 URL 预览
- ✅ 自动清理临时对象

## 浏览器兼容性

| 浏览器 | 版本 | 支持 |
|--------|------|------|
| Chrome | 90+ | ✅ |
| Firefox | 88+ | ✅ |
| Safari | 14+ | ✅ |
| Edge | 90+ | ✅ |

## 常见问题

### 1. 上传失败

检查：
- MinIO 服务是否运行
- 环境变量配置是否正确
- 网络连接是否正常
- 文件大小是否超过限制

### 2. 视频无法播放

检查：
- 视频格式是否支持
- 浏览器是否支持该编码
- MinIO Bucket 策略是否正确
- 视频 URL 是否可访问

### 3. 上传速度慢

优化：
- 使用 CDN 加速
- 配置 MinIO 公开访问 URL
- 压缩视频文件
- 使用更快的网络连接

## 未来计划

- [ ] 视频转码（多分辨率）
- [ ] 视频缩略图生成
- [ ] 视频时长检测
- [ ] 批量上传
- [ ] 断点续传
- [ ] 视频水印
- [ ] 视频剪辑

## 相关文档

- [MinIO 官方文档](https://min.io/docs/minio/linux/index.html)
- [TipTap 视频扩展](https://tiptap.dev/docs/editor/extensions/nodes/video)
- [Nuxt UI 组件](https://ui.nuxt.com/)
