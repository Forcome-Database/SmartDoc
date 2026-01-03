import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'
import tailwindcss from '@tailwindcss/vite'

/**
 * VitePress 配置文件
 * FORCOME 知识库 - 支持多语言（中/英/越南语）
 */

// 中文侧边栏配置
const zhSidebar = {
  // 首页
  '/zh/': [
    {
      text: '开始使用',
      items: [
        { text: '欢迎', link: '/zh/' },
        { text: '快速入门', link: '/zh/quickstart' },
        { text: '图表指南', link: '/zh/diagrams' }
      ]
    }
  ],
  // 金蝶 ERP
  '/zh/enterprise/kingdee': [
    {
      text: '金蝶 ERP',
      items: [
        { text: '概述', link: '/zh/enterprise/kingdee/' },
        { text: '快速开始', link: '/zh/enterprise/kingdee/quickstart' },
        { text: '系统配置', link: '/zh/enterprise/kingdee/setup' }
      ]
    },
    {
      text: '财务管理',
      items: [
        { text: '凭证管理', link: '/zh/enterprise/kingdee/finance/voucher' },
        { text: '账簿查询', link: '/zh/enterprise/kingdee/finance/books' },
        { text: '期末结账', link: '/zh/enterprise/kingdee/finance/closing' },
        { text: '应收应付', link: '/zh/enterprise/kingdee/finance/receivable' },
        { text: '固定资产', link: '/zh/enterprise/kingdee/finance/assets' }
      ]
    },
    {
      text: '供应链',
      items: [
        { text: '采购管理', link: '/zh/enterprise/kingdee/scm/purchase' },
        { text: '销售管理', link: '/zh/enterprise/kingdee/scm/sales' },
        { text: '库存管理', link: '/zh/enterprise/kingdee/scm/inventory' }
      ]
    },
    {
      text: '生产制造',
      items: [
        { text: '生产计划', link: '/zh/enterprise/kingdee/mfg/planning' },
        { text: '物料需求', link: '/zh/enterprise/kingdee/mfg/mrp' },
        { text: '车间管理', link: '/zh/enterprise/kingdee/mfg/workshop' }
      ]
    }
  ],
  // CRM 系统
  '/zh/enterprise/crm': [
    {
      text: 'CRM 系统',
      items: [
        { text: '概述', link: '/zh/enterprise/crm/' },
        { text: '快速开始', link: '/zh/enterprise/crm/quickstart' },
        { text: '系统配置', link: '/zh/enterprise/crm/setup' }
      ]
    },
    {
      text: '客户管理',
      items: [
        { text: '客户信息', link: '/zh/enterprise/crm/customer/info' },
        { text: '客户分类', link: '/zh/enterprise/crm/customer/category' },
        { text: '联系人管理', link: '/zh/enterprise/crm/customer/contacts' }
      ]
    },
    {
      text: '销售管理',
      items: [
        { text: '销售机会', link: '/zh/enterprise/crm/sales/opportunity' },
        { text: '销售漏斗', link: '/zh/enterprise/crm/sales/funnel' },
        { text: '合同管理', link: '/zh/enterprise/crm/sales/contract' }
      ]
    }
  ],
  // OA 办公
  '/zh/enterprise/oa': [
    {
      text: 'OA 办公',
      items: [
        { text: '概述', link: '/zh/enterprise/oa/' },
        { text: '即将推出', link: '/zh/enterprise/oa/coming-soon' }
      ]
    }
  ],
  // 智能财务
  '/zh/ai-apps/finance': [
    {
      text: '智能财务',
      items: [
        { text: '概述', link: '/zh/ai-apps/finance/' },
        { text: '快速开始', link: '/zh/ai-apps/finance/quickstart' }
      ]
    },
    {
      text: '核心功能',
      items: [
        { text: '智能记账', link: '/zh/ai-apps/finance/bookkeeping' },
        { text: '智能对账', link: '/zh/ai-apps/finance/reconciliation' },
        { text: '报表分析', link: '/zh/ai-apps/finance/reports' }
      ]
    }
  ],
  // 智能PPT
  '/zh/ai-apps/ppt': [
    {
      text: '智能PPT',
      items: [
        { text: '概述', link: '/zh/ai-apps/ppt/' },
        { text: '快速开始', link: '/zh/ai-apps/ppt/quickstart' }
      ]
    },
    {
      text: '核心功能',
      items: [
        { text: '内容生成', link: '/zh/ai-apps/ppt/content' },
        { text: '智能设计', link: '/zh/ai-apps/ppt/design' },
        { text: '导出分享', link: '/zh/ai-apps/ppt/export' }
      ]
    }
  ],
  // 知识学习
  '/zh/learning': [
    {
      text: '知识学习',
      items: [
        { text: '概述', link: '/zh/learning/' },
        { text: '学习路径', link: '/zh/learning/roadmap' }
      ]
    },
    {
      text: '大模型基础',
      items: [
        { text: '什么是大模型', link: '/zh/learning/llm/intro' },
        { text: 'Prompt 工程', link: '/zh/learning/llm/prompt' },
        { text: 'RAG 技术', link: '/zh/learning/llm/rag' }
      ]
    }
  ]
}


