/**
 * md-editor-v3 配置插件
 * 配置 mermaid 和 katex 渲染器
 */
import { config } from 'md-editor-v3'
import mermaid from 'mermaid'
import katex from 'katex'
import 'katex/dist/katex.min.css'

export default defineNuxtPlugin(() => {
  // 配置 mermaid
  config({
    mermaidConfig(base) {
      return {
        ...base,
        startOnLoad: false,
        securityLevel: 'loose',
        theme: 'default',
        flowchart: {
          useMaxWidth: true,
          htmlLabels: true,
        },
        gantt: {
          useMaxWidth: true,
        },
        journey: {
          useMaxWidth: true,
        },
        sequence: {
          useMaxWidth: true,
        },
      }
    },
    // 配置 mermaid 渲染
    editorExtensions: {
      mermaid: {
        instance: mermaid,
      },
    },
    // 配置 katex 渲染
    markdownItConfig(md) {
      // md-editor-v3 内部会处理 katex
    },
  })

  // 配置 katex
  config({
    editorExtensions: {
      katex: {
        instance: katex,
      },
    },
  })
})
