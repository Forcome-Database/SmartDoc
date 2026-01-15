# Project Structure

```
project-root/
├── docs/                          # VitePress 文档站点
│   ├── .vitepress/
│   │   ├── config.ts
│   │   └── theme/
│   │       ├── components/        # 🔗 可共享组件
│   │       ├── composables/
│   │       └── styles/
│   ├── zh/ en/ vi/                # 多语言内容
│   └── public/
│
├── admin/                         # Nuxt 3 后台系统
│   ├── pages/
│   │   ├── index.vue              # Dashboard
│   │   ├── login.vue              # 钉钉登录
│   │   ├── documents/[id].vue     # 文档编辑
│   │   ├── categories/            # 栏目管理
│   │   ├── nav-menus/             # 导航菜单
│   │   └── settings/              # 系统设置
│   ├── components/
│   │   ├── editor/                # md-editor-v3 编辑器
│   │   ├── content-tree/          # 内容树组件
│   │   ├── file-tree/             # 文件树
│   │   └── layout/                # 布局组件
│   ├── composables/               # useEditLock, useTranslation...
│   ├── stores/                    # Pinia stores
│   ├── server/
│   │   ├── api/                   # Server API routes
│   │   └── utils/                 # db.ts, git.ts, dingtalk.ts
│   └── types/
│
├── shared/                        # 共享代码
│   ├── schema/                    # Drizzle Schema
│   └── types/
│
├── drizzle/                       # 数据库迁移
├── drizzle.config.ts
└── pnpm-workspace.yaml
```

## Key Patterns

- **Composables**: `use*` 命名，状态逻辑封装
- **Shared Schema**: `shared/schema/` 定义数据库表结构
- **Component Sharing**: Admin 可引用 `docs/.vitepress/theme/components/`
- **Server API**: Nuxt Server Routes 处理后端逻辑
