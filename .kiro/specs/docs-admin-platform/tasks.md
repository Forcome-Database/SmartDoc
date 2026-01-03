# Implementation Plan: FORCOME 知识库后台管理系统

## Overview

本实现计划基于 Nuxt 3 全栈框架，构建类 Mintlify 风格的文档管理平台。采用增量开发方式，从基础架构开始，逐步实现认证、文档管理、编辑器、版本控制、AI 翻译等核心功能。

## Tasks

- [ ] 1. 项目初始化与基础架构
  - [ ] 1.1 创建 Nuxt 3 项目结构
    - 在 `admin/` 目录下初始化 Nuxt 3 项目
    - 配置 `nuxt.config.ts`，添加模块：`@nuxt/ui`, `@pinia/nuxt`, `@vueuse/nuxt`, `nuxt-auth-utils`
    - 配置 Tailwind CSS v4
    - 设置共享组件别名 `@shared` 和 `@docs-components`
    - _Requirements: 8.1, 8.2, 8.3_

  - [ ] 1.2 配置 Monorepo 工作区
    - 创建 `pnpm-workspace.yaml` 配置 docs/admin/shared 包
    - 创建根目录 `package.json` 配置工作区脚本
    - 配置 TypeScript 路径别名
    - _Requirements: 8.1_

  - [ ] 1.3 设置数据库连接
    - 安装 Drizzle ORM 和 PostgreSQL 驱动
    - 创建 `drizzle.config.ts` 配置文件
    - 创建 `admin/server/utils/db.ts` 数据库连接工具
    - _Requirements: 10.1, 10.2_

- [ ] 2. 数据库 Schema 设计与迁移
  - [ ] 2.1 创建基础 Schema 定义
    - 创建 `shared/schema/index.ts`
    - 定义 enums: `userRoleEnum`, `documentStatusEnum`, `navMenuTypeEnum`, `translationStatusEnum`
    - 定义 `locales` 表（语言配置）
    - 定义 `users` 表（用户信息，含钉钉字段）
    - _Requirements: 10.2, 12.7_

  - [ ] 2.2 创建文档相关 Schema
    - 定义 `categories` 表（栏目）
    - 定义 `categoryTitles` 表（栏目多语言标题）
    - 定义 `documents` 表（文档）
    - 定义 `versions` 表（版本历史）
    - 定义 `editLocks` 表（编辑锁）
    - _Requirements: 2.1, 3.1, 4.1, 13.2_

  - [ ] 2.3 创建导航菜单 Schema
    - 定义 `navMenus` 表
    - 定义 `navMenuTitles` 表（菜单多语言标题）
    - 定义 `translations` 表（翻译任务）
    - 定义表关系 (relations)
    - _Requirements: 10.2_

  - [ ] 2.4 执行数据库迁移
    - 运行 `drizzle-kit generate` 生成迁移文件
    - 运行 `drizzle-kit migrate` 执行迁移
    - 验证数据库表结构
    - _Requirements: 10.1, 10.5_

- [ ] 3. 用户认证系统
  - [ ] 3.1 实现钉钉 OAuth 登录
    - 创建 `admin/server/api/auth/dingtalk.get.ts` OAuth 回调处理
    - 实现获取 access_token 逻辑
    - 实现获取用户信息逻辑
    - 实现用户创建/更新逻辑
    - 设置 session
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

  - [ ] 3.2 实现登录页面
    - 创建 `admin/pages/login.vue`
    - 实现钉钉登录按钮和跳转逻辑
    - 处理登录错误显示
    - _Requirements: 1.1, 12.1, 12.6_

  - [ ] 3.3 实现登出和会话管理
    - 创建 `admin/server/api/auth/logout.post.ts`
    - 创建 `admin/server/api/auth/session.get.ts`
    - 创建认证中间件 `admin/server/middleware/auth.ts`
    - _Requirements: 1.4, 1.5, 12.9_

  - [ ] 3.4 实现用户状态管理
    - 创建 `admin/stores/user.ts` Pinia store
    - 实现用户信息获取和缓存
    - 实现角色权限检查
    - _Requirements: 1.6, 12.5_

