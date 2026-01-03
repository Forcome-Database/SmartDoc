# Technical Design Document

## Introduction

本文档描述 FORCOME 知识库后台管理系统的技术架构设计。系统采用 **Nuxt 3** 全栈框架，与 VitePress 文档站点共享 Vue 技术栈和组件，集成钉钉 OAuth 认证、PostgreSQL 数据库、Tiptap 编辑器，实现类 Mintlify 风格的文档管理平台。

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Admin System (Nuxt 3)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ Nuxt UI  │  │  Tiptap  │  │ Tailwind │  │ VueUse + Pinia   │ │
│  │ (Radix)  │  │  (Vue)   │  │   CSS    │  │ (State)          │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (Nuxt Server API)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ nuxt-auth│  │ Drizzle  │  │ AI SDK   │  │ simple-git       │ │
│  │(DingTalk)│  │   ORM    │  │ (Nuxt)   │  │ (Git Service)    │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌────────────────┐
│   PostgreSQL     │ │   VitePress      │ │  DingTalk API  │
│   (Neon)         │ │   docs/ folder   │ │  (OAuth/Msg)   │
└──────────────────┘ └──────────────────┘ └────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Shared Components                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  docs/.vitepress/theme/components/                        │   │
│  │  Quiz.vue | MermaidWrapper.vue | Markmap.vue | ...        │   │
│  │  (VitePress 和 Admin 共用)                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Framework | **Nuxt 3.14+** | Vue 全栈框架，SSR/SSG 支持 |
| UI Components | **Nuxt UI v3** | 基于 Radix Vue 的组件库 |
| Editor | **Tiptap 2 (Vue)** | 可扩展的富文本编辑器 |
| Styling | Tailwind CSS v4 | 原子化 CSS |
| Database | PostgreSQL (Neon) | 主数据存储 |
| ORM | Drizzle ORM | 类型安全的数据库操作 |
| Auth | **nuxt-auth-utils** | 钉钉 OAuth 集成 |
| AI | **@ai-sdk/vue** | 流式翻译服务 |
| Git | simple-git | Git 操作封装 |
| State | **Pinia + VueUse** | 状态管理 + 工具函数 |

### 技术栈优势

1. **组件复用**: VitePress 的 Vue 组件可直接在 Admin 中使用
2. **编辑即所见**: Tiptap Vue 版本可直接渲染 Quiz 等交互组件
3. **统一生态**: Vue 3 + TypeScript 全栈，降低维护成本
4. **Nuxt 特性**: 自动导入、文件路由、Server API、SEO 优化

## Project Structure

```
project-root/
├── docs/                          # VitePress 文档站点
│   ├── .vitepress/
│   │   ├── config.ts
│   │   └── theme/
│   │       ├── components/        # 🔗 共享组件
│   │       │   ├── Quiz.vue
│   │       │   ├── MermaidWrapper.vue
│   │       │   ├── Markmap.vue
│   │       │   └── Callout.vue
│   │       └── ...
│   ├── zh/
│   ├── en/
│   └── vi/
│
├── admin/                         # Nuxt 3 后台系统
│   ├── nuxt.config.ts
│   ├── app.vue
│   ├── pages/
│   │   ├── index.vue              # Dashboard
│   │   ├── login.vue              # 登录页
│   │   ├── documents/
│   │   │   ├── index.vue          # 文档列表
│   │   │   └── [id].vue           # 文档编辑
│   │   ├── categories/
│   │   │   └── index.vue          # 栏目管理
│   │   ├── nav-menus/
│   │   │   └── index.vue          # 导航菜单管理
│   │   └── settings/
│   │       ├── locales.vue        # 语言管理
│   │       └── users.vue          # 用户管理
│   ├── components/
│   │   ├── editor/
│   │   │   ├── DocumentEditor.vue
│   │   │   ├── EditorToolbar.vue
│   │   │   ├── SlashCommand.vue
│   │   │   └── extensions/        # Tiptap 扩展
│   │   ├── file-tree/
│   │   │   ├── FileTree.vue
│   │   │   └── FileTreeItem.vue
│   │   ├── layout/
│   │   │   ├── AppHeader.vue
│   │   │   ├── AppSidebar.vue
│   │   │   └── Breadcrumb.vue
│   │   └── shared/                # 🔗 链接到 docs 组件
│   ├── composables/
│   │   ├── useEditLock.ts
│   │   ├── useTranslation.ts
│   │   └── useAutoSave.ts
│   ├── server/
│   │   ├── api/
│   │   │   ├── auth/
│   │   │   │   └── dingtalk.ts
│   │   │   ├── documents/
│   │   │   ├── categories/
│   │   │   ├── locales/
│   │   │   ├── nav-menus/
│   │   │   └── translate.ts
│   │   ├── utils/
│   │   │   ├── db.ts
│   │   │   ├── git.ts
│   │   │   └── dingtalk.ts
│   │   └── middleware/
│   │       └── auth.ts
│   ├── stores/
│   │   ├── user.ts
│   │   └── editor.ts
│   └── types/
│       └── index.ts
│
├── shared/                        # 共享代码
│   ├── components/                # 符号链接到 docs 组件
│   ├── schema/                    # Drizzle Schema
│   │   ├── users.ts
│   │   ├── documents.ts
│   │   ├── categories.ts
│   │   ├── locales.ts
│   │   └── index.ts
│   └── types/
│       └── index.ts
│
├── drizzle.config.ts
├── package.json
└── pnpm-workspace.yaml            # Monorepo 配置
```


## Monorepo Configuration

```yaml
# pnpm-workspace.yaml
packages:
  - 'docs'
  - 'admin'
  - 'shared'
```

```json
// package.json (root)
{
  "name": "forcome-docs",
  "private": true,
  "scripts": {
    "dev:docs": "pnpm --filter docs dev",
    "dev:admin": "pnpm --filter admin dev",
    "build:docs": "pnpm --filter docs build",
    "build:admin": "pnpm --filter admin build",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "drizzle-kit migrate",
    "db:studio": "drizzle-kit studio"
  },
  "devDependencies": {
    "drizzle-kit": "^0.25.0",
    "typescript": "^5.3.3"
  }
}
```

```typescript
// admin/nuxt.config.ts
export default defineNuxtConfig({
  devtools: { enabled: true },

  modules: [
    '@nuxt/ui',
    '@pinia/nuxt',
    '@vueuse/nuxt',
    'nuxt-auth-utils',
  ],

  // 共享组件别名
  alias: {
    '@shared': '../shared',
    '@docs-components': '../docs/.vitepress/theme/components',
  },

  // 自动导入 docs 组件
  components: [
    { path: '~/components' },
    { path: '../docs/.vitepress/theme/components', prefix: 'Docs' },
  ],

  // Tailwind CSS
  css: ['~/assets/css/main.css'],

  // 运行时配置
  runtimeConfig: {
    // 服务端私有
    databaseUrl: process.env.DATABASE_URL,
    dingtalkAppKey: process.env.DINGTALK_APP_KEY,
    dingtalkAppSecret: process.env.DINGTALK_APP_SECRET,
    dingtalkAgentId: process.env.DINGTALK_AGENT_ID,
    openaiApiKey: process.env.OPENAI_API_KEY,
    docsRoot: process.env.DOCS_ROOT || '../docs',
    // 客户端公开
    public: {
      appName: 'FORCOME 知识库管理',
    },
  },

  // Nitro 服务端配置
  nitro: {
    experimental: {
      asyncContext: true,
    },
  },

  compatibilityDate: '2024-12-01',
})
```

## Database Schema Design

### Entity Relationship Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    users    │     │  documents  │     │  versions   │
├─────────────┤     ├─────────────┤     ├─────────────┤
│ id (PK)     │◄────│ author_id   │     │ id (PK)     │
│ dingtalk_id │     │ id (PK)     │◄────│ document_id │
│ union_id    │     │ category_id │     │ version_num │
│ name        │     │ title       │     │ content     │
│ avatar      │     │ slug        │     │ change_log  │
│ department  │     │ locale_id   │     │ author_id   │
│ role        │     │ status      │     │ created_at  │
│ created_at  │     │ created_at  │     └─────────────┘
└─────────────┘     │ updated_at  │
       │            └─────────────┘
       │                   │
       │            ┌──────┴──────┐
       │            ▼             ▼
       │     ┌─────────────┐ ┌─────────────┐
       │     │ categories  │ │ edit_locks  │
       │     ├─────────────┤ ├─────────────┤
       │     │ id (PK)     │ │ id (PK)     │
       │     │ parent_id   │ │ document_id │
       │     │ slug        │ │ user_id     │
       │     │ sort_order  │ │ acquired_at │
       │     │ created_at  │ │ expires_at  │
       │     └─────────────┘ └─────────────┘
       │            │
       │            ▼
       │     ┌──────────────────┐     ┌─────────────┐
       │     │ category_titles  │     │   locales   │
       │     ├──────────────────┤     ├─────────────┤
       │     │ id (PK)          │     │ id (PK)     │
       │     │ category_id (FK) │     │ code        │
       │     │ locale_id (FK)   │────>│ name        │
       │     │ title            │     │ native_name │
       │     └──────────────────┘     │ is_default  │
       │                              │ is_enabled  │
       │                              │ sort_order  │
       └──────────────────────────────│ created_at  │
                                      └─────────────┘

