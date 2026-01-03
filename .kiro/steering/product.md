# Product Overview

This is a VitePress-based documentation platform that replicates the Cursor official documentation website (cursor.com/cn/docs) style and layout, with integrated Dify AI knowledge base Q&A functionality.

## Core Features

- **Three-column layout**: Fixed navbar (48px), resizable sidebar (280px default, 200-400px range), centered content area (max 768px)
- **Search**: Full-screen modal search with ⌘K/Ctrl+K shortcut, keyboard navigation support
- **AI Q&A Panel**: Right-side sliding panel (400px) with ⌘I/Ctrl+I shortcut, Dify API integration with SSE streaming
- **Dark Mode**: System preference detection, manual toggle, localStorage persistence
- **Multi-language**: Chinese (default), English, Japanese support via VitePress locales
- **Responsive Design**: Mobile drawer sidebar, full-screen modals on small screens

## Design Philosophy

- Minimalist aesthetic: 1px borders, generous whitespace, subtle interactions
- Smooth transitions (0.15-0.2s ease)
- Typography: Inter for UI (替代 CursorGothic), JetBrains Mono for code (替代 BerkeleyMono)
- Accessibility: ARIA labels, keyboard navigation, semantic HTML

## UI Reference Screenshots

参考截图位于 `docs/public/images/reference/`：

| 文件 | 说明 |
|------|------|
| cursor-docs-main-*.png | 文档首页（桌面端） |
| cursor-docs-fullpage-*.png | 完整页面截图 |
| cursor-docs-getstarted-*.png | 文章详情页 |
| cursor-docs-mobile-*.png | 移动端视图 (390x844) |

实现 UI 时应参考这些截图确保视觉一致性。