- [ ] 4. 基础 UI 布局
  - [ ] 4.1 创建应用布局组件
    - 创建 `admin/layouts/default.vue` 三栏布局
    - 创建 `admin/layouts/blank.vue` 空白布局（登录页）
    - 实现响应式布局适配
    - _Requirements: 8.1, 8.4_

  - [ ] 4.2 创建头部组件
    - 创建 `admin/components/layout/AppHeader.vue`
    - 实现 Logo、面包屑导航、用户菜单
    - 实现同步状态显示
    - _Requirements: 8.6, 5.5_

  - [ ] 4.3 创建侧边栏组件
    - 创建 `admin/components/layout/AppSidebar.vue`
    - 实现导航菜单
    - 实现新建文档/设置入口
    - _Requirements: 8.1_

  - [ ] 4.4 实现主题切换
    - 实现 light/dark 主题切换
    - 实现系统偏好检测
    - 持久化主题设置
    - _Requirements: 8.2_

- [ ] 5. Checkpoint - 基础架构验证
  - 确保项目可以正常启动
  - 确保数据库连接正常
  - 确保钉钉登录流程正常
  - 如有问题请询问用户


- [ ] 6. 语言管理模块
  - [ ] 6.1 实现语言 API
    - 创建 `admin/server/api/locales/index.get.ts` 获取语言列表
    - 创建 `admin/server/api/locales/index.post.ts` 添加语言
    - 创建 `admin/server/api/locales/[id].patch.ts` 更新语言
    - 创建 `admin/server/api/locales/[id].delete.ts` 删除语言
    - 创建 `admin/server/api/locales/reorder.post.ts` 重新排序
    - _Requirements: 6.9_

  - [ ] 6.2 实现语言管理页面
    - 创建 `admin/pages/settings/locales.vue`
    - 实现语言列表展示（表格）
    - 实现添加/编辑语言对话框
    - 实现拖拽排序
    - 实现启用/禁用切换
    - _Requirements: 6.9_

- [ ] 7. 栏目管理模块
  - [ ] 7.1 实现栏目 API
    - 创建 `admin/server/api/categories/index.get.ts` 获取栏目树
    - 创建 `admin/server/api/categories/index.post.ts` 创建栏目
    - 创建 `admin/server/api/categories/[id].get.ts` 获取栏目详情
    - 创建 `admin/server/api/categories/[id].patch.ts` 更新栏目
    - 创建 `admin/server/api/categories/[id].delete.ts` 删除栏目
    - 创建 `admin/server/api/categories/reorder.post.ts` 重新排序
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ] 7.2 实现文件树组件
    - 创建 `admin/components/file-tree/FileTree.vue`
    - 创建 `admin/components/file-tree/FileTreeItem.vue`
    - 实现树形结构展示
    - 实现展开/折叠功能
    - 实现右键上下文菜单
    - _Requirements: 7.1, 7.3, 7.6_

  - [ ] 7.3 实现文件树交互
    - 实现拖拽排序和移动
    - 实现新建文件夹/文档
    - 实现重命名和删除
    - 显示未保存状态指示器
    - _Requirements: 7.4, 7.5, 7.7, 2.4_

  - [ ] 7.4 实现栏目管理页面
    - 创建 `admin/pages/categories/index.vue`
    - 实现栏目树管理界面
    - 实现多语言标题编辑
    - _Requirements: 2.5, 2.6_

- [ ] 8. 导航菜单管理模块
  - [ ] 8.1 实现导航菜单 API
    - 创建 `admin/server/api/nav-menus/index.get.ts` 获取菜单树
    - 创建 `admin/server/api/nav-menus/index.post.ts` 创建菜单项
    - 创建 `admin/server/api/nav-menus/[id].patch.ts` 更新菜单项
    - 创建 `admin/server/api/nav-menus/[id].delete.ts` 删除菜单项
    - 创建 `admin/server/api/nav-menus/reorder.post.ts` 重新排序
    - 创建 `admin/server/api/nav-menus/publish.post.ts` 发布到 VitePress
    - _Requirements: 5.1, 5.2_

  - [ ] 8.2 实现导航菜单管理页面
    - 创建 `admin/pages/nav-menus/index.vue`
    - 实现菜单树可视化编辑
    - 实现菜单类型选择（链接/下拉/分割线）
    - 实现目标类型选择（栏目/文档/外部链接）
    - 实现多语言标题编辑
    - _Requirements: 5.1_

- [ ] 9. Checkpoint - 内容结构管理验证
  - 确保语言管理功能正常
  - 确保栏目树 CRUD 正常
  - 确保导航菜单管理正常
  - 如有问题请询问用户

