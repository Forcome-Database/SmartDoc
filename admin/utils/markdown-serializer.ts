/**
 * Markdown 序列化器
 * 将 Tiptap HTML 转换为 Markdown + Vue 组件语法
 * 
 * 支持的组件：
 * - Quiz: 选择题组件
 * - MermaidWrapper: Mermaid 图表
 * - Markmap: 思维导图
 * - Callout: 提示框
 */
import TurndownService from 'turndown'
// @ts-expect-error - turndown-plugin-gfm 没有类型定义
import { gfm } from 'turndown-plugin-gfm'

// 类型定义
type TurndownNode = Node
type TurndownOptions = TurndownService.Options

// 创建 Turndown 实例
const turndownService = new TurndownService({
  headingStyle: 'atx',
  codeBlockStyle: 'fenced',
  bulletListMarker: '-',
  emDelimiter: '*',
  strongDelimiter: '**',
  linkStyle: 'inlined',
  hr: '---',
})

// 添加 GFM 支持（表格、任务列表、删除线等）
turndownService.use(gfm)

// ============ 组件序列化函数 ============

/**
 * 转义 HTML 属性中的特殊字符
 */
function escapeAttr(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '\\n')
}

/**
 * 序列化 Quiz 选择题组件
 * 输出格式：Vue 组件标签
 */
function serializeQuiz(props: {
  question: string
  options: string[]
  answer: number
  explanation?: string
}): string {
  const lines = [
    '',
    '<Quiz',
    `  question="${escapeAttr(props.question || '')}"`,
    `  :options='${JSON.stringify(props.options || [])}'`,
    `  :answer="${props.answer ?? 0}"`,
  ]
  if (props.explanation) {
    lines.push(`  explanation="${escapeAttr(props.explanation)}"`)
  }
  lines.push('/>')
  lines.push('')
  return lines.join('\n')
}

/**
 * 序列化 Mermaid 图表组件
 * 输出格式：带 mermaid 标记的代码块
 */
function serializeMermaid(props: { content: string; title?: string }): string {
  const content = props.content || 'graph TD\n  A[开始] --> B[结束]'
  if (props.title) {
    return `\n\`\`\`mermaid-box{title="${escapeAttr(props.title)}"}\n${content}\n\`\`\`\n`
  }
  return `\n\`\`\`mermaid\n${content}\n\`\`\`\n`
}

/**
 * 序列化 Markmap 思维导图组件
 * 输出格式：带 markmap 标记的代码块
 */
function serializeMarkmap(props: { content: string }): string {
  const content = props.content || '# 主题\n## 分支1\n## 分支2'
  return `\n\`\`\`markmap\n${content}\n\`\`\`\n`
}

/**
 * 序列化 Callout 提示框组件
 * 输出格式：VitePress 容器语法 ::: type
 */
function serializeCallout(props: { type: string; title?: string; content: string }): string {
  const type = props.type || 'info'
  const content = props.content || ''
  
  if (props.title) {
    return `\n::: ${type} ${props.title}\n${content}\n:::\n`
  }
  return `\n::: ${type}\n${content}\n:::\n`
}

/**
 * 通用组件序列化
 * 用于处理未知组件类型
 */
function serializeGeneric(name: string, props: Record<string, any>): string {
  const propsEntries = Object.entries(props).filter(([_, value]) => value !== undefined && value !== null)
  
  if (propsEntries.length === 0) {
    return `\n<${name} />\n`
  }
  
  const propsStr = propsEntries
    .map(([key, value]) => {
      if (typeof value === 'string') {
        return `  ${key}="${escapeAttr(value)}"`
      }
      if (typeof value === 'boolean') {
        return value ? `  ${key}` : ''
      }
      if (typeof value === 'number') {
        return `  :${key}="${value}"`
      }
      return `  :${key}='${JSON.stringify(value)}'`
    })
    .filter(Boolean)
    .join('\n')
  
  return `\n<${name}\n${propsStr}\n/>\n`
}

/**
 * 根据组件名称选择对应的序列化函数
 */
function serializeComponent(name: string, props: Record<string, any>): string {
  switch (name) {
    case 'Quiz':
      return serializeQuiz(props as Parameters<typeof serializeQuiz>[0])
    case 'MermaidWrapper':
    case 'Mermaid':
      return serializeMermaid(props as Parameters<typeof serializeMermaid>[0])
    case 'Markmap':
      return serializeMarkmap(props as Parameters<typeof serializeMarkmap>[0])
    case 'Callout':
      return serializeCallout(props as Parameters<typeof serializeCallout>[0])
    default:
      return serializeGeneric(name, props)
  }
}