┌─────────────┐     ┌──────────────────┐
│  nav_menus  │     │ nav_menu_titles  │
├─────────────┤     ├──────────────────┤
│ id (PK)     │◄────│ nav_menu_id (FK) │
│ parent_id   │     │ locale_id (FK)   │
│ type        │     │ title            │
│ target_type │     └──────────────────┘
│ target_id   │
│ external_url│
│ sort_order  │
│ is_visible  │
└─────────────┘
```

### Drizzle Schema Definition

```typescript
// shared/schema/index.ts
import { pgTable, text, timestamp, boolean, integer, pgEnum, unique } from 'drizzle-orm/pg-core';
import { relations } from 'drizzle-orm';

// ============ Enums ============
export const userRoleEnum = pgEnum('user_role', ['admin', 'editor', 'viewer']);
export const documentStatusEnum = pgEnum('document_status', ['draft', 'published', 'archived']);
export const navMenuTypeEnum = pgEnum('nav_menu_type', ['link', 'dropdown', 'divider']);
export const navMenuTargetTypeEnum = pgEnum('nav_menu_target_type', ['category', 'document', 'external', 'none']);
export const translationStatusEnum = pgEnum('translation_status', ['pending', 'processing', 'completed', 'failed']);

// ============ Locales ============
export const locales = pgTable('locales', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  code: text('code').unique().notNull(),
  name: text('name').notNull(),
  nativeName: text('native_name').notNull(),
  isDefault: boolean('is_default').default(false).notNull(),
  isEnabled: boolean('is_enabled').default(true).notNull(),
  sortOrder: integer('sort_order').default(0).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// ============ Users ============
export const users = pgTable('users', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  dingtalkId: text('dingtalk_id').unique().notNull(),
  unionId: text('union_id').unique(),
  name: text('name').notNull(),
  avatar: text('avatar'),
  email: text('email'),
  mobile: text('mobile'),
  department: text('department'),
  departmentId: text('department_id'),
  role: userRoleEnum('role').default('editor').notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

// ============ Categories ============
export const categories = pgTable('categories', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  parentId: text('parent_id').references(() => categories.id),
  slug: text('slug').notNull(),
  sortOrder: integer('sort_order').default(0).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

export const categoryTitles = pgTable('category_titles', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  categoryId: text('category_id').references(() => categories.id, { onDelete: 'cascade' }).notNull(),
  localeId: text('locale_id').references(() => locales.id).notNull(),
  title: text('title').notNull(),
}, (table) => ({
  uniqueCategoryLocale: unique().on(table.categoryId, table.localeId),
}));

// ============ Documents ============
export const documents = pgTable('documents', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  categoryId: text('category_id').references(() => categories.id),
  authorId: text('author_id').references(() => users.id).notNull(),
  localeId: text('locale_id').references(() => locales.id).notNull(),
  title: text('title').notNull(),
  slug: text('slug').notNull(),
  content: text('content').default('').notNull(),
  status: documentStatusEnum('status').default('draft').notNull(),
  publishedVersion: integer('published_version'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
}, (table) => ({
  uniqueSlugLocale: unique().on(table.categoryId, table.localeId, table.slug),
}));

// ============ Versions ============
export const versions = pgTable('versions', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  documentId: text('document_id').references(() => documents.id, { onDelete: 'cascade' }).notNull(),
  versionNum: integer('version_num').notNull(),
  content: text('content').notNull(),
  changeLog: text('change_log'),
  authorId: text('author_id').references(() => users.id).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// ============ Edit Locks ============
export const editLocks = pgTable('edit_locks', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  documentId: text('document_id').references(() => documents.id, { onDelete: 'cascade' }).unique().notNull(),
  userId: text('user_id').references(() => users.id).notNull(),
  acquiredAt: timestamp('acquired_at').defaultNow().notNull(),
  expiresAt: timestamp('expires_at').notNull(),
});

// ============ Nav Menus ============
export const navMenus = pgTable('nav_menus', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  parentId: text('parent_id').references(() => navMenus.id),
  type: navMenuTypeEnum('type').default('link').notNull(),
  targetType: navMenuTargetTypeEnum('target_type').default('none').notNull(),
  targetId: text('target_id'),
  externalUrl: text('external_url'),
  openInNewTab: boolean('open_in_new_tab').default(false).notNull(),
  icon: text('icon'),
  sortOrder: integer('sort_order').default(0).notNull(),
  isVisible: boolean('is_visible').default(true).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

export const navMenuTitles = pgTable('nav_menu_titles', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  navMenuId: text('nav_menu_id').references(() => navMenus.id, { onDelete: 'cascade' }).notNull(),
  localeId: text('locale_id').references(() => locales.id).notNull(),
  title: text('title').notNull(),
}, (table) => ({
  uniqueMenuLocale: unique().on(table.navMenuId, table.localeId),
}));

// ============ Translations ============
export const translations = pgTable('translations', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  documentId: text('document_id').references(() => documents.id, { onDelete: 'cascade' }).notNull(),
  sourceLocaleId: text('source_locale_id').references(() => locales.id).notNull(),
  targetLocaleId: text('target_locale_id').references(() => locales.id).notNull(),
  status: translationStatusEnum('status').default('pending').notNull(),
  result: text('result'),
  createdBy: text('created_by').references(() => users.id).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// ============ Relations ============
export const usersRelations = relations(users, ({ many }) => ({
  documents: many(documents),
  versions: many(versions),
  editLocks: many(editLocks),
}));

export const documentsRelations = relations(documents, ({ one, many }) => ({
  author: one(users, { fields: [documents.authorId], references: [users.id] }),
  category: one(categories, { fields: [documents.categoryId], references: [categories.id] }),
  locale: one(locales, { fields: [documents.localeId], references: [locales.id] }),
  versions: many(versions),
  editLock: one(editLocks),
}));

export const categoriesRelations = relations(categories, ({ one, many }) => ({
  parent: one(categories, { fields: [categories.parentId], references: [categories.id] }),
  children: many(categories),
  titles: many(categoryTitles),
  documents: many(documents),
}));
```


## Component Design

### 1. DingTalk OAuth Integration (Nuxt)

```typescript
// admin/server/api/auth/dingtalk.get.ts
// 钉钉 OAuth 回调处理

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig();
  const query = getQuery(event);
  const { code } = query;

  if (!code) {
    throw createError({ statusCode: 400, message: '缺少授权码' });
  }

  try {
    // 1. 获取 access_token
    const tokenRes = await $fetch<{
      accessToken: string;
      refreshToken: string;
      expireIn: number;
    }>('https://api.dingtalk.com/v1.0/oauth2/userAccessToken', {
      method: 'POST',
      body: {
        clientId: config.dingtalkAppKey,
        clientSecret: config.dingtalkAppSecret,
        code,
        grantType: 'authorization_code',
      },
    });

    // 2. 获取用户信息
    const userInfo = await $fetch<{
      nick: string;
      avatarUrl: string;
      mobile: string;
      openId: string;
      unionId: string;
      email: string;
    }>('https://api.dingtalk.com/v1.0/contact/users/me', {
      headers: {
        'x-acs-dingtalk-access-token': tokenRes.accessToken,
      },
    });

    // 3. 查找或创建用户
    const db = useDb();
    let user = await db.query.users.findFirst({
      where: eq(users.dingtalkId, userInfo.openId),
    });

    if (!user) {
      // 新用户
      const [newUser] = await db.insert(users).values({
        dingtalkId: userInfo.openId,
        unionId: userInfo.unionId,
        name: userInfo.nick,
        avatar: userInfo.avatarUrl,
        email: userInfo.email,
        mobile: userInfo.mobile,
        role: 'editor',
      }).returning();
      user = newUser;
    } else {
      // 更新用户信息
      await db.update(users)
        .set({
          name: userInfo.nick,
          avatar: userInfo.avatarUrl,
          updatedAt: new Date(),
        })
        .where(eq(users.id, user.id));
    }

    // 4. 设置 session
    await setUserSession(event, {
      user: {
        id: user.id,
        name: user.name,
        avatar: user.avatar,
        role: user.role,
        dingtalkId: user.dingtalkId,
      },
    });

    // 5. 重定向到首页
    return sendRedirect(event, '/');
  } catch (error) {
    console.error('DingTalk OAuth error:', error);
    throw createError({ statusCode: 500, message: '登录失败' });
  }
});
```

```typescript
// admin/server/api/auth/logout.post.ts
export default defineEventHandler(async (event) => {
  await clearUserSession(event);
  return { success: true };
});
```

```vue
<!-- admin/pages/login.vue -->
<script setup lang="ts">
definePageMeta({ layout: 'blank' });

const config = useRuntimeConfig();

// 钉钉登录 URL
const dingtalkLoginUrl = computed(() => {
  const params = new URLSearchParams({
    client_id: config.public.dingtalkAppKey,
    redirect_uri: `${window.location.origin}/api/auth/dingtalk`,
    response_type: 'code',
    scope: 'openid corpid',
    prompt: 'consent',
  });
  return `https://login.dingtalk.com/oauth2/auth?${params}`;
});
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
    <UCard class="w-full max-w-md">
      <template #header>
        <div class="text-center">
          <h1 class="text-2xl font-bold">FORCOME 知识库</h1>
          <p class="text-gray-500 mt-2">后台管理系统</p>
        </div>
      </template>

      <div class="space-y-4">
        <UButton
          :to="dingtalkLoginUrl"
          external
          block
          size="lg"
          color="primary"
          icon="i-simple-icons-dingtalk"
        >
          使用钉钉登录
        </UButton>
      </div>
    </UCard>
  </div>
</template>
```

### 2. Document Editor (Tiptap Vue)

```vue
<!-- admin/components/editor/DocumentEditor.vue -->
<script setup lang="ts">
/**
 * 文档编辑器
 * 基于 Tiptap，支持 Slash Command 和自定义组件
 */
import { useEditor, EditorContent, BubbleMenu } from '@tiptap/vue-3';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight';
import Image from '@tiptap/extension-image';
import Link from '@tiptap/extension-link';
import Table from '@tiptap/extension-table';
import TableRow from '@tiptap/extension-table-row';
import TableCell from '@tiptap/extension-table-cell';
import TableHeader from '@tiptap/extension-table-header';
import TaskList from '@tiptap/extension-task-list';
import TaskItem from '@tiptap/extension-task-item';
import { common, createLowlight } from 'lowlight';

// 自定义扩展
import { SlashCommand } from './extensions/SlashCommand';
import { ComponentBlock } from './extensions/ComponentBlock';

const props = defineProps<{
  modelValue: string;
  documentId: string;
  readOnly?: boolean;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: string];
  'save': [];
}>();

