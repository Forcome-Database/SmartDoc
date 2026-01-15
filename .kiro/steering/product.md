# Product Overview

FORCOME 知识库平台，包含两个子系统：

## 1. 文档站点 (docs/)

VitePress 驱动的文档展示站点，Cursor 官网风格。

**核心功能**：
- 三栏布局：导航栏 + 可调侧边栏 + 内容区
- 全局搜索 (⌘K) + AI 问答面板 (⌘I)
- 深色模式 + 多语言 (zh/en/vi)

## 2. 后台管理 (admin/)

Nuxt 3 全栈后台，类 Mintlify 风格。

**核心功能**：
- 钉钉 OAuth 登录 + 角色权限
- 文件树导航 + md-editor-v3 Markdown 编辑器
- 文档版本管理（数据库草稿 + Git 发布）
- AI 流式翻译（多语言）
- 多用户协作（编辑锁 + 在线状态）
- 文件上传（MinIO 对象存储）

**数据模型**：
- `users` - 用户（钉钉集成）
- `documents` - 文档
- `versions` - 版本历史
- `categories` - 栏目树
- `locales` - 语言配置
- `nav_menus` - 导航菜单
- `edit_locks` - 编辑锁

## Design Philosophy

- 简约大气：充足留白，细微交互
- 平滑过渡：0.15-0.2s ease
- 字体：Inter (UI) + JetBrains Mono (代码)
- 无障碍：ARIA 标签，键盘导航
