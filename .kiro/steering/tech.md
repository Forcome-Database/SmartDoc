# Tech Stack & Build System

## Core Technologies

| Category | Technology | Version |
|----------|------------|---------|
| Static Site Generator | VitePress | ^2.0.0 |
| Frontend Framework | Vue 3 | ^3.5.0 |
| Type System | TypeScript | ^5.3.3 |
| CSS Framework | Tailwind CSS | ^4.0.0 |
| Package Manager | pnpm | ^9.0.0 |
| AI Service | Dify API | SSE streaming |

## Development Commands

```bash
# Install dependencies
pnpm install

# Start dev server
pnpm docs:dev

# Build for production
pnpm docs:build

# Preview production build
pnpm docs:preview

# Type check
pnpm type-check
```

## Code Conventions

- **Vue Components**: Composition API with `<script setup lang="ts">`
- **TypeScript**: Strict mode enabled
- **Styling**: CSS variables for theming, avoid hardcoded colors
- **Comments**: Chinese language for code comments
- **State Management**: Composables pattern (useTheme, useSidebar, useAIChat, etc.)

## Environment Variables

```bash
VITE_DIFY_API_BASE=https://your-dify-instance/v1
VITE_DIFY_API_KEY=your-api-key
```

## Key Dependencies

- `@vue/test-utils` - Component testing
- `vitest` - Unit testing
- `playwright` - E2E testing (optional)

## Agent Guidelines

### 第三方依赖使用规范

在使用任何第三方库或框架时，**必须先查阅对应版本的官方文档**，确保 API 用法与指定版本兼容：

- VitePress 2.0: 使用 Context7 MCP 工具查询 `/vitepress/vitepress` 文档
- Vue 3.4+: 查询 Composition API 和 `<script setup>` 语法
- Tailwind CSS 4.0: 注意 v4 与 v3 的配置差异

### UI 参考与调研

需要了解 Cursor 官网界面、UI 细节或交互行为时，使用 **Playwright MCP 工具**：

```
1. - 访问 https://cursor.com/cn/docs
2. - 截图参考
3. - 获取页面结构
```

这样可以确保实现与目标网站的视觉和交互保持一致。