// 英文侧边栏配置
const enSidebar = {
  '/en/': [
    {
      text: 'Getting Started',
      items: [
        { text: 'Welcome', link: '/en/' },
        { text: 'Quickstart', link: '/en/quickstart' }
      ]
    }
  ],
  '/en/enterprise/kingdee': [
    {
      text: 'Kingdee ERP',
      items: [
        { text: 'Overview', link: '/en/enterprise/kingdee/' },
        { text: 'Quickstart', link: '/en/enterprise/kingdee/quickstart' },
        { text: 'Setup', link: '/en/enterprise/kingdee/setup' }
      ]
    },
    {
      text: 'Finance',
      items: [
        { text: 'Voucher', link: '/en/enterprise/kingdee/finance/voucher' },
        { text: 'Ledger', link: '/en/enterprise/kingdee/finance/books' },
        { text: 'Period Closing', link: '/en/enterprise/kingdee/finance/closing' }
      ]
    },
    {
      text: 'Supply Chain',
      items: [
        { text: 'Purchasing', link: '/en/enterprise/kingdee/scm/purchase' },
        { text: 'Sales', link: '/en/enterprise/kingdee/scm/sales' },
        { text: 'Inventory', link: '/en/enterprise/kingdee/scm/inventory' }
      ]
    }
  ],
  '/en/enterprise/crm': [
    {
      text: 'CRM System',
      items: [
        { text: 'Overview', link: '/en/enterprise/crm/' },
        { text: 'Quickstart', link: '/en/enterprise/crm/quickstart' }
      ]
    },
    {
      text: 'Customer',
      items: [
        { text: 'Customer Info', link: '/en/enterprise/crm/customer/info' },
        { text: 'Contacts', link: '/en/enterprise/crm/customer/contacts' }
      ]
    }
  ],
  '/en/enterprise/oa': [
    {
      text: 'OA System',
      items: [
        { text: 'Overview', link: '/en/enterprise/oa/' },
        { text: 'Coming Soon', link: '/en/enterprise/oa/coming-soon' }
      ]
    }
  ],
  '/en/ai-apps/finance': [
    {
      text: 'Smart Finance',
      items: [
        { text: 'Overview', link: '/en/ai-apps/finance/' },
        { text: 'Quickstart', link: '/en/ai-apps/finance/quickstart' }
      ]
    },
    {
      text: 'Features',
      items: [
        { text: 'Bookkeeping', link: '/en/ai-apps/finance/bookkeeping' },
        { text: 'Reconciliation', link: '/en/ai-apps/finance/reconciliation' }
      ]
    }
  ],
  '/en/ai-apps/ppt': [
    {
      text: 'Smart PPT',
      items: [
        { text: 'Overview', link: '/en/ai-apps/ppt/' },
        { text: 'Quickstart', link: '/en/ai-apps/ppt/quickstart' }
      ]
    },
    {
      text: 'Features',
      items: [
        { text: 'Content Generation', link: '/en/ai-apps/ppt/content' },
        { text: 'Smart Design', link: '/en/ai-apps/ppt/design' }
      ]
    }
  ],
  '/en/learning': [
    {
      text: 'Learning',
      items: [
        { text: 'Overview', link: '/en/learning/' },
        { text: 'Roadmap', link: '/en/learning/roadmap' }
      ]
    },
    {
      text: 'LLM Basics',
      items: [
        { text: 'What is LLM', link: '/en/learning/llm/intro' },
        { text: 'Prompt Engineering', link: '/en/learning/llm/prompt' }
      ]
    }
  ]
}

