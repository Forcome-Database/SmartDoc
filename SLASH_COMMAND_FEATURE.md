# ✨ Slash 命令功能

## 功能概述

为 FORCOME 知识库后台管理系统的 Markdown 编辑器添加了类似 Notion 的 "/" 指令功能，让内容创作更加高效。

## 🎯 核心特性

- ✅ **快速插入**：输入 `/` 即可打开命令面板
- ✅ **智能搜索**：支持中英文关键词过滤
- ✅ **键盘导航**：完整的键盘快捷键支持
- ✅ **丰富命令**：17+ 常用 Markdown 元素
- ✅ **深色模式**：完美适配深色主题
- ✅ **流畅体验**：平滑动画和过渡效果

## 📦 新增文件

```
admin/
├── components/editor/
│   ├── SlashCommandPanel.vue           # 命令面板组件
│   ├── DocumentEditorWithSlash.vue     # 增强版编辑器
│   ├── README.md                       # 组件文档
│   └── SLASH_COMMAND_GUIDE.md          # 使用指南
├── composables/
│   └── useSlashCommand.ts              # 命令逻辑
└── pages/
    └── test-slash-command.vue          # 测试页面
```

## 🚀 快速开始

### 1. 在现有页面中使用

将原有的 `EditorDocumentEditor` 替换为 `EditorDocumentEditorWithSlash`：

```vue
<template>
  <!-- 之前 -->
  <EditorDocumentEditor
    v-model="content"
    @save="handleSave"
  />
  
  <!-- 现在 -->
  <EditorDocumentEditorWithSlash
    v-model="content"
    @save="handleSave"
  />
</template>
```

### 2. 访问测试页面

启动开发服务器后，访问：

```
http://localhost:3000/test-slash-command
```

## 💡 使用方法

### 基本用法

1. 在编辑器中输入 `/`（必须在行首或空格后）
2. 命令面板自动弹出
3. 输入关键词搜索命令
4. 使用 ↑↓ 键选择，Enter 确认

### 示例

```markdown
# 输入 /h1 插入一级标题
/h1
# 标题

# 输入 /code 插入代码块
/code
```javascript
console.log('Hello')
```

# 输入 /table 插入表格
/table
| 列1 | 列2 | 列3 |
| --- | --- | --- |
| 内容 | 内容 | 内容 |
```

## 📋 可用命令

### 标题（3 个）
- `/h1` - 一级标题
- `/h2` - 二级标题
- `/h3` - 三级标题

### 文本格式（3 个）
- `/bold` - 粗体
- `/italic` - 斜体
- `/code` - 代码块

### 列表（3 个）
- `/list` - 无序列表
- `/ordered` - 有序列表
- `/task` - 任务列表

### 内容块（3 个）
- `/quote` - 引用
- `/table` - 表格
- `/divider` - 分割线

### 媒体（2 个）
- `/link` - 链接
- `/image` - 图片

### 提示框（3 个）
- `/info` - 信息提示框
- `/warning` - 警告提示框
- `/tip` - 技巧提示框

## ⌨️ 键盘快捷键

| 快捷键 | 功能 |
|--------|------|
| `/` | 打开命令面板 |
| `↑` `↓` | 在命令列表中导航 |
| `Enter` | 选择当前命令 |
| `Esc` | 关闭命令面板 |
| `Cmd/Ctrl + S` | 保存文档 |

## 🎨 设计理念

遵循 FORCOME 知识库的设计哲学：

- **简约大气**：清晰的视觉层次，充足的留白
- **平滑过渡**：0.15-0.2s 的流畅动画
- **无障碍**：完整的键盘导航支持
- **响应式**：适配深色模式

## 🔧 自定义命令

在 `SlashCommandPanel.vue` 中添加自定义命令：

```typescript
const commands: SlashCommand[] = [
  // ... 现有命令
  
  {
    id: 'custom',
    label: '自定义命令',
    description: '插入自定义内容',
    icon: 'i-lucide-star',
    keywords: ['custom', '自定义'],
    action: () => '你的内容',
  },
]
```

## 📊 技术实现

### 核心技术栈

- **Vue 3** - Composition API
- **TypeScript** - 类型安全
- **md-editor-v3** - Markdown 编辑器
- **Nuxt UI v3** - UI 组件库
- **Tailwind CSS** - 样式

### 实现原理

1. **内容监听**：监听编辑器 `onChange` 事件
2. **模式匹配**：检测 `/` 字符及其上下文
3. **位置计算**：获取光标屏幕坐标
4. **面板渲染**：使用 `Teleport` 渲染到 body
5. **内容替换**：选择命令后替换文本

### 关键代码

```typescript
// 检测 slash 命令
const detectSlashCommand = (content: string, cursorPos: number) => {
  const beforeCursor = content.substring(0, cursorPos)
  const lastSlashIndex = beforeCursor.lastIndexOf('/')
  
  // 检查 "/" 前面是否是行首或空格
  const charBeforeSlash = lastSlashIndex > 0 
    ? beforeCursor[lastSlashIndex - 1] 
    : '\n'
    
  return charBeforeSlash === '\n' || charBeforeSlash === ' '
}
```

## 🧪 测试

### 手动测试

1. 启动开发服务器：
   ```bash
   pnpm dev:admin
   ```

2. 访问测试页面：
   ```
   http://localhost:3000/test-slash-command
   ```

3. 测试场景：
   - ✅ 在行首输入 `/`
   - ✅ 在空格后输入 `/`
   - ✅ 搜索命令（中英文）
   - ✅ 键盘导航
   - ✅ 鼠标点击
   - ✅ 深色模式

## 📝 更新日志

### v1.0.0 (2026-01-05)

**新增功能**
- ✨ Slash 命令面板组件
- ✨ 17+ 常用 Markdown 命令
- ✨ 智能搜索和过滤
- ✨ 完整键盘导航
- ✨ 深色模式支持

**技术改进**
- 🔧 创建 `useSlashCommand` composable
- 🔧 增强版编辑器组件
- 📚 完整的使用文档

## 🎯 未来计划

- [ ] 添加更多命令（Mermaid 图表、数学公式等）
- [ ] 支持自定义命令配置
- [ ] 命令历史记录
- [ ] 命令使用统计
- [ ] AI 辅助命令推荐

## 📖 相关文档

- [组件文档](./admin/components/editor/README.md)
- [使用指南](./admin/components/editor/SLASH_COMMAND_GUIDE.md)
- [测试页面](./admin/pages/test-slash-command.vue)

## 🤝 贡献

欢迎提出建议和改进！

---

**Made with ❤️ for FORCOME Knowledge Base**
