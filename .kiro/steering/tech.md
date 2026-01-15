# Tech Stack & Build System

## Monorepo Structure

| Package | Technology | Purpose |
|---------|------------|---------|
| `docs/` | VitePress ^2.0 | 文档站点 |
| `admin/` | Nuxt 3.14+ | 后台管理系统 |
| `shared/` | TypeScript | 共享 Schema/Types |

## Core Technologies

| Category | Technology | Version |
|----------|------------|---------|
| Docs Framework | VitePress | ^2.0.0 |
| Admin Framework | Nuxt 3 | ^3.14.0 |
| UI Components | Nuxt UI v3 | (Radix Vue) |
| Editor | md-editor-v3 | ^6.3.1 |
| Database | PostgreSQL | Neon 托管 |
| ORM | Drizzle ORM | ^0.36.0 |
| Auth | nuxt-auth-utils | 钉钉 OAuth |
| AI SDK | @ai-sdk/vue | 流式翻译 |
| State | Pinia + VueUse | 状态管理 |
| CSS | Tailwind CSS | ^4.0.0 |
| Package Manager | pnpm | ^9.0.0 |
| File Storage | MinIO | 对象存储 |

## Development Commands

```bash
# 安装依赖
pnpm install

# 文档站点
pnpm docs:dev
pnpm docs:build

# 后台系统
pnpm dev:admin
pnpm build:admin

# 数据库
pnpm db:generate    # 生成迁移
pnpm db:migrate     # 执行迁移
pnpm db:studio      # Drizzle Studio
```

## Code Conventions

- **Vue Components**: Composition API with `<script setup lang="ts">`
- **TypeScript**: Strict mode enabled
- **Styling**: Tailwind CSS + CSS variables for theming
- **Comments**: Chinese language for code comments
- **State**: Composables (`use*`) + Pinia stores

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://...

# DingTalk OAuth
DINGTALK_APP_KEY=your-app-key
DINGTALK_APP_SECRET=your-app-secret

# AI Service
OPENAI_API_KEY=your-api-key

# Docs (VitePress)
VITE_DIFY_API_BASE=https://your-dify-instance/v1
VITE_DIFY_API_KEY=your-api-key
```

## Agent Guidelines

### 第三方依赖使用规范

使用第三方库时，**必须先查阅对应版本的官方文档**：

- VitePress 2.0: Context7 查询 `/vitepress/vitepress`
- Nuxt 3: Context7 查询 `/nuxt/nuxt`
- Nuxt UI v3: Context7 查询 `/nuxt/ui`
- md-editor-v3: Context7 查询 `/imzbf/md-editor-v3`
- Drizzle ORM: Context7 查询 `/drizzle-team/drizzle-orm`

### UI 参考

参考 Mintlify 风格实现简约大气的后台界面。