- [ ] 10. 文档 CRUD API
  - [ ] 10.1 实现文档基础 API
    - 创建 `admin/server/api/documents/index.get.ts` 获取文档列表
    - 创建 `admin/server/api/documents/index.post.ts` 创建文档
    - 创建 `admin/server/api/documents/[id].get.ts` 获取文档详情
    - 创建 `admin/server/api/documents/[id].patch.ts` 更新文档
    - 创建 `admin/server/api/documents/[id].delete.ts` 删除文档
    - _Requirements: 3.1, 3.7_

  - [ ] 10.2 实现版本管理 API
    - 创建 `admin/server/api/documents/[id]/versions.get.ts` 获取版本历史
    - 实现版本创建逻辑（保存时自动创建）
    - 实现版本回滚逻辑
    - _Requirements: 4.1, 4.2, 4.5, 4.6, 4.7_

  - [ ] 10.3 实现搜索 API
    - 创建 `admin/server/api/documents/search.get.ts`
    - 实现标题、内容、元数据搜索
    - 实现搜索结果排序
    - _Requirements: 9.3_


- [ ] 11. Tiptap 编辑器核心
  - [ ] 11.1 创建编辑器基础组件
    - 创建 `admin/components/editor/DocumentEditor.vue`
    - 配置 Tiptap 扩展：StarterKit, Placeholder, CodeBlockLowlight
    - 配置 Image, Link, Table, TaskList 扩展
    - 实现编辑器样式（prose 类）
    - _Requirements: 3.2, 3.4_

  - [ ] 11.2 实现编辑器工具栏
    - 创建 `admin/components/editor/EditorToolbar.vue`
    - 实现格式化按钮（标题、列表、代码块等）
    - 实现气泡菜单 (BubbleMenu)
    - _Requirements: 3.8_

  - [ ] 11.3 实现 Slash Command 扩展
    - 创建 `admin/components/editor/extensions/SlashCommand.ts`
    - 创建 `admin/components/editor/SlashCommandList.vue`
    - 实现命令列表过滤和键盘导航
    - 添加标题、列表、代码块、引用等命令
    - _Requirements: 3.3_

  - [ ] 11.4 实现自定义组件块扩展
    - 创建 `admin/components/editor/extensions/ComponentBlock.ts`
    - 创建 `admin/components/editor/ComponentBlockView.vue`
    - 实现组件渲染（Quiz, Mermaid, Markmap, Callout）
    - 实现组件属性编辑
    - _Requirements: 3.4_

  - [ ] 11.5 实现组件属性编辑器
    - 创建 `admin/components/editor/ComponentPropsEditor.vue`
    - 创建 `admin/components/editor/props-editors/QuizPropsEditor.vue`
    - 创建 `admin/components/editor/props-editors/MermaidPropsEditor.vue`
    - 创建 `admin/components/editor/props-editors/CalloutPropsEditor.vue`
    - _Requirements: 3.4_

- [ ] 12. 文件上传功能
  - [ ] 12.1 配置 MinIO 客户端
    - 创建 `admin/server/utils/minio.ts`
    - 配置 MinIO 连接和 Bucket
    - 定义文件类型配置（图片/视频/文件）
    - _Requirements: 3.4_

  - [ ] 12.2 实现上传 API
    - 创建 `admin/server/api/upload.post.ts`
    - 实现文件类型和大小验证
    - 实现文件上传到 MinIO
    - 返回访问 URL
    - _Requirements: 3.4_

  - [ ] 12.3 实现图片上传扩展
    - 创建 `admin/components/editor/extensions/ImageUpload.ts`
    - 实现拖拽上传
    - 实现粘贴上传
    - _Requirements: 3.4, 3.5_

  - [ ] 12.4 实现视频扩展
    - 创建 `admin/components/editor/extensions/Video.ts`
    - 创建 `admin/components/editor/VideoView.vue`
    - 实现视频上传和播放
    - _Requirements: 3.4_

  - [ ] 12.5 实现上传 Composable
    - 创建 `admin/composables/useUpload.ts`
    - 实现上传进度跟踪
    - 实现错误处理
    - _Requirements: 3.4_

- [ ] 13. Markdown 序列化
  - [ ] 13.1 实现 HTML 到 Markdown 转换
    - 创建 `admin/utils/markdown-serializer.ts`
    - 配置 Turndown 和 GFM 插件
    - 实现自定义组件块序列化规则
    - _Requirements: 3.6_

  - [ ] 13.2 实现组件序列化
    - 实现 Quiz 组件序列化
    - 实现 Mermaid 组件序列化
    - 实现 Markmap 组件序列化
    - 实现 Callout 组件序列化
    - _Requirements: 3.6_

