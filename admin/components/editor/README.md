# 编辑器组件

## DocumentEditorWithSlash

增强版 Markdown 编辑器，支持 "/" 指令快速插入内容。

### 功能特性

- ✅ 基于 md-editor-v3
- ✅ 支持 "/" 指令打开命令面板
- ✅ 类似 Notion 的交互体验
- ✅ 键盘导航（↑↓ 选择，Enter 确认，Esc 关闭）
- ✅ 智能搜索过滤
- ✅ 深色模式支持
- ✅ 图片上传到 MinIO

### 使用方法

```vue
<template>
  <EditorDocumentEditorWithSlash
    v-model="content"
    document-id="doc-123"
    placeholder="开始输入..."
    @save="handleSave"
  />
</template>

<script setup>
const content = ref('# Hello World')

const handleSave = () => {
  console.log('保存文档')
}
</script>
```

### Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `modelValue` | `string` | - | 编辑器内容（v-model） |
| `documentId` | `string` | - | 文档 ID |
| `readOnly` | `boolean` | `false` | 只读模式 |
| `placeholder` | `string` | - | 占位符文本 |

### Events

| 事件 | 参数 | 说明 |
|------|------|------|
| `update:modelValue` | `(value: string)` | 内容变化 |
| `save` | - | 保存触发 |

### Slash 命令列表

输入 `/` 触发命令面板，支持以下命令：

#### 标题
- `/h1` - 一级标题
- `/h2` - 二级标题
- `/h3` - 三级标题

#### 文本格式
- `/bold` - 粗体
- `/italic` - 斜体
- `/code` - 代码块

#### 列表
- `/list` - 无序列表
- `/ordered` - 有序列表
- `/task` - 任务列表

#### 内容块
- `/quote` - 引用
- `/table` - 表格
- `/divider` - 分割线

#### 媒体
- `/link` - 链接
- `/image` - 图片

#### 提示框
- `/info` - 信息提示框
- `/warning` - 警告提示框
- `/tip` - 技巧提示框

### 自定义命令

可以通过修改 `SlashCommandPanel.vue` 中的 `commands` 数组来添加自定义命令：

```typescript
{
  id: 'custom-command',
  label: '自定义命令',
  description: '命令描述',
  icon: 'i-lucide-star',
  keywords: ['custom', '自定义'],
  action: () => '插入的内容',
}
```

### 键盘快捷键

- `↑` / `↓` - 在命令列表中导航
- `Enter` - 选择当前命令
- `Esc` - 关闭命令面板
- `Cmd/Ctrl + S` - 保存文档

### 技术实现

1. **命令检测**：监听编辑器内容变化，检测 "/" 字符
2. **位置计算**：获取光标在屏幕上的位置
3. **命令面板**：使用 Teleport 渲染到 body
4. **内容插入**：替换 "/" 及搜索文本为命令内容

### 注意事项

- "/" 必须在行首或空格后才会触发
- 命令面板会自动过滤匹配的命令
- 选择命令后会自动聚焦编辑器