// 越南语侧边栏配置
const viSidebar = {
  '/vi/': [
    {
      text: 'Bắt đầu',
      items: [
        { text: 'Chào mừng', link: '/vi/' },
        { text: 'Bắt đầu nhanh', link: '/vi/quickstart' }
      ]
    }
  ],
  '/vi/enterprise/kingdee': [
    {
      text: 'Kingdee ERP',
      items: [
        { text: 'Tổng quan', link: '/vi/enterprise/kingdee/' },
        { text: 'Bắt đầu nhanh', link: '/vi/enterprise/kingdee/quickstart' },
        { text: 'Cấu hình', link: '/vi/enterprise/kingdee/setup' }
      ]
    },
    {
      text: 'Tài chính',
      items: [
        { text: 'Chứng từ', link: '/vi/enterprise/kingdee/finance/voucher' },
        { text: 'Sổ cái', link: '/vi/enterprise/kingdee/finance/books' },
        { text: 'Kết chuyển', link: '/vi/enterprise/kingdee/finance/closing' }
      ]
    },
    {
      text: 'Chuỗi cung ứng',
      items: [
        { text: 'Mua hàng', link: '/vi/enterprise/kingdee/scm/purchase' },
        { text: 'Bán hàng', link: '/vi/enterprise/kingdee/scm/sales' },
        { text: 'Kho', link: '/vi/enterprise/kingdee/scm/inventory' }
      ]
    }
  ],
  '/vi/enterprise/crm': [
    {
      text: 'Hệ thống CRM',
      items: [
        { text: 'Tổng quan', link: '/vi/enterprise/crm/' },
        { text: 'Bắt đầu nhanh', link: '/vi/enterprise/crm/quickstart' }
      ]
    },
    {
      text: 'Khách hàng',
      items: [
        { text: 'Thông tin', link: '/vi/enterprise/crm/customer/info' },
        { text: 'Liên hệ', link: '/vi/enterprise/crm/customer/contacts' }
      ]
    }
  ],
  '/vi/enterprise/oa': [
    {
      text: 'Hệ thống OA',
      items: [
        { text: 'Tổng quan', link: '/vi/enterprise/oa/' },
        { text: 'Sắp ra mắt', link: '/vi/enterprise/oa/coming-soon' }
      ]
    }
  ],
  '/vi/ai-apps/finance': [
    {
      text: 'Tài chính thông minh',
      items: [
        { text: 'Tổng quan', link: '/vi/ai-apps/finance/' },
        { text: 'Bắt đầu nhanh', link: '/vi/ai-apps/finance/quickstart' }
      ]
    },
    {
      text: 'Tính năng',
      items: [
        { text: 'Kế toán', link: '/vi/ai-apps/finance/bookkeeping' },
        { text: 'Đối chiếu', link: '/vi/ai-apps/finance/reconciliation' }
      ]
    }
  ],
  '/vi/ai-apps/ppt': [
    {
      text: 'PPT thông minh',
      items: [
        { text: 'Tổng quan', link: '/vi/ai-apps/ppt/' },
        { text: 'Bắt đầu nhanh', link: '/vi/ai-apps/ppt/quickstart' }
      ]
    },
    {
      text: 'Tính năng',
      items: [
        { text: 'Tạo nội dung', link: '/vi/ai-apps/ppt/content' },
        { text: 'Thiết kế', link: '/vi/ai-apps/ppt/design' }
      ]
    }
  ],
  '/vi/learning': [
    {
      text: 'Học tập',
      items: [
        { text: 'Tổng quan', link: '/vi/learning/' },
        { text: 'Lộ trình', link: '/vi/learning/roadmap' }
      ]
    },
    {
      text: 'LLM cơ bản',
      items: [
        { text: 'LLM là gì', link: '/vi/learning/llm/intro' },
        { text: 'Prompt Engineering', link: '/vi/learning/llm/prompt' }
      ]
    }
  ]
}