const lowlight = createLowlight(common);

const editor = useEditor({
  content: props.modelValue,
  editable: !props.readOnly,
  extensions: [
    StarterKit.configure({
      codeBlock: false,
    }),
    Placeholder.configure({
      placeholder: '输入 "/" 打开命令菜单...',
    }),
    CodeBlockLowlight.configure({ lowlight }),
    Image.configure({ allowBase64: true }),
    Link.configure({ openOnClick: false }),
    Table.configure({ resizable: true }),
    TableRow,
    TableCell,
    TableHeader,
    TaskList,
    TaskItem.configure({ nested: true }),
    SlashCommand,
    ComponentBlock,
  ],
  editorProps: {
    attributes: {
      class: 'prose prose-lg dark:prose-invert max-w-none focus:outline-none min-h-[500px] px-4 py-2',
    },
  },
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML());
  },
});

// 自动保存
const { start: startAutoSave, stop: stopAutoSave } = useAutoSave({
  documentId: props.documentId,
  getContent: () => editor.value?.getHTML() || '',
  onSave: () => emit('save'),
  debounceMs: 2000,
});

onMounted(() => {
  startAutoSave();
});

onUnmounted(() => {
  stopAutoSave();
  editor.value?.destroy();
});

// 监听内容变化
watch(() => props.modelValue, (newValue) => {
  if (editor.value && newValue !== editor.value.getHTML()) {
    editor.value.commands.setContent(newValue, false);
  }
});

// 快捷键保存
useEventListener('keydown', (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 's') {
    e.preventDefault();
    emit('save');
  }
});
</script>

<template>
  <div class="document-editor">
    <!-- 工具栏 -->
    <EditorToolbar v-if="editor && !readOnly" :editor="editor" />

    <!-- 气泡菜单 -->
    <BubbleMenu
      v-if="editor && !readOnly"
      :editor="editor"
      :tippy-options="{ duration: 100 }"
      class="bubble-menu"
    >
      <UButtonGroup size="xs">
        <UButton
          :variant="editor.isActive('bold') ? 'solid' : 'ghost'"
          icon="i-lucide-bold"
          @click="editor.chain().focus().toggleBold().run()"
        />
        <UButton
          :variant="editor.isActive('italic') ? 'solid' : 'ghost'"
          icon="i-lucide-italic"
          @click="editor.chain().focus().toggleItalic().run()"
        />
        <UButton
          :variant="editor.isActive('strike') ? 'solid' : 'ghost'"
          icon="i-lucide-strikethrough"
          @click="editor.chain().focus().toggleStrike().run()"
        />
        <UButton
          :variant="editor.isActive('code') ? 'solid' : 'ghost'"
          icon="i-lucide-code"
          @click="editor.chain().focus().toggleCode().run()"
        />
        <UButton
          :variant="editor.isActive('link') ? 'solid' : 'ghost'"
          icon="i-lucide-link"
          @click="setLink"
        />
      </UButtonGroup>
    </BubbleMenu>

    <!-- 编辑器内容 -->
    <EditorContent :editor="editor" />
  </div>
</template>

<style scoped>
.document-editor {
  @apply border rounded-lg bg-white dark:bg-gray-900;
}

.bubble-menu {
  @apply bg-white dark:bg-gray-800 border rounded-lg shadow-lg p-1;
}
</style>
```


### 3. Component Block Extension (Tiptap)

```typescript
// admin/components/editor/extensions/ComponentBlock.ts
/**
 * 自定义组件块扩展
 * 支持在编辑器中插入和编辑 Vue 组件
 */
import { Node, mergeAttributes } from '@tiptap/core';
import { VueNodeViewRenderer } from '@tiptap/vue-3';
import ComponentBlockView from '../ComponentBlockView.vue';

export interface ComponentBlockOptions {
  HTMLAttributes: Record<string, any>;
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    componentBlock: {
      insertComponent: (name: string, props?: Record<string, any>) => ReturnType;
      updateComponentProps: (props: Record<string, any>) => ReturnType;
    };
  }
}

export const ComponentBlock = Node.create<ComponentBlockOptions>({
  name: 'componentBlock',
  group: 'block',
  atom: true,
  draggable: true,

  addOptions() {
    return {
      HTMLAttributes: {},
    };
  },

  addAttributes() {
    return {
      componentName: {
        default: '',
      },
      props: {
        default: {},
        parseHTML: (element) => {
          const propsStr = element.getAttribute('data-props');
          try {
            return propsStr ? JSON.parse(propsStr) : {};
          } catch {
            return {};
          }
        },
        renderHTML: (attributes) => ({
          'data-props': JSON.stringify(attributes.props),
        }),
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-component-block]',
        getAttrs: (element) => {
          if (typeof element === 'string') return false;
          return {
            componentName: element.getAttribute('data-component-name'),
          };
        },
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'div',
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        'data-component-block': '',
        'data-component-name': HTMLAttributes.componentName,
      }),
    ];
  },

  addNodeView() {
    return VueNodeViewRenderer(ComponentBlockView);
  },

  addCommands() {
    return {
      insertComponent:
        (name: string, props: Record<string, any> = {}) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs: { componentName: name, props },
          });
        },
      updateComponentProps:
        (props: Record<string, any>) =>
        ({ commands }) => {
          return commands.updateAttributes(this.name, { props });
        },
    };
  },
});
```

### 4. Component Block View (Vue)

```vue
<!-- admin/components/editor/ComponentBlockView.vue -->
<script setup lang="ts">
/**
 * 组件块视图
 * 在编辑器中渲染实际的 Vue 组件（来自 VitePress）
 */
import { NodeViewWrapper, nodeViewProps } from '@tiptap/vue-3';
import { computed, ref, markRaw } from 'vue';

// 导入共享组件（来自 VitePress）
import DocsQuiz from '@docs-components/Quiz.vue';
import DocsMermaidWrapper from '@docs-components/MermaidWrapper.vue';
import DocsMarkmap from '@docs-components/Markmap.vue';
import DocsCallout from '@docs-components/Callout.vue';

const props = defineProps(nodeViewProps);

// 组件映射
const componentMap: Record<string, any> = {
  Quiz: markRaw(DocsQuiz),
  MermaidWrapper: markRaw(DocsMermaidWrapper),
  Markmap: markRaw(DocsMarkmap),
  Callout: markRaw(DocsCallout),
};

// 组件元数据
const componentMeta: Record<string, { label: string; icon: string }> = {
  Quiz: { label: '选择题', icon: '❓' },
  MermaidWrapper: { label: 'Mermaid 图表', icon: '📊' },
  Markmap: { label: '思维导图', icon: '🧠' },
  Callout: { label: '提示框', icon: '💡' },
};

const isEditing = ref(false);
const isPreview = ref(true); // 默认显示预览

const componentName = computed(() => props.node.attrs.componentName);
const componentProps = computed(() => props.node.attrs.props);
const meta = computed(() => componentMeta[componentName.value]);
const CurrentComponent = computed(() => componentMap[componentName.value]);

// 更新组件属性
const updateProps = (newProps: Record<string, any>) => {
  props.updateAttributes({ props: newProps });
  isEditing.value = false;
};

// 删除组件
const deleteComponent = () => {
  props.deleteNode();
};
</script>