// ============ Turndown 自定义规则 ============

/**
 * 自定义组件块规则
 * 处理 data-component-block 属性的 div 元素
 */
turndownService.addRule('componentBlock', {
  filter: (node: TurndownNode) => {
    return (
      node.nodeName === 'DIV' && 
      (node as HTMLElement).hasAttribute('data-component-block')
    )
  },
  replacement: (_content: string, node: TurndownNode) => {
    const element = node as HTMLElement
    const componentName = element.getAttribute('data-component-name')
    const propsStr = element.getAttribute('data-props')
    
    if (!componentName) {
      return ''
    }
    
    try {
      const props = propsStr ? JSON.parse(propsStr) : {}
      return serializeComponent(componentName, props)
    } catch (error) {
      console.error('Failed to parse component props:', error)
      return ''
    }
  },
})

/**
 * 保留代码块中的语言标记
 * 确保代码块正确转换
 */
turndownService.addRule('fencedCodeBlock', {
  filter: (node: TurndownNode, options: TurndownOptions) => {
    return (
      options.codeBlockStyle === 'fenced' &&
      node.nodeName === 'PRE' &&
      node.firstChild !== null &&
      node.firstChild.nodeName === 'CODE'
    )
  },
  replacement: (_content: string, node: TurndownNode) => {
    const codeElement = node.firstChild as HTMLElement
    const className = codeElement.getAttribute('class') || ''
    const languageMatch = className.match(/language-(\S+)/)
    const language = languageMatch ? languageMatch[1] : ''
    const code = codeElement.textContent || ''
    
    return `\n\`\`\`${language}\n${code}\n\`\`\`\n`
  },
})

/**
 * 处理任务列表项
 */
turndownService.addRule('taskListItem', {
  filter: (node: TurndownNode) => {
    return (
      node.nodeName === 'LI' &&
      (node as HTMLElement).hasAttribute('data-type') &&
      (node as HTMLElement).getAttribute('data-type') === 'taskItem'
    )
  },
  replacement: (content: string, node: TurndownNode) => {
    const element = node as HTMLElement
    const checked = element.getAttribute('data-checked') === 'true'
    const checkbox = checked ? '[x]' : '[ ]'
    const trimmedContent = content.trim().replace(/^\n+/, '').replace(/\n+$/, '')
    return `- ${checkbox} ${trimmedContent}\n`
  },
})

/**
 * 处理图片，保留 alt 和 title
 */
turndownService.addRule('image', {
  filter: 'img',
  replacement: (_content: string, node: TurndownNode) => {
    const element = node as HTMLImageElement
    const alt = element.getAttribute('alt') || ''
    const src = element.getAttribute('src') || ''
    const title = element.getAttribute('title')
    
    if (title) {
      return `![${alt}](${src} "${title}")`
    }
    return `![${alt}](${src})`
  },
})

/**
 * 处理视频元素
 * 转换为 HTML video 标签
 */
turndownService.addRule('video', {
  filter: (node: TurndownNode) => {
    return (
      node.nodeName === 'DIV' &&
      (node as HTMLElement).hasAttribute('data-video')
    )
  },
  replacement: (_content: string, node: TurndownNode) => {
    const element = node as HTMLElement
    const src = element.getAttribute('data-src') || ''
    const poster = element.getAttribute('data-poster') || ''
    
    if (!src) return ''
    
    const posterAttr = poster ? ` poster="${poster}"` : ''
    return `\n<video src="${src}"${posterAttr} controls></video>\n`
  },
})

// ============ 导出函数 ============

/**
 * 将 HTML 转换为 Markdown
 * @param html - Tiptap 编辑器输出的 HTML
 * @returns Markdown 字符串
 */
export function htmlToMarkdown(html: string): string {
  if (!html || html.trim() === '') {
    return ''
  }
  
  // 预处理：清理空白节点
  const cleanedHtml = html
    .replace(/>\s+</g, '><')  // 移除标签间的空白
    .replace(/\n\s*\n/g, '\n') // 移除多余空行
  
  const markdown = turndownService.turndown(cleanedHtml)
  
  // 后处理：规范化空行
  return markdown
    .replace(/\n{3,}/g, '\n\n')  // 最多保留两个换行
    .trim()
}

/**
 * 导出组件序列化函数供外部使用
 */
export {
  serializeQuiz,
  serializeMermaid,
  serializeMarkmap,
  serializeCallout,
  serializeGeneric,
  serializeComponent,
  escapeAttr,
}
