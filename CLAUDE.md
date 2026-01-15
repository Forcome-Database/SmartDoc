# FORCOME 知识库平台

Monorepo: VitePress 文档站点 + Nuxt 3 后台管理系统

## 关键文件

```
shared/types/index.ts      # 所有类型定义 (单一来源)
admin/server/middleware/auth.ts  # API 认证中间件
admin/server/utils/api-response.ts  # API 响应工具
admin/server/utils/permissions.ts   # 权限检查工具
admin/nuxt.config.ts       # Nuxt 配置
admin/app.config.ts        # 运行时配置 (图标等)
shared/schema/index.ts     # 数据库 Schema
```

## 技术栈

- **docs/**: VitePress 2.0, TailwindCSS 4
- **admin/**: Nuxt 3.14, @nuxt/ui 3.0, Pinia, Drizzle ORM
- **数据库**: PostgreSQL, MinIO
- **认证**: 钉钉 OAuth

## 命令

```bash
pnpm admin:dev    # 后台 :3000
pnpm docs:dev     # 文档 :5173
pnpm db:generate  # 生成迁移
pnpm db:migrate   # 执行迁移
```

## 规则

### 必须
- 类型定义放在 `shared/types/index.ts`
- API 使用 `requireAuth(event)` 验证登录
- 权限检查使用 `requireDocumentPermission()`
- 新增公开 API 路径需更新 `auth.ts` 的 `publicPaths`

### 禁止
- 在 admin/types 重复定义类型
- 创建空文件
- 在 composables 中重复导出相同函数
- 硬编码敏感信息

## 常见错误

| 错误 | 解决方案 |
|------|----------|
| 图标 401 | auth.ts 添加路径到 publicPaths |
| 图标 Invalid data | app.config.ts 设置 `icon.cssLayer: 'base'` |
| 重复导出警告 | 统一到 shared/types，删除重复文件 |
| 组件未找到 | 检查 components 目录结构和自动导入前缀 |
| API 401 未登录 | 检查 session 配置和 cookie |

## 图标配置

```typescript
// app.config.ts (TailwindCSS v4 必需)
icon: { mode: 'css', cssLayer: 'base' }

// nuxt.config.ts
icon: {
  serverBundle: { collections: ['lucide', 'simple-icons'] },
  clientBundle: { scan: true }
}
```

## 文档维护

**解决问题后立即更新本文件：**
- 新错误添加到「常见错误」表格
- 保持一行问题一行方案
- 不重复记录

## 外部依赖文档查阅

使用不熟悉的库或 API 前，按优先级查阅文档：
1. **Context7** - `resolve-library-id` → `query-docs` (首选)
2. **专用 MCP** - 钉钉用 `dingtalk-api` MCP
3. **WebFetch** - 爬取官方文档 (兜底)
