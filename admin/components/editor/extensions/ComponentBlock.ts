/**
 * 自定义组件块扩展
 * 支持在编辑器中插入和编辑 Vue 组件
 */
import { Node, mergeAttributes } from '@tiptap/core'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import ComponentBlockView from '../ComponentBlockView.vue'

export interface ComponentBlockOptions {
  HTMLAttributes: Record<string, any>
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    componentBlock: {
      /**
       * 插入组件块
       */
      insertComponent: (name: string, props?: Record<string, any>) => ReturnType
      /**
       * 更新组件属性
       */
      updateComponentProps: (props: Record<string, any>) => ReturnType
    }
  }
}

export const ComponentBlock = Node.create<ComponentBlockOptions>({
  name: 'componentBlock',
  group: 'block',
  atom: true,
  draggable: true,

  addOptions() {
    return {
      HTMLAttributes: {},
    }
  },

  addAttributes() {
    return {
      componentName: {
        default: '',
      },
      props: {
        default: {},
        parseHTML: (element) => {
          const propsStr = element.getAttribute('data-props')
          try {
            return propsStr ? JSON.parse(propsStr) : {}
          } catch {
            return {}
          }
        },
        renderHTML: (attributes) => ({
          'data-props': JSON.stringify(attributes.props),
        }),
      },
    }
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-component-block]',
        getAttrs: (element) => {
          if (typeof element === 'string') return false
          return {
            componentName: element.getAttribute('data-component-name'),
          }
        },
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'div',
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        'data-component-block': '',
        'data-component-name': HTMLAttributes.componentName,
      }),
    ]
  },

  addNodeView() {
    return VueNodeViewRenderer(ComponentBlockView)
  },

  addCommands() {
    return {
      insertComponent:
        (name: string, props: Record<string, any> = {}) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs: { componentName: name, props },
          })
        },
      updateComponentProps:
        (props: Record<string, any>) =>
        ({ commands }) => {
          return commands.updateAttributes(this.name, { props })
        },
    }
  },
})
