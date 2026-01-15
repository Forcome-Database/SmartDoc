/**
 * Slash Command 扩展
 * 输入 "/" 显示命令菜单
 */
import { Extension } from '@tiptap/core'
import { VueRenderer } from '@tiptap/vue-3'
import tippy, { type Instance } from 'tippy.js'
import Suggestion, { type SuggestionOptions } from '@tiptap/suggestion'
import SlashCommandList from '../SlashCommandList.vue'

export interface CommandItem {
  title: string
  description: string
  icon: string
  command: (props: { editor: any; range: any }) => void
}

// 基础命令列表
const baseCommands: CommandItem[] = [
  {
    title: '标题 1',
    description: '大标题',
    icon: 'i-lucide-heading-1',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).setNode('heading', { level: 1 }).run()
    },
  },
  {
    title: '标题 2',
    description: '中标题',
    icon: 'i-lucide-heading-2',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).setNode('heading', { level: 2 }).run()
    },
  },
  {
    title: '标题 3',
    description: '小标题',
    icon: 'i-lucide-heading-3',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).setNode('heading', { level: 3 }).run()
    },
  },
  {
    title: '无序列表',
    description: '创建无序列表',
    icon: 'i-lucide-list',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).toggleBulletList().run()
    },
  },
  {
    title: '有序列表',
    description: '创建有序列表',
    icon: 'i-lucide-list-ordered',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).toggleOrderedList().run()
    },
  },
  {
    title: '任务列表',
    description: '创建待办事项',
    icon: 'i-lucide-list-checks',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).toggleTaskList().run()
    },
  },
  {
    title: '代码块',
    description: '插入代码块',
    icon: 'i-lucide-file-code',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).toggleCodeBlock().run()
    },
  },
  {
    title: '引用',
    description: '插入引用块',
    icon: 'i-lucide-quote',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).toggleBlockquote().run()
    },
  },
  {
    title: '分割线',
    description: '插入水平分割线',
    icon: 'i-lucide-minus',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).setHorizontalRule().run()
    },
  },
  {
    title: '表格',
    description: '插入表格',
    icon: 'i-lucide-table',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
    },
  },
  {
    title: '图片',
    description: '插入图片',
    icon: 'i-lucide-image',
    command: ({ editor, range }) => {
      const url = window.prompt('输入图片地址')
      if (url) {
        editor.chain().focus().deleteRange(range).setImage({ src: url }).run()
      }
    },
  },
  // 自定义组件
  {
    title: '选择题',
    description: '插入交互式选择题',
    icon: 'i-lucide-help-circle',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).insertComponent('Quiz', {
        question: '',
        options: ['', '', '', ''],
        answer: 0,
        explanation: '',
      }).run()
    },
  },
  {
    title: 'Mermaid 图表',
    description: '插入流程图、时序图等',
    icon: 'i-lucide-git-branch',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).insertComponent('MermaidWrapper', {
        content: 'graph TD\n  A[开始] --> B[结束]',
        title: '',
      }).run()
    },
  },
  {
    title: '思维导图',
    description: '插入 Markmap 思维导图',
    icon: 'i-lucide-brain',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).insertComponent('Markmap', {
        content: '# 主题\n## 分支1\n## 分支2',
      }).run()
    },
  },
  {
    title: '提示框',
    description: '插入信息提示框',
    icon: 'i-lucide-info',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).insertComponent('Callout', {
        type: 'info',
        title: '',
        content: '提示内容',
      }).run()
    },
  },
]

export interface SlashCommandOptions {
  suggestion: Partial<SuggestionOptions>
  commands?: CommandItem[]
}

export const SlashCommand = Extension.create<SlashCommandOptions>({
  name: 'slashCommand',

  addOptions() {
    return {
      suggestion: {
        char: '/',
        command: ({ editor, range, props }: any) => {
          props.command({ editor, range })
        },
      },
      commands: baseCommands,
    }
  },

  addProseMirrorPlugins() {
    return [
      Suggestion({
        editor: this.editor,
        ...this.options.suggestion,
        items: ({ query }: { query: string }) => {
          const commands = this.options.commands || baseCommands
          return commands.filter((item) =>
            item.title.toLowerCase().includes(query.toLowerCase()) ||
            item.description.toLowerCase().includes(query.toLowerCase())
          )
        },
        render: () => {
          let component: VueRenderer
          let popup: Instance[]

          return {
            onStart: (props: any) => {
              component = new VueRenderer(SlashCommandList, {
                props,
                editor: props.editor,
              })

              if (!props.clientRect) return

              popup = tippy('body', {
                getReferenceClientRect: props.clientRect,
                appendTo: () => document.body,
                content: component.element,
                showOnCreate: true,
                interactive: true,
                trigger: 'manual',
                placement: 'bottom-start',
              })
            },
            onUpdate: (props: any) => {
              component.updateProps(props)
              if (props.clientRect) {
                popup[0].setProps({
                  getReferenceClientRect: props.clientRect,
                })
              }
            },
            onKeyDown: (props: any) => {
              if (props.event.key === 'Escape') {
                popup[0].hide()
                return true
              }
              return component.ref?.onKeyDown(props)
            },
            onExit: () => {
              popup[0].destroy()
              component.destroy()
            },
          }
        },
      }),
    ]
  },
})

export { baseCommands }