- [ ] 14. Checkpoint - 编辑器功能验证
  - 确保编辑器基础功能正常
  - 确保 Slash Command 正常工作
  - 确保文件上传正常
  - 确保 Markdown 导出正常
  - 如有问题请询问用户

- [ ] 15. 文档编辑页面
  - [ ] 15.1 创建文档编辑页面
    - 创建 `admin/pages/documents/[id].vue`
    - 集成 DocumentEditor 组件
    - 实现文档加载和保存
    - 实现未保存状态提示
    - _Requirements: 3.1, 3.7, 3.9_

  - [ ] 15.2 实现自动保存
    - 创建 `admin/composables/useAutoSave.ts`
    - 实现防抖保存逻辑
    - 实现保存状态指示
    - _Requirements: 3.7_

  - [ ] 15.3 实现版本历史面板
    - 创建版本历史侧边栏组件
    - 实现版本列表展示
    - 实现版本预览
    - 实现版本回滚
    - _Requirements: 4.2, 4.3, 4.5_

  - [ ] 15.4 实现版本对比
    - 实现两个版本的 diff 对比视图
    - 高亮显示变更内容
    - _Requirements: 4.4_


- [ ] 16. 编辑锁与协作
  - [ ] 16.1 实现编辑锁 API
    - 创建 `admin/server/api/documents/[id]/lock.post.ts` 获取锁
    - 创建 `admin/server/api/documents/[id]/lock.patch.ts` 续期锁
    - 创建 `admin/server/api/documents/[id]/lock.delete.ts` 释放锁
    - 创建 `admin/server/api/documents/[id]/lock/release.post.ts` Beacon 释放
    - _Requirements: 13.2, 13.3, 13.4_

  - [ ] 16.2 实现编辑锁 Composable
    - 创建 `admin/composables/useEditLock.ts`
    - 实现锁获取、续期、释放逻辑
    - 实现心跳定时器（5分钟超时自动释放）
    - 实现页面卸载时释放锁
    - _Requirements: 13.2, 13.4, 13.5_

  - [ ] 16.3 实现协作者显示
    - 显示当前文档的协作者头像
    - 显示锁持有者信息
    - 实现锁定状态 UI 提示
    - _Requirements: 13.1, 13.3, 13.7_

  - [ ] 16.4 实现文档更新通知
    - 创建 `admin/server/api/documents/[id]/watchers.get.ts` 获取查看者
    - 实现文档更新时通知当前查看者刷新
    - 使用轮询或 SSE 实现实时通知
    - _Requirements: 13.6_

  - [ ] 16.5 实现版本作者记录
    - 在版本保存时记录作者信息
    - 在版本历史中显示作者头像和名称
    - _Requirements: 13.8_

  - [ ] 16.6 实现评论与 @提及功能
    - 创建 `admin/server/api/documents/[id]/comments` API
    - 实现评论列表和添加评论
    - 实现 @用户 提及功能
    - 实现提及用户自动补全
    - _Requirements: 13.9_

  - [ ] 16.7 实现通知系统
    - 创建 `admin/server/api/notifications` API
    - 实现站内通知（被 @提及、文档更新）
    - 可选：集成钉钉消息推送
    - _Requirements: 13.10_

  - [ ] 16.8 实现活动动态
    - 创建 `admin/server/api/activities` API
    - 实现最近文档变更动态列表
    - 在 Dashboard 显示团队活动
    - _Requirements: 13.11_

  - [ ] 16.9 实现文档权限控制
    - 创建 `admin/server/api/documents/[id]/permissions` API
    - 实现文档级别权限设置（查看/编辑/管理）
    - 支持按用户或部门设置权限
    - _Requirements: 13.12_

- [ ] 17. 搜索功能
  - [ ] 17.1 实现搜索模态框
    - 创建 `admin/components/SearchModal.vue`
    - 实现 Ctrl+K / Cmd+K 快捷键触发
    - 实现实时搜索
    - _Requirements: 9.1, 9.2_

  - [ ] 17.2 实现搜索结果展示
    - 实现搜索结果列表
    - 实现键盘导航（上下箭头、回车）
    - 实现点击跳转
    - 实现无结果提示
    - _Requirements: 9.4, 9.5, 9.6_

