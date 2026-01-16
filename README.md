# FORCOME 知识库平台

企业知识管理平台，包含 VitePress 文档站点和 Nuxt 4 后台管理系统。

## 项目结构

```
├── docs/                    # VitePress 文档站点
│   ├── .vitepress/          # VitePress 配置和主题
│   ├── zh/                  # 中文文档
│   ├── en/                  # 英文文档
│   └── vi/                  # 越南语文档
├── admin/                   # Nuxt 4 后台管理系统
│   ├── server/              # API 服务端
│   │   ├── api/             # API 端点
│   │   ├── middleware/      # 服务端中间件
│   │   └── utils/           # 工具函数
│   ├── pages/               # 页面
│   ├── components/          # 组件
│   ├── composables/         # 组合式函数
│   └── stores/              # Pinia 状态管理
├── shared/                  # 共享代码
│   ├── schema/              # Drizzle ORM Schema
│   └── types/               # TypeScript 类型定义
└── drizzle/                 # 数据库迁移文件
```

## 技术栈

### 文档站点 (docs/)
- VitePress 2.0
- Vue 3.5
- TailwindCSS 4
- Mermaid (图表)
- Markmap (思维导图)

### 后台管理 (admin/)
- Nuxt 4.2
- Vue 3.5
- Pinia (状态管理)
- @nuxt/ui 4.x (UI 组件库)
- @nuxt/icon (图标模块)
- @fontsource (本地字体)
- md-editor-v3 (Markdown 编辑器)

### 后端
- Nitro (Nuxt 服务端框架)
- PostgreSQL (数据库)
- Drizzle ORM (数据库 ORM)
- MinIO (对象存储)

### 第三方集成
- 钉钉 OAuth (认证)
- OpenAI API (AI 翻译)

## 快速开始

### 环境要求

- Node.js >= 18
- pnpm >= 8
- PostgreSQL >= 14
- MinIO (可选，用于文件存储)

### 安装依赖

```bash
pnpm install
```

### 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入实际配置：

```env
# 数据库
DATABASE_URL=postgresql://user:password@localhost:5432/forcome_docs

# 钉钉 OAuth
DINGTALK_APP_KEY=your_app_key
DINGTALK_APP_SECRET=your_app_secret
DINGTALK_AGENT_ID=your_agent_id

# OpenAI (用于 AI 翻译)
OPENAI_API_KEY=your_openai_key

# MinIO (对象存储)
MINIO_ENDPOINT=localhost
MINIO_PORT=9000
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
MINIO_BUCKET=forcome-docs

# Session
NUXT_SESSION_PASSWORD=your_session_password_at_least_32_chars
```

### 数据库迁移

```bash
# 生成迁移文件
pnpm db:generate

# 执行迁移
pnpm db:migrate

# 打开数据库管理界面
pnpm db:studio
```

### 启动开发服务器

```bash
# 启动文档站点 (默认端口 5173)
pnpm docs:dev

# 启动后台管理 (默认端口 3000)
pnpm admin:dev

# 同时启动两个服务
pnpm dev
```

### 构建生产版本

```bash
# 构建文档站点
pnpm docs:build

# 构建后台管理
pnpm admin:build

# 构建所有
pnpm build
```

## 主要功能

### 文档管理
- 多语言支持 (中文、英文、越南语)
- Markdown 编辑器 (支持 Slash 命令)
- 版本历史
- 文档发布流程

### 权限管理
- 基于角色的访问控制 (Admin, Editor, Viewer)
- 文档级别权限设置
- 部门权限支持

### 协作功能
- 编辑锁 (防止并发编辑)
- 评论系统
- 文档关注
- 活动日志

### 内容发布
- 批量发布
- Git 同步
- AI 翻译

## 开发指南

### 目录约定

- `admin/server/api/` - API 端点，文件名即路由
- `admin/composables/` - 可复用的组合式函数
- `admin/components/` - Vue 组件
- `shared/types/` - 共享类型定义

### 类型定义

所有类型定义集中在 `shared/types/index.ts`，Admin 通过 `@shared/types` 导入。

主要类型包括：
- 实体类型：`User`, `Document`, `Category`, `NavMenu`, `Comment` 等
- API 响应类型：`ApiResponse<T>`, `PaginatedResponse<T>`
- API 请求类型：`CreateDocumentRequest`, `UpdateDocumentRequest` 等
- 工具类型：`ReorderItem` (拖拽排序)

### API 开发

使用 `admin/server/utils/api-response.ts` 提供的工具函数：

```typescript
import { requireAuth, Errors } from '../utils/api-response'

export default defineEventHandler(async (event) => {
  // 验证登录
  const user = await requireAuth(event)

  // 业务逻辑
  // ...

  // 返回数据
  return { success: true, data: result }
})
```

### 权限检查

使用 `admin/server/utils/permissions.ts` 提供的工具函数：

```typescript
import { requireDocumentPermission } from '../utils/permissions'

export default defineEventHandler(async (event) => {
  const documentId = getRouterParam(event, 'id')

  // 验证文档编辑权限
  await requireDocumentPermission(event, documentId, 'edit')

  // 业务逻辑
  // ...
})
```

### 服务端认证中间件

`admin/server/middleware/auth.ts` 自动保护所有 API 路由，以下路径除外：
- `/api/auth/*` - 认证相关
- `/api/health` - 健康检查
- `/api/_nuxt_icon/*` - Nuxt Icon 内部 API

### 图标配置

项目使用 @nuxt/icon 模块配合本地图标包：
- `@iconify-json/lucide` - Lucide 图标
- `@iconify-json/simple-icons` - 品牌图标

**TailwindCSS v4 兼容配置** (`app.config.ts`)：
```typescript
export default defineAppConfig({
  icon: {
    mode: 'css',
    cssLayer: 'base',  // TailwindCSS v4 必需
  },
})
```

**图标模块配置** (`nuxt.config.ts`)：
```typescript
icon: {
  serverBundle: {
    collections: ['lucide', 'simple-icons'],
  },
  clientBundle: {
    scan: true,  // 自动扫描并预打包常用图标
  },
},
```

### 测试页面

测试页面 (`/test-*`) 仅在开发环境可用，生产环境自动返回 404。

## 许可证

MIT License

Copyright © 2024-present FORCOME