<template>
  <NodeViewWrapper class="component-block" data-drag-handle>
    <!-- 组件头部 -->
    <div class="component-header">
      <div class="flex items-center gap-2">
        <UIcon name="i-lucide-grip-vertical" class="drag-handle cursor-grab" />
        <span class="text-lg">{{ meta?.icon }}</span>
        <span class="font-medium text-sm">{{ meta?.label }}</span>
      </div>

      <div class="flex items-center gap-1">
        <!-- 切换预览/编辑 -->
        <UButton
          :variant="isPreview ? 'solid' : 'ghost'"
          size="xs"
          icon="i-lucide-eye"
          @click="isPreview = true"
        />
        <UButton
          :variant="!isPreview ? 'solid' : 'ghost'"
          size="xs"
          icon="i-lucide-pencil"
          @click="isPreview = false; isEditing = true"
        />
        <UButton
          variant="ghost"
          size="xs"
          color="red"
          icon="i-lucide-trash-2"
          @click="deleteComponent"
        />
      </div>
    </div>

    <!-- 组件内容 -->
    <div class="component-content">
      <!-- 预览模式：直接渲染 Vue 组件 -->
      <div v-if="isPreview && CurrentComponent" class="component-preview">
        <component :is="CurrentComponent" v-bind="componentProps" />
      </div>

      <!-- 编辑模式：显示属性编辑器 -->
      <div v-else class="component-editor">
        <ComponentPropsEditor
          :component-name="componentName"
          :props="componentProps"
          @save="updateProps"
          @cancel="isEditing = false; isPreview = true"
        />
      </div>
    </div>
  </NodeViewWrapper>
</template>

<style scoped>
.component-block {
  @apply my-4 border-2 border-dashed border-primary/30 rounded-lg bg-primary/5;
}

.component-header {
  @apply flex items-center justify-between px-3 py-2 border-b border-primary/20 bg-primary/10;
}

.component-content {
  @apply p-4;
}

.component-preview {
  @apply pointer-events-auto;
}

.drag-handle {
  @apply text-gray-400 hover:text-gray-600;
}
</style>
```

### 5. Quiz Props Editor

```vue
<!-- admin/components/editor/props-editors/QuizPropsEditor.vue -->
<script setup lang="ts">
/**
 * 选择题属性编辑器
 */
import { ref, watch } from 'vue';
import draggable from 'vuedraggable';

interface QuizProps {
  question: string;
  options: string[];
  answer: number;
  explanation?: string;
}

const props = defineProps<{
  modelValue: QuizProps;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: QuizProps];
}>();

// 本地状态
const localValue = ref<QuizProps>({ ...props.modelValue });

// 同步到父组件
watch(localValue, (newValue) => {
  emit('update:modelValue', { ...newValue });
}, { deep: true });

// 添加选项
const addOption = () => {
  localValue.value.options.push('');
};

// 删除选项
const removeOption = (index: number) => {
  if (localValue.value.options.length <= 2) return;
  localValue.value.options.splice(index, 1);
  // 调整正确答案索引
  if (localValue.value.answer >= index && localValue.value.answer > 0) {
    localValue.value.answer--;
  }
};

// 设置正确答案
const setAnswer = (index: number) => {
  localValue.value.answer = index;
};
</script>

<template>
  <div class="space-y-4">
    <!-- 题目 -->
    <UFormGroup label="题目" required>
      <UTextarea
        v-model="localValue.question"
        placeholder="请输入题目内容..."
        :rows="2"
      />
    </UFormGroup>

    <!-- 选项列表 -->
    <UFormGroup label="选项（点击单选按钮设置正确答案）">
      <draggable
        v-model="localValue.options"
        item-key="index"
        handle=".drag-handle"
        class="space-y-2"
      >
        <template #item="{ element, index }">
          <div class="flex items-center gap-2 p-2 border rounded-lg bg-white dark:bg-gray-800">
            <UIcon name="i-lucide-grip-vertical" class="drag-handle cursor-grab text-gray-400" />
            
            <URadio
              :model-value="localValue.answer === index"
              @update:model-value="setAnswer(index)"
            />
            
            <span class="w-6 text-sm font-medium text-gray-500">
              {{ String.fromCharCode(65 + index) }}.
            </span>
            
            <UInput
              v-model="localValue.options[index]"
              :placeholder="`选项 ${String.fromCharCode(65 + index)}`"
              class="flex-1"
            />
            
            <UButton
              variant="ghost"
              size="xs"
              color="red"
              icon="i-lucide-trash-2"
              :disabled="localValue.options.length <= 2"
              @click="removeOption(index)"
            />
          </div>
        </template>
      </draggable>

      <UButton
        variant="outline"
        size="sm"
        icon="i-lucide-plus"
        class="mt-2"
        @click="addOption"
      >
        添加选项
      </UButton>
    </UFormGroup>

    <!-- 答案解析 -->
    <UFormGroup label="答案解析（可选）">
      <UTextarea
        v-model="localValue.explanation"
        placeholder="解释为什么这个答案是正确的..."
        :rows="2"
      />
    </UFormGroup>
  </div>
</template>
```


### 6. Slash Command Extension

```typescript
// admin/components/editor/extensions/SlashCommand.ts
/**
 * Slash Command 扩展
 * 输入 "/" 显示命令菜单
 */
import { Extension } from '@tiptap/core';
import { VueRenderer } from '@tiptap/vue-3';
import tippy, { Instance } from 'tippy.js';
import Suggestion from '@tiptap/suggestion';
import SlashCommandList from '../SlashCommandList.vue';

export interface CommandItem {
  title: string;
  description: string;
  icon: string;
  command: (props: { editor: any; range: any }) => void;
}

const commands: CommandItem[] = [
  {
    title: '标题 1',
    description: '大标题',
    icon: 'i-lucide-heading-1',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).setNode('heading', { level: 1 }).run();
    },
  },
  {
    title: '标题 2',
    description: '中标题',
    icon: 'i-lucide-heading-2',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).setNode('heading', { level: 2 }).run();
    },
  },
  {
    title: '标题 3',
    description: '小标题',
    icon: 'i-lucide-heading-3',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).setNode('heading', { level: 3 }).run();
    },
  },
  {
    title: '无序列表',
    description: '创建无序列表',
    icon: 'i-lucide-list',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).toggleBulletList().run();
    },
  },
  {
    title: '有序列表',
    description: '创建有序列表',
    icon: 'i-lucide-list-ordered',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).toggleOrderedList().run();
    },
  },
  {
    title: '任务列表',
    description: '创建待办事项',
    icon: 'i-lucide-check-square',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).toggleTaskList().run();
    },
  },
  {
    title: '代码块',
    description: '插入代码块',
    icon: 'i-lucide-code',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).toggleCodeBlock().run();
    },
  },
  {
    title: '引用',
    description: '插入引用块',
    icon: 'i-lucide-quote',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).toggleBlockquote().run();
    },
  },
  {
    title: '分割线',
    description: '插入水平分割线',
    icon: 'i-lucide-minus',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).setHorizontalRule().run();
    },
  },
  // 自定义组件
  {
    title: '选择题',
    description: '插入交互式选择题',
    icon: 'i-lucide-help-circle',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).insertComponent('Quiz', {
        question: '',
        options: ['', '', '', ''],
        answer: 0,
      }).run();
    },
  },
  {
    title: 'Mermaid 图表',
    description: '插入流程图、时序图等',
    icon: 'i-lucide-git-branch',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).insertComponent('MermaidWrapper', {
        content: 'graph TD\n  A[开始] --> B[结束]',
      }).run();
    },
  },
  {
    title: '思维导图',
    description: '插入 Markmap 思维导图',
    icon: 'i-lucide-brain',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).insertComponent('Markmap', {
        content: '# 主题\n## 分支1\n## 分支2',
      }).run();
    },
  },
  {
    title: '提示框',
    description: '插入信息提示框',
    icon: 'i-lucide-info',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).insertComponent('Callout', {
        type: 'info',
        content: '提示内容',
      }).run();
    },
  },
];

export const SlashCommand = Extension.create({
  name: 'slashCommand',

  addOptions() {
    return {
      suggestion: {
        char: '/',
        command: ({ editor, range, props }: any) => {
          props.command({ editor, range });
        },
      },
    };
  },

  addProseMirrorPlugins() {
    return [
      Suggestion({
        editor: this.editor,
        ...this.options.suggestion,
        items: ({ query }: { query: string }) => {
          return commands.filter((item) =>
            item.title.toLowerCase().includes(query.toLowerCase()) ||
            item.description.toLowerCase().includes(query.toLowerCase())
          );
        },
        render: () => {
          let component: VueRenderer;
          let popup: Instance[];

          return {
            onStart: (props: any) => {
              component = new VueRenderer(SlashCommandList, {
                props,
                editor: props.editor,
              });

              if (!props.clientRect) return;

              popup = tippy('body', {
                getReferenceClientRect: props.clientRect,
                appendTo: () => document.body,
                content: component.element,
                showOnCreate: true,
                interactive: true,
                trigger: 'manual',
                placement: 'bottom-start',
              });
            },
            onUpdate: (props: any) => {
              component.updateProps(props);
              if (props.clientRect) {
                popup[0].setProps({
                  getReferenceClientRect: props.clientRect,
                });
              }
            },
            onKeyDown: (props: any) => {
              if (props.event.key === 'Escape') {
                popup[0].hide();
                return true;
              }
              return component.ref?.onKeyDown(props);
            },
            onExit: () => {
              popup[0].destroy();
              component.destroy();
            },
          };
        },
      }),
    ];
  },
});
```

```vue
<!-- admin/components/editor/SlashCommandList.vue -->
<script setup lang="ts">
import { ref, watch } from 'vue';

