# Tasks - FORCOME 知识库后台管理系统

## Phase 1: 项目初始化与基础架构

### Task 1.1: Monorepo 项目结构搭建
- [ ] 创建 `admin/` 目录，初始化 Nuxt 3 项目
- [ ] 配置 `pnpm-workspace.yaml` 实现 monorepo
- [ ] 配置根目录 `package.json` 脚本
- [ ] 设置 TypeScript 配置和路径别名
- [ ] 配置 `admin/nuxt.config.ts`，添加共享组件路径

### Task 1.2: 数据库配置
- [ ] 安装 Drizzle ORM 和 PostgreSQL 驱动
- [ ] 创建 `shared/schema/` 目录，编写所有表的 Schema
- [ ] 配置 `drizzle.config.ts`
- [ ] 创建数据库迁移脚本
- [ ] 初始化种子数据（默认语言 zh/en/vi）

### Task 1.3: UI 框架配置
- [ ] 安装 Nuxt UI v3 模块
- [ ] 配置 Tailwind CSS v4
- [ ] 设置暗色/亮色主题
- [ ] 创建全局样式文件 `admin/assets/css/main.css`

---

## Phase 2: 用户认证系统

### Task 2.1: 钉钉 OAuth 集成
- [ ] 安装 `nuxt-auth-utils` 模块
- [ ] 创建 `server/api/auth/dingtalk.get.ts` OAuth 回调
- [ ] 创建 `server/api/auth/logout.post.ts` 登出接口
- [ ] 创建 `server/api/auth/session.get.ts` 会话查询
- [ ] 实现用户自动创建/更新逻辑

### Task 2.2: 登录页面
- [ ] 创建 `pages/login.vue` 登录页
- [ ] 实现钉钉扫码登录按钮
- [ ] 添加登录状态提示和错误处理
- [ ] 创建空白布局 `layouts/blank.vue`

### Task 2.3: 认证中间件
- [ ] 创建 `server/middleware/auth.ts` 服务端中间件
- [ ] 创建 `middleware/auth.global.ts` 客户端路由守卫
- [ ] 实现角色权限检查工具函数

---

## Phase 3: 后台布局与导航

### Task 3.1: 主布局组件
- [ ] 创建 `layouts/default.vue` 主布局
- [ ] 创建 `components/layout/AppHeader.vue` 顶部导航
- [ ] 创建 `components/layout/AppSidebar.vue` 侧边栏
- [ ] 创建 `components/layout/Breadcrumb.vue` 面包屑

### Task 3.2: 仪表盘首页
- [ ] 创建 `pages/index.vue` 仪表盘
- [ ] 显示文档统计（总数、草稿、已发布）
- [ ] 显示最近编辑的文档列表
- [ ] 显示团队活动动态

---

## Phase 4: 语言管理

### Task 4.1: 语言管理 API
- [ ] 创建 `server/api/locales/index.get.ts` 获取列表
- [ ] 创建 `server/api/locales/index.post.ts` 添加语言
- [ ] 创建 `server/api/locales/[id].patch.ts` 更新语言
- [ ] 创建 `server/api/locales/[id].delete.ts` 删除语言
- [ ] 创建 `server/api/locales/reorder.post.ts` 排序

### Task 4.2: 语言管理页面
- [ ] 创建 `pages/settings/locales.vue` 语言管理页
- [ ] 实现语言列表展示（拖拽排序）
- [ ] 实现添加语言对话框
- [ ] 实现编辑/删除语言功能
- [ ] 实现启用/禁用和设置默认语言

---

## Phase 5: 栏目管理

### Task 5.1: 栏目管理 API
- [ ] 创建 `server/api/categories/index.get.ts` 获取栏目树
- [ ] 创建 `server/api/categories/index.post.ts` 创建栏目
- [ ] 创建 `server/api/categories/[id].get.ts` 获取详情
- [ ] 创建 `server/api/categories/[id].patch.ts` 更新栏目
- [ ] 创建 `server/api/categories/[id].delete.ts` 删除栏目
- [ ] 创建 `server/api/categories/reorder.post.ts` 排序

### Task 5.2: 栏目管理页面
- [ ] 创建 `pages/categories/index.vue` 栏目管理页
- [ ] 实现栏目树展示（支持多级）
- [ ] 实现拖拽排序和移动
- [ ] 实现添加/编辑栏目对话框（多语言标题）
- [ ] 实现删除栏目（处理子栏目和文档）

---

## Phase 6: 导航菜单管理

### Task 6.1: 导航菜单 API
- [ ] 创建 `server/api/nav-menus/index.get.ts` 获取菜单树
- [ ] 创建 `server/api/nav-menus/index.post.ts` 创建菜单
- [ ] 创建 `server/api/nav-menus/[id].patch.ts` 更新菜单
- [ ] 创建 `server/api/nav-menus/[id].delete.ts` 删除菜单
- [ ] 创建 `server/api/nav-menus/reorder.post.ts` 排序
- [ ] 创建 `server/api/nav-menus/publish.post.ts` 发布到 VitePress