export default withMermaid(defineConfig({
  vite: {
    plugins: [tailwindcss() as any],
    envDir: '../',
    optimizeDeps: { include: ['mermaid', 'dayjs'] },
    ssr: { noExternal: ['mermaid'] }
  },

  title: 'FORCOME 知识库',
  description: 'FORCOME 知识库 - 企业知识管理平台',

  head: [
    ['link', { rel: 'icon', type: 'image/x-icon', href: '/images/logo/favicon.ico' }],
    ['link', { rel: 'icon', type: 'image/png', href: '/images/logo/logo.png' }],
    ['meta', { name: 'viewport', content: 'width=device-width, initial-scale=1.0' }],
    ['meta', { name: 'theme-color', content: '#000000' }],
    ['link', { rel: 'preload', href: '/fonts/inter/Inter-Regular.woff2', as: 'font', type: 'font/woff2', crossorigin: '' }],
    ['link', { rel: 'preload', href: '/fonts/jetbrains-mono/JetBrainsMono-Regular.woff2', as: 'font', type: 'font/woff2', crossorigin: '' }]
  ],

  locales: {
    zh: {
      label: '中文',
      lang: 'zh-CN',
      link: '/zh/',
      title: 'FORCOME 知识库',
      description: '企业知识管理平台',
      themeConfig: {
        nav: [
          { text: '首页', link: '/zh/', activeMatch: '^/zh/$' },
          {
            text: '企业应用',
            activeMatch: '^/zh/enterprise/',
            items: [
              { text: '金蝶 ERP', link: '/zh/enterprise/kingdee/' },
              { text: 'CRM 系统', link: '/zh/enterprise/crm/' },
              { text: 'OA 办公', link: '/zh/enterprise/oa/' }
            ]
          },
          {
            text: 'AI应用',
            activeMatch: '^/zh/ai-apps/',
            items: [
              { text: '智能财务', link: '/zh/ai-apps/finance/' },
              { text: '智能PPT', link: '/zh/ai-apps/ppt/' }
            ]
          },
          { text: '知识学习', link: '/zh/learning/', activeMatch: '^/zh/learning/' }
        ],
        sidebar: zhSidebar,
        outline: { label: '本页目录' },
        docFooter: { prev: '上一页', next: '下一页' },
        lastUpdated: { text: '最后更新于' }
      }
    },
    en: {
      label: 'English',
      lang: 'en-US',
      link: '/en/',
      title: 'FORCOME Knowledge Base',
      description: 'Enterprise Knowledge Management Platform',
      themeConfig: {
        nav: [
          { text: 'Home', link: '/en/', activeMatch: '^/en/$' },
          {
            text: 'Enterprise',
            activeMatch: '^/en/enterprise/',
            items: [
              { text: 'Kingdee ERP', link: '/en/enterprise/kingdee/' },
              { text: 'CRM System', link: '/en/enterprise/crm/' },
              { text: 'OA System', link: '/en/enterprise/oa/' }
            ]
          },
          {
            text: 'AI Apps',
            activeMatch: '^/en/ai-apps/',
            items: [
              { text: 'Smart Finance', link: '/en/ai-apps/finance/' },
              { text: 'Smart PPT', link: '/en/ai-apps/ppt/' }
            ]
          },
          { text: 'Learning', link: '/en/learning/', activeMatch: '^/en/learning/' }
        ],
        sidebar: enSidebar,
        outline: { label: 'On this page' },
        docFooter: { prev: 'Previous', next: 'Next' },
        lastUpdated: { text: 'Last updated' }
      }
    },
    vi: {
      label: 'Tiếng Việt',
      lang: 'vi-VN',
      link: '/vi/',
      title: 'FORCOME Cơ sở tri thức',
      description: 'Nền tảng quản lý tri thức doanh nghiệp',
      themeConfig: {
        nav: [
          { text: 'Trang chủ', link: '/vi/', activeMatch: '^/vi/$' },
          {
            text: 'Doanh nghiệp',
            activeMatch: '^/vi/enterprise/',
            items: [
              { text: 'Kingdee ERP', link: '/vi/enterprise/kingdee/' },
              { text: 'Hệ thống CRM', link: '/vi/enterprise/crm/' },
              { text: 'Hệ thống OA', link: '/vi/enterprise/oa/' }
            ]
          },
          {
            text: 'Ứng dụng AI',
            activeMatch: '^/vi/ai-apps/',
            items: [
              { text: 'Tài chính thông minh', link: '/vi/ai-apps/finance/' },
              { text: 'PPT thông minh', link: '/vi/ai-apps/ppt/' }
            ]
          },
          { text: 'Học tập', link: '/vi/learning/', activeMatch: '^/vi/learning/' }
        ],
        sidebar: viSidebar,
        outline: { label: 'Mục lục' },
        docFooter: { prev: 'Trước', next: 'Tiếp' },
        lastUpdated: { text: 'Cập nhật lần cuối' }
      }
    }
  },

  themeConfig: {
    logo: '/images/logo/logo.png',
    siteTitle: 'FORCOME 知识库',
    search: { provider: 'local' },
    socialLinks: [{ icon: 'github', link: 'https://github.com' }],
    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2024-present FORCOME'
    }
  },

  markdown: {
    theme: { light: 'github-light', dark: 'github-dark' },
    lineNumbers: false,
    config: (md) => {
      // 保存原始的 fence 渲染器
      const defaultFence = md.renderer.rules.fence!
      
      // 自定义 fence 渲染器，处理自定义代码块
      md.renderer.rules.fence = (tokens, idx, options, env, self) => {
        const token = tokens[idx]
        const info = token.info.trim()
        const content = token.content
        
        // 处理 markmap 代码块
        if (info === 'markmap') {
          const encoded = btoa(unescape(encodeURIComponent(content)))
          return `<Markmap content-base64="${encoded}" />`
        }
        
        // 处理带容器的 mermaid 代码块 (mermaid-box)
        if (info.startsWith('mermaid-box')) {
          const encoded = btoa(unescape(encodeURIComponent(content)))
          // 解析可选的标题参数，如 mermaid-box{title="流程图"}
          const titleMatch = info.match(/title="([^"]*)"/)
          const title = titleMatch ? titleMatch[1] : ''
          return `<MermaidWrapper content-base64="${encoded}" ${title ? `title="${title}"` : ''} />`
        }
        
        return defaultFence(tokens, idx, options, env, self)
      }
    }
  },

  cleanUrls: true,
  lastUpdated: true,
  ignoreDeadLinks: true
}))