interface CommandItem {
  title: string;
  description: string;
  icon: string;
  command: (props: any) => void;
}

const props = defineProps<{
  items: CommandItem[];
  command: (item: CommandItem) => void;
}>();

const selectedIndex = ref(0);

watch(() => props.items, () => {
  selectedIndex.value = 0;
});

const selectItem = (index: number) => {
  const item = props.items[index];
  if (item) {
    props.command(item);
  }
};

const onKeyDown = ({ event }: { event: KeyboardEvent }) => {
  if (event.key === 'ArrowUp') {
    selectedIndex.value = (selectedIndex.value + props.items.length - 1) % props.items.length;
    return true;
  }
  if (event.key === 'ArrowDown') {
    selectedIndex.value = (selectedIndex.value + 1) % props.items.length;
    return true;
  }
  if (event.key === 'Enter') {
    selectItem(selectedIndex.value);
    return true;
  }
  return false;
};

defineExpose({ onKeyDown });
</script>

<template>
  <div class="slash-command-list">
    <template v-if="items.length">
      <button
        v-for="(item, index) in items"
        :key="index"
        class="slash-command-item"
        :class="{ 'is-selected': index === selectedIndex }"
        @click="selectItem(index)"
        @mouseenter="selectedIndex = index"
      >
        <UIcon :name="item.icon" class="w-5 h-5" />
        <div class="flex-1">
          <div class="font-medium">{{ item.title }}</div>
          <div class="text-xs text-gray-500">{{ item.description }}</div>
        </div>
      </button>
    </template>
    <div v-else class="slash-command-empty">
      没有找到匹配的命令
    </div>
  </div>
</template>

<style scoped>
.slash-command-list {
  @apply bg-white dark:bg-gray-800 border rounded-lg shadow-lg overflow-hidden max-h-80 overflow-y-auto w-72;
}

.slash-command-item {
  @apply flex items-center gap-3 w-full px-3 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700;
}

.slash-command-item.is-selected {
  @apply bg-gray-100 dark:bg-gray-700;
}

.slash-command-empty {
  @apply px-3 py-2 text-gray-500 text-sm;
}
</style>
```


### 7. Markdown Serialization

```typescript
// admin/utils/markdown-serializer.ts
/**
 * Markdown 序列化器
 * 将 Tiptap HTML 转换为 Markdown + Vue 组件语法
 */
import TurndownService from 'turndown';
import { gfm } from 'turndown-plugin-gfm';

const turndownService = new TurndownService({
  headingStyle: 'atx',
  codeBlockStyle: 'fenced',
  bulletListMarker: '-',
});

// 添加 GFM 支持（表格、任务列表等）
turndownService.use(gfm);

// 自定义组件块规则
turndownService.addRule('componentBlock', {
  filter: (node) => {
    return node.nodeName === 'DIV' && node.hasAttribute('data-component-block');
  },
  replacement: (content, node) => {
    const element = node as HTMLElement;
    const componentName = element.getAttribute('data-component-name');
    const propsStr = element.getAttribute('data-props');
    
    if (!componentName) return '';
    
    try {
      const props = propsStr ? JSON.parse(propsStr) : {};
      return serializeComponent(componentName, props);
    } catch {
      return '';
    }
  },
});

// 组件序列化
function serializeComponent(name: string, props: Record<string, any>): string {
  switch (name) {
    case 'Quiz':
      return serializeQuiz(props);
    case 'MermaidWrapper':
      return serializeMermaid(props);
    case 'Markmap':
      return serializeMarkmap(props);
    case 'Callout':
      return serializeCallout(props);
    default:
      return serializeGeneric(name, props);
  }
}

function serializeQuiz(props: {
  question: string;
  options: string[];
  answer: number;
  explanation?: string;
}): string {
  const lines = [
    '',
    '<Quiz',
    `  question="${escapeAttr(props.question)}"`,
    `  :options='${JSON.stringify(props.options)}'`,
    `  :answer="${props.answer}"`,
  ];
  if (props.explanation) {
    lines.push(`  explanation="${escapeAttr(props.explanation)}"`);
  }
  lines.push('/>');
  lines.push('');
  return lines.join('\n');
}

function serializeMermaid(props: { content: string; title?: string }): string {
  const info = props.title ? `mermaid-box{title="${props.title}"}` : 'mermaid';
  return `\n\`\`\`${info}\n${props.content}\n\`\`\`\n`;
}

function serializeMarkmap(props: { content: string }): string {
  return `\n\`\`\`markmap\n${props.content}\n\`\`\`\n`;
}

function serializeCallout(props: { type: string; title?: string; content: string }): string {
  const header = props.title ? `${props.type} ${props.title}` : props.type;
  return `\n::: ${header}\n${props.content}\n:::\n`;
}

function serializeGeneric(name: string, props: Record<string, any>): string {
  const propsStr = Object.entries(props)
    .map(([key, value]) => {
      if (typeof value === 'string') {
        return `${key}="${escapeAttr(value)}"`;
      }
      return `:${key}='${JSON.stringify(value)}'`;
    })
    .join('\n  ');
  return `\n<${name}\n  ${propsStr}\n/>\n`;
}

function escapeAttr(str: string): string {
  return str.replace(/"/g, '&quot;').replace(/\n/g, '\\n');
}

// 导出函数
export function htmlToMarkdown(html: string): string {
  return turndownService.turndown(html);
}

export function markdownToHtml(markdown: string): string {
  // 使用 marked 或其他库将 Markdown 转换为 HTML
  // 这里简化处理，实际需要处理 Vue 组件语法
  // ...
  return markdown;
}
```

### 8. Edit Lock Composable

```typescript
// admin/composables/useEditLock.ts
/**
 * 编辑锁 Composable
 * 管理文档编辑锁的获取、续期和释放
 */
export function useEditLock(documentId: MaybeRef<string>) {
  const docId = toRef(documentId);
  
  const hasLock = ref(false);
  const isLocked = ref(false);
  const lockHolder = ref<{ id: string; name: string; avatar: string } | null>(null);
  const isAcquiring = ref(false);

  // 获取锁
  const acquireLock = async () => {
    isAcquiring.value = true;
    try {
      const { data, error } = await useFetch(`/api/documents/${docId.value}/lock`, {
        method: 'POST',
      });

      if (error.value) throw error.value;

      if (data.value?.success) {
        hasLock.value = true;
        isLocked.value = false;
        lockHolder.value = null;
      } else {
        hasLock.value = false;
        isLocked.value = true;
        lockHolder.value = data.value?.holder || null;
      }

      return data.value?.success || false;
    } catch (e) {
      console.error('Failed to acquire lock:', e);
      return false;
    } finally {
      isAcquiring.value = false;
    }
  };

  // 释放锁
  const releaseLock = async () => {
    if (!hasLock.value) return;

    try {
      await $fetch(`/api/documents/${docId.value}/lock`, {
        method: 'DELETE',
      });
      hasLock.value = false;
    } catch (e) {
      console.error('Failed to release lock:', e);
    }
  };

  // 续期锁（心跳）
  const renewLock = async () => {
    if (!hasLock.value) return;

    try {
      await $fetch(`/api/documents/${docId.value}/lock`, {
        method: 'PATCH',
      });
    } catch (e) {
      console.error('Failed to renew lock:', e);
      hasLock.value = false;
    }
  };

  // 心跳定时器（每 2 分钟续期）
  let heartbeatInterval: ReturnType<typeof setInterval> | null = null;

  const startHeartbeat = () => {
    if (heartbeatInterval) return;
    heartbeatInterval = setInterval(renewLock, 2 * 60 * 1000);
  };

  const stopHeartbeat = () => {
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval);
      heartbeatInterval = null;
    }
  };

  // 监听锁状态
  watch(hasLock, (newValue) => {
    if (newValue) {
      startHeartbeat();
    } else {
      stopHeartbeat();
    }
  });

  // 页面卸载时释放锁
  onBeforeUnmount(() => {
    stopHeartbeat();
    if (hasLock.value) {
      // 使用 sendBeacon 确保请求发送
      navigator.sendBeacon(`/api/documents/${docId.value}/lock/release`);
    }
  });

  // 页面可见性变化时处理
  useEventListener(document, 'visibilitychange', () => {
    if (document.visibilityState === 'hidden' && hasLock.value) {
      // 页面隐藏时释放锁
      releaseLock();
    }
  });

  return {
    hasLock: readonly(hasLock),
    isLocked: readonly(isLocked),
    lockHolder: readonly(lockHolder),
    isAcquiring: readonly(isAcquiring),
    acquireLock,
    releaseLock,
  };
}
```

### 9. AI Translation Composable

```typescript
// admin/composables/useTranslation.ts
/**
 * AI 翻译 Composable
 * 使用 Vercel AI SDK 实现流式翻译
 */