### Task 6.2: 导航菜单管理页面
- [ ] 创建 `pages/nav-menus/index.vue` 菜单管理页
- [ ] 实现菜单树展示（支持下拉菜单）
- [ ] 实现拖拽排序
- [ ] 实现添加/编辑菜单对话框
- [ ] 实现发布到 VitePress 功能

---

## Phase 7: 文件上传 (MinIO)

### Task 7.1: MinIO 配置
- [ ] 安装 `minio` npm 包
- [ ] 创建 `server/utils/minio.ts` MinIO 客户端
- [ ] 配置环境变量
- [ ] 创建 Bucket 初始化脚本

### Task 7.2: 上传 API
- [ ] 创建 `server/api/upload.post.ts` 文件上传接口
- [ ] 实现文件类型和大小验证
- [ ] 实现唯一文件名生成
- [ ] 返回 CDN 访问 URL

### Task 7.3: 上传 Composable
- [ ] 创建 `composables/useUpload.ts`
- [ ] 实现上传进度追踪
- [ ] 实现错误处理

---

## Phase 8: 文档编辑器

### Task 8.1: Tiptap 基础配置
- [ ] 安装 Tiptap Vue 3 及扩展包
- [ ] 创建 `components/editor/DocumentEditor.vue`
- [ ] 配置基础扩展（StarterKit, Placeholder 等）
- [ ] 实现编辑器工具栏

### Task 8.2: 图片和视频扩展
- [ ] 创建 `components/editor/extensions/ImageUpload.ts`
- [ ] 实现拖拽上传图片
- [ ] 实现粘贴上传图片
- [ ] 创建 `components/editor/extensions/Video.ts`
- [ ] 创建 `components/editor/VideoView.vue`

### Task 8.3: Slash Command
- [ ] 创建 `components/editor/extensions/SlashCommand.ts`
- [ ] 创建 `components/editor/SlashCommandList.vue`
- [ ] 实现命令搜索和键盘导航
- [ ] 添加所有命令项（标题、列表、代码块等）

### Task 8.4: 自定义组件块
- [ ] 创建 `components/editor/extensions/ComponentBlock.ts`
- [ ] 创建 `components/editor/ComponentBlockView.vue`
- [ ] 实现组件预览/编辑切换
- [ ] 配置共享组件导入（Quiz, Mermaid 等）

### Task 8.5: 组件属性编辑器
- [ ] 创建 `components/editor/ComponentPropsEditor.vue`
- [ ] 创建 `components/editor/props-editors/QuizPropsEditor.vue`
- [ ] 创建 `components/editor/props-editors/MermaidPropsEditor.vue`
- [ ] 创建 `components/editor/props-editors/CalloutPropsEditor.vue`

---

## Phase 9: 文档管理

### Task 9.1: 文档 API
- [ ] 创建 `server/api/documents/index.get.ts` 获取列表
- [ ] 创建 `server/api/documents/index.post.ts` 创建文档
- [ ] 创建 `server/api/documents/[id].get.ts` 获取详情
- [ ] 创建 `server/api/documents/[id].patch.ts` 更新文档
- [ ] 创建 `server/api/documents/[id].delete.ts` 删除文档
- [ ] 创建 `server/api/documents/search.get.ts` 搜索文档

### Task 9.2: 文档列表页面
- [ ] 创建 `pages/documents/index.vue` 文档列表
- [ ] 实现文件树组件 `components/file-tree/FileTree.vue`
- [ ] 实现文件树项 `components/file-tree/FileTreeItem.vue`
- [ ] 实现右键菜单（新建、重命名、删除）
- [ ] 实现拖拽移动文档

### Task 9.3: 文档编辑页面
- [ ] 创建 `pages/documents/[id].vue` 文档编辑页
- [ ] 集成 DocumentEditor 组件
- [ ] 实现文档标题编辑
- [ ] 实现保存和自动保存
- [ ] 显示文档状态（草稿/已发布）

---

## Phase 10: 版本管理

### Task 10.1: 版本 API
- [ ] 创建 `server/api/documents/[id]/versions.get.ts` 获取版本历史
- [ ] 创建 `server/api/documents/[id]/versions.post.ts` 创建版本
- [ ] 创建 `server/api/documents/[id]/versions/[versionId].get.ts` 获取版本内容
- [ ] 实现版本回滚逻辑

### Task 10.2: 版本历史 UI
- [ ] 创建版本历史侧边栏组件
- [ ] 实现版本列表展示
- [ ] 实现版本内容预览
- [ ] 实现版本对比（diff）
- [ ] 实现版本回滚功能

---

## Phase 11: 编辑锁系统

