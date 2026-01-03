# Project Structure

```
docs/
├── .vitepress/
│   ├── config.ts                 # VitePress config (nav, sidebar, locales)
│   ├── theme/
│   │   ├── index.ts              # Theme entry point
│   │   ├── Layout.vue            # Root layout component
│   │   ├── components/
│   │   │   ├── NavBar.vue        # Top navigation bar
│   │   │   ├── SideBar.vue       # Left sidebar with resize handle
│   │   │   ├── SideBarItem.vue   # Recursive sidebar item
│   │   │   ├── SearchModal.vue   # Full-screen search (⌘K)
│   │   │   ├── AIChat.vue        # AI Q&A panel (⌘I)
│   │   │   ├── AIChatMessage.vue # Chat message component
│   │   │   ├── RightPanel.vue    # Right panel (TOC + toolbar)
│   │   │   ├── ThemeToggle.vue   # Dark/light mode toggle
│   │   │   ├── LangSwitch.vue    # Language switcher
│   │   │   └── icons/            # SVG icon components
│   │   ├── composables/
│   │   │   ├── useTheme.ts       # Theme state & persistence
│   │   │   ├── useSidebar.ts     # Sidebar width & drag logic
│   │   │   ├── useSearch.ts      # Search state & keyboard nav
│   │   │   ├── useAIChat.ts      # AI chat state & Dify integration
│   │   │   └── useStorage.ts     # localStorage wrapper
│   │   ├── services/
│   │   │   ├── dify.ts           # Dify API client (SSE streaming)
│   │   │   └── storage.ts        # Storage service
│   │   ├── types/
│   │   │   └── index.ts          # TypeScript type definitions
│   │   └── styles/
│   │       ├── vars.css          # CSS variables (colors, spacing, fonts)
│   │       ├── base.css          # Reset & base styles
│   │       ├── layout.css        # Layout structure styles
│   │       ├── components.css    # Component-specific styles
│   │       ├── markdown.css      # Markdown content styles
│   │       └── transitions.css   # Animation & transition styles
│   └── cache/
├── public/
│   ├── fonts/
│   │   ├── inter/                # Inter font files (woff2)
│   │   └── jetbrains-mono/       # JetBrains Mono font files
│   └── images/
│       └── logo.svg
├── zh/                           # Chinese docs (default)
├── en/                           # English docs
├── ja/                           # Japanese docs
└── index.md                      # Homepage
```

## Key Patterns

- **Composables**: All stateful logic lives in `composables/` with `use*` naming
- **Services**: External API integrations in `services/`
- **CSS Variables**: Theme values defined in `vars.css`, referenced throughout
- **Component Hierarchy**: Layout → NavBar/SideBar/Content → child components