import { useCompletion } from '@ai-sdk/vue';

interface TranslationOptions {
  onComplete?: (result: string) => void;
  onError?: (error: Error) => void;
}

export function useTranslation(options: TranslationOptions = {}) {
  const {
    completion,
    complete,
    isLoading,
    error,
    stop,
  } = useCompletion({
    api: '/api/translate',
    onFinish: (prompt, completion) => {
      options.onComplete?.(completion);
    },
    onError: (error) => {
      options.onError?.(error);
    },
  });

  const translate = async (params: {
    documentId: string;
    content: string;
    sourceLocale: string;
    targetLocale: string;
  }) => {
    await complete('', {
      body: params,
    });
  };

  return {
    translation: completion,
    isTranslating: isLoading,
    error,
    translate,
    stop,
  };
}
```

```typescript
// admin/server/api/translate.post.ts
/**
 * AI 翻译 API
 * 流式返回翻译结果
 */
import { streamText } from 'ai';
import { openai } from '@ai-sdk/openai';

const LANGUAGE_NAMES: Record<string, string> = {
  zh: '中文',
  en: 'English',
  vi: 'Tiếng Việt',
  ja: '日本語',
};

export default defineEventHandler(async (event) => {
  const session = await requireUserSession(event);
  const body = await readBody(event);
  const { content, sourceLocale, targetLocale } = body;

  const config = useRuntimeConfig();

  const systemPrompt = `你是一个专业的技术文档翻译专家。请将以下${LANGUAGE_NAMES[sourceLocale]}文档翻译成${LANGUAGE_NAMES[targetLocale]}。

翻译要求：
1. 保持 Markdown 格式不变
2. 代码块内容不翻译
3. Vue 组件标签和属性不翻译
4. 保持专业术语的准确性
5. 保持原文的语气和风格
6. 链接和图片路径保持不变`;

  const result = await streamText({
    model: openai('gpt-4o', { apiKey: config.openaiApiKey }),
    system: systemPrompt,
    prompt: content,
  });

  return result.toDataStreamResponse();
});
```


### 10. Git Publishing Service

```typescript
// admin/server/utils/git.ts
/**
 * Git 发布服务
 * 将文档发布到 VitePress docs 目录
 */
import simpleGit, { SimpleGit } from 'simple-git';
import { promises as fs } from 'fs';
import path from 'path';

export class GitService {
  private git: SimpleGit;
  private docsRoot: string;

  constructor() {
    const config = useRuntimeConfig();
    this.docsRoot = path.resolve(config.docsRoot);
    this.git = simpleGit(this.docsRoot);
  }