### Task 11.1: 编辑锁 API
- [ ] 创建 `server/api/documents/[id]/lock.post.ts` 获取锁
- [ ] 创建 `server/api/documents/[id]/lock.patch.ts` 续期锁
- [ ] 创建 `server/api/documents/[id]/lock.delete.ts` 释放锁
- [ ] 创建 `server/api/documents/[id]/lock/release.post.ts` Beacon 释放

### Task 11.2: 编辑锁 Composable
- [ ] 创建 `composables/useEditLock.ts`
- [ ] 实现锁获取和释放
- [ ] 实现心跳续期
- [ ] 实现页面卸载时释放锁

### Task 11.3: 编辑锁 UI
- [ ] 在编辑页显示锁状态
- [ ] 显示锁持有者信息
- [ ] 实现锁冲突提示

---

## Phase 12: 发布系统

### Task 12.1: Git 服务
- [ ] 安装 `simple-git` 包
- [ ] 创建 `server/utils/git.ts` Git 服务
- [ ] 实现单文档发布
- [ ] 实现批量发布
- [ ] 实现同步状态检查

### Task 12.2: 发布 API
- [ ] 创建 `server/api/documents/[id]/publish.post.ts` 发布文档
- [ ] 创建 `server/api/publish/batch.post.ts` 批量发布
- [ ] 实现 Markdown 序列化

### Task 12.3: 发布 UI
- [ ] 在编辑页添加发布按钮
- [ ] 实现发布确认对话框
- [ ] 显示发布状态和历史
- [ ] 实现批量发布页面

---

## Phase 13: AI 翻译

### Task 13.1: 翻译 API
- [ ] 安装 `@ai-sdk/vue` 和 `ai` 包
- [ ] 创建 `server/api/translate.post.ts` 翻译接口
- [ ] 实现流式响应
- [ ] 实现翻译任务记录

### Task 13.2: 翻译 Composable
- [ ] 创建 `composables/useTranslation.ts`
- [ ] 实现流式翻译状态管理

### Task 13.3: 翻译 UI
- [ ] 创建翻译对话框组件
- [ ] 实现语言选择
- [ ] 实现翻译进度显示
- [ ] 实现翻译结果预览和确认

---

## Phase 14: 用户管理

### Task 14.1: 用户 API
- [ ] 创建 `server/api/users/index.get.ts` 获取用户列表
- [ ] 创建 `server/api/users/[id].patch.ts` 更新用户角色

### Task 14.2: 用户管理页面
- [ ] 创建 `pages/settings/users.vue` 用户管理页
- [ ] 实现用户列表展示
- [ ] 实现角色修改功能

---

## Phase 15: 搜索功能

### Task 15.1: 全局搜索
- [ ] 创建搜索 Modal 组件
- [ ] 实现 Cmd+K 快捷键
- [ ] 实现文档搜索
- [ ] 实现键盘导航

---

## Phase 16: 测试与优化

### Task 16.1: 单元测试
- [ ] 配置 Vitest
- [ ] 编写 API 路由测试
- [ ] 编写 Composable 测试

### Task 16.2: E2E 测试
- [ ] 配置 Playwright
- [ ] 编写登录流程测试
- [ ] 编写文档编辑流程测试

### Task 16.3: 性能优化
- [ ] 添加数据库索引
- [ ] 配置 API 缓存
- [ ] 优化图片加载

---

## Phase 17: 部署

### Task 17.1: 部署配置
- [ ] 配置 Docker 镜像
- [ ] 配置 CI/CD 流水线
- [ ] 配置环境变量管理
- [ ] 配置 MinIO Bucket 策略

### Task 17.2: 文档
- [ ] 编写部署文档
- [ ] 编写开发者指南
- [ ] 编写 API 文档

---

## 依赖关系

```
Phase 1 (基础架构)
    ↓
Phase 2 (认证) ← Phase 3 (布局)
    ↓
Phase 4 (语言) → Phase 5 (栏目) → Phase 6 (导航菜单)
    ↓
Phase 7 (文件上传)
    ↓
Phase 8 (编辑器) → Phase 9 (文档管理)
    ↓
Phase 10 (版本) ← Phase 11 (编辑锁)
    ↓
Phase 12 (发布) ← Phase 13 (翻译)
    ↓
Phase 14 (用户) → Phase 15 (搜索)
    ↓
Phase 16 (测试) → Phase 17 (部署)
```

## 预估工时

| Phase | 任务数 | 预估工时 |
|-------|--------|----------|
| Phase 1-3 | 基础架构 | 3-4 天 |
| Phase 4-6 | 配置管理 | 2-3 天 |
| Phase 7-8 | 文件上传+编辑器 | 4-5 天 |
| Phase 9-11 | 文档管理 | 3-4 天 |
| Phase 12-13 | 发布+翻译 | 2-3 天 |
| Phase 14-15 | 用户+搜索 | 1-2 天 |
| Phase 16-17 | 测试+部署 | 2-3 天 |
| **总计** | | **17-24 天** |