- [ ] 18. Git 发布功能
  - [ ] 18.1 实现 Git 服务
    - 创建 `admin/server/utils/git.ts`
    - 实现单文档发布
    - 实现批量发布
    - 实现同步状态检查
    - _Requirements: 5.1, 5.2, 5.5, 5.7_

  - [ ] 18.2 实现发布 API
    - 创建 `admin/server/api/documents/[id]/publish.post.ts`
    - 创建 `admin/server/api/publish/batch.post.ts`
    - 实现发布状态更新
    - _Requirements: 5.1, 5.3, 5.4_

  - [ ] 18.3 实现发布 UI
    - 在编辑器工具栏添加发布按钮
    - 实现发布确认对话框
    - 显示发布状态（已发布/有更改）
    - 实现批量发布界面
    - _Requirements: 5.3, 5.6, 5.7_

- [ ] 19. Checkpoint - 文档管理验证
  - 确保文档 CRUD 正常
  - 确保版本管理正常
  - 确保编辑锁正常工作
  - 确保发布功能正常
  - 如有问题请询问用户

- [ ] 20. AI 翻译功能
  - [ ] 20.1 实现翻译 API
    - 创建 `admin/server/api/translate.post.ts`
    - 配置 OpenAI/AI SDK
    - 实现流式翻译响应
    - 实现 Markdown 格式保持
    - _Requirements: 6.2, 6.3, 6.6, 6.7_

  - [ ] 20.2 实现翻译 Composable
    - 创建 `admin/composables/useTranslation.ts`
    - 使用 `@ai-sdk/vue` 的 `useCompletion`
    - 实现翻译状态管理
    - _Requirements: 6.2, 6.3_

  - [ ] 20.3 实现翻译对话框
    - 创建翻译对话框组件
    - 实现源语言/目标语言选择
    - 实现流式翻译结果展示
    - 实现翻译结果预览和编辑
    - _Requirements: 6.1, 6.3, 6.4_

  - [ ] 20.4 实现翻译保存
    - 实现翻译结果保存为新文档
    - 关联源文档和翻译文档
    - 记录翻译任务历史
    - _Requirements: 6.5, 6.8, 6.9_

- [ ] 21. 用户管理
  - [ ] 21.1 实现用户 API
    - 创建 `admin/server/api/users/index.get.ts` 获取用户列表
    - 创建 `admin/server/api/users/[id].patch.ts` 更新用户角色
    - _Requirements: 1.6, 13.12_

  - [ ] 21.2 实现用户管理页面
    - 创建 `admin/pages/settings/users.vue`
    - 实现用户列表展示
    - 实现角色修改
    - _Requirements: 1.6_

  - [ ] 21.3 实现 Dashboard 首页
    - 创建 `admin/pages/index.vue`
    - 显示最近编辑的文档
    - 显示团队活动动态
    - 显示待处理通知
    - _Requirements: 13.11_

- [ ] 22. 错误处理与反馈
  - [ ] 22.1 实现 Toast 通知系统
    - 使用 Nuxt UI 的 Toast 组件
    - 实现成功/错误/警告通知
    - _Requirements: 11.1, 11.2_

  - [ ] 22.2 实现加载状态
    - 实现全局加载指示器
    - 实现按钮加载状态
    - _Requirements: 11.3_

  - [ ] 22.3 实现表单验证
    - 使用 Zod 进行输入验证
    - 实现内联验证错误显示
    - _Requirements: 11.4_

  - [ ] 22.4 实现网络错误处理
    - 实现请求重试机制
    - 保留用户输入
    - _Requirements: 11.5_

- [ ] 23. 快捷键支持
  - [ ] 23.1 实现全局快捷键
    - Ctrl+K / Cmd+K 打开搜索
    - Ctrl+S / Cmd+S 保存文档
    - 实现快捷键提示
    - _Requirements: 8.5_

- [ ] 24. 最终集成与测试
  - [ ] 24.1 集成所有模块
    - 确保所有页面路由正常
    - 确保所有 API 正常工作
    - 确保组件间通信正常
    - _Requirements: 全部_

  - [ ] 24.2 UI 细节优化
    - 实现平滑过渡动画 (0.15-0.2s)
    - 统一间距、字体、颜色
    - 响应式布局测试
    - _Requirements: 8.3, 8.4, 8.7_

- [ ] 25. Final Checkpoint - 完整功能验证
  - 确保所有功能正常工作
  - 确保 UI 符合设计规范
  - 确保错误处理完善
  - 如有问题请询问用户

## Notes

- 任务按照依赖关系排序，前置任务完成后再进行后续任务
- 每个 Checkpoint 用于验证阶段性成果，确保增量开发质量
- 所有 API 需要添加认证中间件保护
- 所有用户输入需要使用 Zod 验证
- 遵循 Nuxt 3 最佳实践和 Vue 3 Composition API 规范