  // 发布单个文档
  async publishDocument(params: {
    slug: string;
    locale: string;
    content: string;
    title: string;
    categoryPath?: string;
    authorName: string;
    authorEmail: string;
  }): Promise<{ success: boolean; commitHash?: string; error?: string }> {
    const { slug, locale, content, title, categoryPath, authorName, authorEmail } = params;

    // 构建文件路径: docs/{locale}/{categoryPath}/{slug}.md
    const relativePath = categoryPath
      ? path.join(locale, categoryPath, `${slug}.md`)
      : path.join(locale, `${slug}.md`);
    const filePath = path.join(this.docsRoot, relativePath);

    try {
      // 确保目录存在
      await fs.mkdir(path.dirname(filePath), { recursive: true });

      // 添加 frontmatter
      const fileContent = `---
title: ${title}
---

${content}`;

      // 写入文件
      await fs.writeFile(filePath, fileContent, 'utf-8');

      // Git 操作
      await this.git.add(relativePath);

      const commitMessage = `docs(${locale}): update ${slug}`;
      const commit = await this.git.commit(commitMessage, relativePath, {
        '--author': `${authorName} <${authorEmail}>`,
      });

      return {
        success: true,
        commitHash: commit.commit,
      };
    } catch (error) {
      console.error('Git publish error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  // 批量发布
  async publishBatch(
    documents: Array<{
      slug: string;
      locale: string;
      content: string;
      title: string;
      categoryPath?: string;
    }>,
    author: { name: string; email: string }
  ): Promise<{ success: boolean; commitHash?: string; error?: string }> {
    try {
      const files: string[] = [];

      for (const doc of documents) {
        const relativePath = doc.categoryPath
          ? path.join(doc.locale, doc.categoryPath, `${doc.slug}.md`)
          : path.join(doc.locale, `${doc.slug}.md`);
        const filePath = path.join(this.docsRoot, relativePath);

        await fs.mkdir(path.dirname(filePath), { recursive: true });

        const fileContent = `---
title: ${doc.title}
---

${doc.content}`;

        await fs.writeFile(filePath, fileContent, 'utf-8');
        files.push(relativePath);
      }

      await this.git.add(files);

      const commitMessage = `docs: batch update ${documents.length} documents`;
      const commit = await this.git.commit(commitMessage, files, {
        '--author': `${author.name} <${author.email}>`,
      });

      return {
        success: true,
        commitHash: commit.commit,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  // 获取同步状态
  async getSyncStatus(): Promise<'synced' | 'ahead' | 'behind' | 'diverged'> {
    try {
      await this.git.fetch();
      const status = await this.git.status();

      if (status.ahead > 0 && status.behind > 0) return 'diverged';
      if (status.ahead > 0) return 'ahead';
      if (status.behind > 0) return 'behind';
      return 'synced';
    } catch {
      return 'synced';
    }
  }

  // 推送到远程
  async push(): Promise<boolean> {
    try {
      await this.git.push();
      return true;
    } catch {
      return false;
    }
  }
}

// 单例
let gitService: GitService | null = null;

export function useGitService(): GitService {
  if (!gitService) {
    gitService = new GitService();
  }
  return gitService;
}
```

## API Routes Design

### RESTful API Structure

```
/api
├── /auth
│   ├── /dingtalk           # GET: 钉钉 OAuth 回调
│   ├── /logout             # POST: 登出
│   └── /session            # GET: 获取当前会话
├── /locales
│   ├── GET                 # 获取所有语言列表
│   ├── POST                # 添加新语言 (admin only)
│   ├── /[id]
│   │   ├── PATCH           # 更新语言配置
│   │   └── DELETE          # 删除语言
│   └── /reorder            # POST: 重新排序
├── /nav-menus
│   ├── GET                 # 获取菜单树
│   ├── POST                # 创建菜单项
│   ├── /[id]
│   │   ├── GET             # 获取菜单项详情
│   │   ├── PATCH           # 更新菜单项
│   │   └── DELETE          # 删除菜单项
│   ├── /reorder            # POST: 重新排序
│   └── /publish            # POST: 发布到 VitePress
├── /categories
│   ├── GET                 # 获取栏目树
│   ├── POST                # 创建栏目
│   ├── /[id]
│   │   ├── GET             # 获取栏目详情
│   │   ├── PATCH           # 更新栏目
│   │   └── DELETE          # 删除栏目
│   └── /reorder            # POST: 重新排序
├── /documents
│   ├── GET                 # 获取文档列表
│   ├── POST                # 创建文档
│   ├── /[id]
│   │   ├── GET             # 获取文档详情
│   │   ├── PATCH           # 更新文档
│   │   ├── DELETE          # 删除文档
│   │   ├── /versions       # GET: 获取版本历史
│   │   ├── /publish        # POST: 发布文档
│   │   └── /lock
│   │       ├── POST        # 获取编辑锁
│   │       ├── PATCH       # 续期锁
│   │       ├── DELETE      # 释放锁
│   │       └── /release    # POST: Beacon 释放锁
│   └── /search             # GET: 搜索文档
├── /translate              # POST: AI 翻译（流式）
├── /publish
│   └── /batch              # POST: 批量发布
└── /users
    ├── GET                 # 获取用户列表
    └── /[id]
        └── PATCH           # 更新用户角色
```

## UI Layout Design

```
┌─────────────────────────────────────────────────────────────────┐
│  AppHeader (h-14)                                               │
│  ┌──────┐ ┌──────────────────────────────┐ ┌──────────────────┐│
│  │ Logo │ │ Breadcrumb                   │ │ User + Actions   ││
│  └──────┘ └──────────────────────────────┘ └──────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐ ┌───────────────────────────────────────────┐ │
│  │  Sidebar    │ │  Main Content                             │ │
│  │  (w-64)     │ │                                           │ │
│  │             │ │  ┌─────────────────────────────────────┐  │ │
│  │  ┌────────┐ │ │  │  EditorToolbar                     │  │ │
│  │  │FileTree│ │ │  ├─────────────────────────────────────┤  │ │
│  │  │        │ │ │  │                                     │  │ │
│  │  │ 📁 zh  │ │ │  │  DocumentEditor (Tiptap)            │  │ │
│  │  │ 📁 en  │ │ │  │  - 直接渲染 Quiz.vue 等组件         │  │ │
│  │  │ 📁 vi  │ │ │  │  - Slash Command 插入组件           │  │ │
│  │  │        │ │ │  │  - 所见即所得                       │  │ │
│  │  └────────┘ │ │  │                                     │  │ │
│  │             │ │  └─────────────────────────────────────┘  │ │
│  │  ┌────────┐ │ │                                           │ │
│  │  │+ 新建  │ │ │  ┌─────────────────────────────────────┐  │ │
│  │  │⚙ 设置 │ │ │  │  StatusBar (sync, lock, collaborators)│ │
│  │  └────────┘ │ │  └─────────────────────────────────────┘  │ │
│  └─────────────┘ └───────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Nuxt Auth
NUXT_SESSION_PASSWORD=your-32-char-secret

# DingTalk OAuth
DINGTALK_APP_KEY=your-app-key
DINGTALK_APP_SECRET=your-app-secret
DINGTALK_AGENT_ID=your-agent-id
DINGTALK_CORP_ID=your-corp-id

# AI Translation
OPENAI_API_KEY=your-openai-key

# Git/Docs
DOCS_ROOT=../docs
```

## Security Considerations

1. **Authentication**: 所有 API 路由需验证 session（使用 `requireUserSession`）
2. **Authorization**: 基于角色的访问控制 (admin/editor/viewer)
3. **Input Validation**: 使用 Zod 验证所有输入
4. **Rate Limiting**: 使用 Nuxt Rate Limit 模块
5. **CSRF Protection**: nuxt-auth-utils 内置 CSRF 保护
6. **XSS Prevention**: Vue 自动转义 + DOMPurify 处理富文本

## Performance Optimizations

1. **Database**: 添加适当索引，使用连接池
2. **Caching**: Nuxt 内置缓存 + Redis 缓存热点数据
3. **Code Splitting**: Nuxt 自动代码分割
4. **Image Optimization**: Nuxt Image 模块
5. **Streaming**: AI 翻译使用流式响应

## Key Benefits of Nuxt 3 + Vue Unified Stack

| 特性 | 说明 |
|------|------|
| **组件复用** | VitePress 的 Quiz.vue 等组件直接在 Admin 中使用 |
| **编辑即所见** | Tiptap 编辑器直接渲染 Vue 组件，无需 iframe |
| **统一技术栈** | Vue 3 + TypeScript 全栈，降低学习和维护成本 |
| **Nuxt 特性** | 自动导入、文件路由、Server API、SEO 优化 |
| **Nuxt UI** | 基于 Radix Vue 的精致组件库，与 shadcn/ui 风格一致 |
| **VueUse** | 丰富的 Composition API 工具函数 |


## File Upload (MinIO)

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Document Editor                               │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  拖拽上传 / 粘贴 / 点击上传                                  ││
│  │  支持: 图片 (jpg, png, gif, webp, svg)                       ││
│  │        视频 (mp4, webm, mov)                                 ││
│  │        文件 (pdf, zip, etc.)                                 ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Nuxt Server API                               │
│  POST /api/upload                                                │
│  - 验证文件类型和大小                                            │
│  - 生成唯一文件名                                                │
│  - 上传到 MinIO                                                  │
│  - 返回访问 URL                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MinIO Object Storage                          │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │  Bucket: docs    │  │  Bucket: temp    │                     │
│  │  /images/        │  │  (临时上传)       │                     │
│  │  /videos/        │  │                  │                     │
│  │  /files/         │  │                  │                     │
│  └──────────────────┘  └──────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

### MinIO Configuration

```typescript
// admin/server/utils/minio.ts
/**
 * MinIO 客户端配置
 */
import { Client } from 'minio';

let minioClient: Client | null = null;

export function useMinioClient(): Client {
  if (!minioClient) {
    const config = useRuntimeConfig();
    
    minioClient = new Client({
      endPoint: config.minioEndpoint,
      port: parseInt(config.minioPort),
      useSSL: config.minioUseSSL === 'true',
      accessKey: config.minioAccessKey,
      secretKey: config.minioSecretKey,
    });
  }
  
  return minioClient;
}

// Bucket 名称
export const BUCKETS = {
  DOCS: 'forcome-docs',      // 正式文件
  TEMP: 'forcome-docs-temp', // 临时上传
} as const;

// 文件类型配置
export const FILE_CONFIG = {
  image: {
    maxSize: 10 * 1024 * 1024, // 10MB
    mimeTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'],
    extensions: ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'],
    folder: 'images',
  },
  video: {
    maxSize: 100 * 1024 * 1024, // 100MB
    mimeTypes: ['video/mp4', 'video/webm', 'video/quicktime'],
    extensions: ['.mp4', '.webm', '.mov'],
    folder: 'videos',
  },
  file: {
    maxSize: 50 * 1024 * 1024, // 50MB
    mimeTypes: ['application/pdf', 'application/zip', 'application/x-rar-compressed'],
    extensions: ['.pdf', '.zip', '.rar'],
    folder: 'files',
  },
} as const;

export type FileType = keyof typeof FILE_CONFIG;
```

### Upload API

```typescript
// admin/server/api/upload.post.ts
/**
 * 文件上传 API
 * 支持图片、视频、文件上传到 MinIO
 */
import { randomUUID } from 'crypto';
import path from 'path';
import { useMinioClient, BUCKETS, FILE_CONFIG, type FileType } from '../utils/minio';

export default defineEventHandler(async (event) => {
  // 验证登录
  const session = await requireUserSession(event);
  
  // 解析 multipart 表单
  const formData = await readMultipartFormData(event);
  if (!formData || formData.length === 0) {
    throw createError({ statusCode: 400, message: '没有上传文件' });
  }

  const file = formData.find(f => f.name === 'file');
  if (!file || !file.data || !file.filename) {
    throw createError({ statusCode: 400, message: '文件无效' });
  }

  // 获取文件类型
  const fileType = getFileType(file.type || '', file.filename);
  if (!fileType) {
    throw createError({ statusCode: 400, message: '不支持的文件类型' });
  }

  const config = FILE_CONFIG[fileType];

  // 验证文件大小
  if (file.data.length > config.maxSize) {
    throw createError({
      statusCode: 400,
      message: `文件大小超过限制 (最大 ${config.maxSize / 1024 / 1024}MB)`,
    });
  }

  // 生成唯一文件名
  const ext = path.extname(file.filename).toLowerCase();
  const uniqueName = `${randomUUID()}${ext}`;
  const objectName = `${config.folder}/${uniqueName}`;

  try {
    const minio = useMinioClient();
    const runtimeConfig = useRuntimeConfig();

    // 上传到 MinIO
    await minio.putObject(
      BUCKETS.DOCS,
      objectName,
      file.data,
      file.data.length,
      {
        'Content-Type': file.type || 'application/octet-stream',
        'x-amz-meta-original-name': encodeURIComponent(file.filename),
        'x-amz-meta-uploaded-by': session.user.id,
        'x-amz-meta-uploaded-at': new Date().toISOString(),
      }
    );

    // 构建访问 URL
    const baseUrl = runtimeConfig.public.minioPublicUrl || 
      `${runtimeConfig.minioUseSSL === 'true' ? 'https' : 'http'}://${runtimeConfig.minioEndpoint}:${runtimeConfig.minioPort}`;
    const url = `${baseUrl}/${BUCKETS.DOCS}/${objectName}`;

    return {
      success: true,
      url,
      name: file.filename,
      size: file.data.length,
      type: fileType,
      mimeType: file.type,
    };
  } catch (error) {
    console.error('MinIO upload error:', error);
    throw createError({ statusCode: 500, message: '文件上传失败' });
  }
});

// 判断文件类型
function getFileType(mimeType: string, filename: string): FileType | null {
  const ext = path.extname(filename).toLowerCase();

  for (const [type, config] of Object.entries(FILE_CONFIG)) {
    if (config.mimeTypes.includes(mimeType) || config.extensions.includes(ext)) {
      return type as FileType;
    }
  }

  return null;
}
```

### Tiptap Image Extension (Enhanced)

```typescript
// admin/components/editor/extensions/ImageUpload.ts
/**
 * 增强的图片扩展
 * 支持拖拽、粘贴、点击上传
 */
import Image from '@tiptap/extension-image';
import { Plugin, PluginKey } from '@tiptap/pm/state';

export interface ImageUploadOptions {
  uploadFn: (file: File) => Promise<string>;
  maxSize?: number;
  allowedTypes?: string[];
}

export const ImageUpload = Image.extend<ImageUploadOptions>({
  addOptions() {
    return {
      ...this.parent?.(),
      uploadFn: async () => '',
      maxSize: 10 * 1024 * 1024,
      allowedTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'],
    };
  },

  addProseMirrorPlugins() {
    const { uploadFn, maxSize, allowedTypes } = this.options;

    return [
      new Plugin({
        key: new PluginKey('imageUpload'),
        props: {
          // 处理拖拽
          handleDrop: (view, event, slice, moved) => {
            if (moved || !event.dataTransfer?.files.length) {
              return false;
            }

            const files = Array.from(event.dataTransfer.files).filter(
              (file) => allowedTypes?.includes(file.type) && file.size <= (maxSize || Infinity)
            );

            if (files.length === 0) return false;

            event.preventDefault();

            const { schema } = view.state;
            const coordinates = view.posAtCoords({
              left: event.clientX,
              top: event.clientY,
            });

            files.forEach(async (file) => {
              try {
                const url = await uploadFn(file);
                const node = schema.nodes.image.create({ src: url, alt: file.name });
                const transaction = view.state.tr.insert(coordinates?.pos || 0, node);
                view.dispatch(transaction);
              } catch (error) {
                console.error('Image upload failed:', error);
              }
            });

            return true;
          },

          // 处理粘贴
          handlePaste: (view, event) => {
            const items = Array.from(event.clipboardData?.items || []);
            const imageItems = items.filter((item) => item.type.startsWith('image/'));

            if (imageItems.length === 0) return false;

            event.preventDefault();

            imageItems.forEach(async (item) => {
              const file = item.getAsFile();
              if (!file || file.size > (maxSize || Infinity)) return;

              try {
                const url = await uploadFn(file);
                const { schema } = view.state;
                const node = schema.nodes.image.create({ src: url, alt: 'Pasted image' });
                const transaction = view.state.tr.replaceSelectionWith(node);
                view.dispatch(transaction);
              } catch (error) {
                console.error('Image paste upload failed:', error);
              }
            });

            return true;
          },
        },
      }),
    ];
  },
});
```

### Video Extension

```typescript
// admin/components/editor/extensions/Video.ts
/**
 * 视频扩展
 * 支持上传和嵌入视频
 */
import { Node, mergeAttributes } from '@tiptap/core';
import { VueNodeViewRenderer } from '@tiptap/vue-3';
import VideoView from '../VideoView.vue';

export interface VideoOptions {
  HTMLAttributes: Record<string, any>;
  uploadFn: (file: File) => Promise<string>;
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    video: {
      setVideo: (options: { src: string; title?: string }) => ReturnType;
    };
  }
}

export const Video = Node.create<VideoOptions>({
  name: 'video',
  group: 'block',
  atom: true,
  draggable: true,

  addOptions() {
    return {
      HTMLAttributes: {},
      uploadFn: async () => '',
    };
  },

  addAttributes() {
    return {
      src: { default: null },
      title: { default: null },
      width: { default: '100%' },
      height: { default: 'auto' },
    };
  },

  parseHTML() {
    return [{ tag: 'video' }];
  },

  renderHTML({ HTMLAttributes }) {
    return ['video', mergeAttributes(this.options.HTMLAttributes, HTMLAttributes)];
  },

  addNodeView() {
    return VueNodeViewRenderer(VideoView);
  },

  addCommands() {
    return {
      setVideo:
        (options) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs: options,
          });
        },
    };
  },
});
```

```vue
<!-- admin/components/editor/VideoView.vue -->
<script setup lang="ts">
import { NodeViewWrapper, nodeViewProps } from '@tiptap/vue-3';
import { computed } from 'vue';

const props = defineProps(nodeViewProps);

const src = computed(() => props.node.attrs.src);
const title = computed(() => props.node.attrs.title);
</script>

<template>
  <NodeViewWrapper class="video-wrapper" data-drag-handle>
    <div class="video-container">
      <video
        :src="src"
        :title="title"
        controls
        preload="metadata"
        class="w-full rounded-lg"
      >
        您的浏览器不支持视频播放
      </video>
      <div v-if="title" class="video-title">{{ title }}</div>
    </div>
    
    <!-- 删除按钮 -->
    <button
      class="delete-btn"
      @click="deleteNode"
      title="删除视频"
    >
      <UIcon name="i-lucide-trash-2" />
    </button>
  </NodeViewWrapper>
</template>

<style scoped>
.video-wrapper {
  @apply relative my-4;
}

.video-container {
  @apply border rounded-lg overflow-hidden bg-black;
}

.video-title {
  @apply text-sm text-gray-500 mt-2 text-center;
}

.delete-btn {
  @apply absolute top-2 right-2 p-1.5 rounded bg-black/50 text-white opacity-0 transition-opacity;
}

.video-wrapper:hover .delete-btn {
  @apply opacity-100;
}
</style>
```

### Upload Composable

```typescript
// admin/composables/useUpload.ts
/**
 * 文件上传 Composable
 */
export function useUpload() {
  const isUploading = ref(false);
  const progress = ref(0);
  const error = ref<string | null>(null);

  const upload = async (file: File): Promise<string> => {
    isUploading.value = true;
    progress.value = 0;
    error.value = null;

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await $fetch<{
        success: boolean;
        url: string;
        error?: string;
      }>('/api/upload', {
        method: 'POST',
        body: formData,
        onUploadProgress: (event) => {
          if (event.total) {
            progress.value = Math.round((event.loaded / event.total) * 100);
          }
        },
      });

      if (!response.success) {
        throw new Error(response.error || '上传失败');
      }

      return response.url;
    } catch (e) {
      error.value = e instanceof Error ? e.message : '上传失败';
      throw e;
    } finally {
      isUploading.value = false;
    }
  };

  // 上传图片
  const uploadImage = async (file: File): Promise<string> => {
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'];
    if (!allowedTypes.includes(file.type)) {
      throw new Error('不支持的图片格式');
    }
    return upload(file);
  };

  // 上传视频
  const uploadVideo = async (file: File): Promise<string> => {
    const allowedTypes = ['video/mp4', 'video/webm', 'video/quicktime'];
    if (!allowedTypes.includes(file.type)) {
      throw new Error('不支持的视频格式');
    }
    return upload(file);
  };

  return {
    upload,
    uploadImage,
    uploadVideo,
    isUploading: readonly(isUploading),
    progress: readonly(progress),
    error: readonly(error),
  };
}
```

### Editor Integration

```vue
<!-- admin/components/editor/DocumentEditor.vue (更新) -->
<script setup lang="ts">
// ... 其他导入

// 文件上传
import { ImageUpload } from './extensions/ImageUpload';
import { Video } from './extensions/Video';

const { uploadImage, uploadVideo } = useUpload();

const editor = useEditor({
  extensions: [
    // ... 其他扩展
    
    // 图片上传（替换默认 Image）
    ImageUpload.configure({
      uploadFn: uploadImage,
      maxSize: 10 * 1024 * 1024,
    }),
    
    // 视频
    Video.configure({
      uploadFn: uploadVideo,
    }),
  ],
  // ...
});

// Slash Command 中添加图片和视频选项
const commands = [
  // ... 其他命令
  {
    title: '图片',
    description: '上传或插入图片',
    icon: 'i-lucide-image',
    command: ({ editor }) => {
      // 打开文件选择器
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.onchange = async (e) => {
        const file = (e.target as HTMLInputElement).files?.[0];
        if (file) {
          const url = await uploadImage(file);
          editor.chain().focus().setImage({ src: url }).run();
        }
      };
      input.click();
    },
  },
  {
    title: '视频',
    description: '上传视频文件',
    icon: 'i-lucide-video',
    command: ({ editor }) => {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'video/*';
      input.onchange = async (e) => {
        const file = (e.target as HTMLInputElement).files?.[0];
        if (file) {
          const url = await uploadVideo(file);
          editor.chain().focus().setVideo({ src: url, title: file.name }).run();
        }
      };
      input.click();
    },
  },
];
</script>
```

### Environment Variables (Updated)

```bash
# MinIO Configuration
MINIO_ENDPOINT=minio.example.com
MINIO_PORT=9000
MINIO_USE_SSL=true
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_PUBLIC_URL=https://cdn.example.com  # CDN 或公开访问地址
```

### Nuxt Config (Updated)

```typescript
// admin/nuxt.config.ts
export default defineNuxtConfig({
  // ...
  
  runtimeConfig: {
    // MinIO (服务端私有)
    minioEndpoint: process.env.MINIO_ENDPOINT,
    minioPort: process.env.MINIO_PORT || '9000',
    minioUseSSL: process.env.MINIO_USE_SSL || 'false',
    minioAccessKey: process.env.MINIO_ACCESS_KEY,
    minioSecretKey: process.env.MINIO_SECRET_KEY,
    
    // 其他配置...
    
    public: {
      minioPublicUrl: process.env.MINIO_PUBLIC_URL,
      // ...
    },
  },
});
```

### File Upload Summary

| 功能 | 支持格式 | 大小限制 |
|------|----------|----------|
| 图片上传 | jpg, png, gif, webp, svg | 10MB |
| 视频上传 | mp4, webm, mov | 100MB |
| 文件上传 | pdf, zip, rar | 50MB |

| 上传方式 | 说明 |
|----------|------|
| 拖拽上传 | 直接拖拽文件到编辑器 |
| 粘贴上传 | Ctrl+V 粘贴剪贴板图片 |
| 点击上传 | Slash Command `/图片` `/视频` |
| 工具栏上传 | 点击工具栏图片/视频按钮 |
