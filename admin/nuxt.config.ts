// https://nuxt.com/docs/api/configuration/nuxt-config
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'
import { config } from 'dotenv'

const __dirname = dirname(fileURLToPath(import.meta.url))

// 加载根目录的 .env 文件
config({ path: resolve(__dirname, '../.env') })

export default defineNuxtConfig({
  // 保持 Nuxt 3 目录结构（Nuxt 4 默认使用 app/ 目录）
  srcDir: '.',

  devtools: { enabled: true },

  // 禁用遥测
  telemetry: false,

  // 开发服务器配置 - 允许局域网访问
  devServer: {
    host: '0.0.0.0',
    port: 3000,
  },

  modules: [
    '@nuxt/ui',
    '@pinia/nuxt',
    '@vueuse/nuxt',
    'nuxt-auth-utils',
  ],

  // 共享组件别名 - 使用绝对路径
  alias: {
    '@shared': resolve(__dirname, '../shared'),
    '@docs-components': resolve(__dirname, '../docs/.vitepress/theme/components'),
  },

  // 自动导入 docs 组件
  components: [
    { path: '~/components' },
    { path: resolve(__dirname, '../docs/.vitepress/theme/components'), prefix: 'Docs' },
  ],

  // Tailwind CSS v4
  css: ['~/assets/css/main.css'],

  // 运行时配置
  runtimeConfig: {
    // Session 配置 (nuxt-auth-utils)
    session: {
      maxAge: 60 * 60 * 24 * 7, // 1 week
      name: 'nuxt-session',
      password: process.env.NUXT_SESSION_PASSWORD || '',
      cookie: {
        sameSite: 'lax',
        // 开发环境使用 HTTP，生产环境使用 HTTPS
        secure: process.env.NODE_ENV === 'production',
        httpOnly: true,
      },
    },
    // 服务端私有
    databaseUrl: process.env.DATABASE_URL,
    dingtalkAppKey: process.env.DINGTALK_APP_KEY,
    dingtalkAppSecret: process.env.DINGTALK_APP_SECRET,
    dingtalkAgentId: process.env.DINGTALK_AGENT_ID,
    openaiApiKey: process.env.OPENAI_API_KEY,
    openaiBaseUrl: process.env.OPENAI_BASE_URL,
    docsRoot: process.env.DOCS_ROOT || '../docs',
    sessionPassword: process.env.NUXT_SESSION_PASSWORD,
    // MinIO 配置
    minioEndpoint: process.env.MINIO_ENDPOINT,
    minioPort: process.env.MINIO_PORT || '9000',
    minioUseSSL: process.env.MINIO_USE_SSL || 'false',
    minioAccessKey: process.env.MINIO_ACCESS_KEY,
    minioSecretKey: process.env.MINIO_SECRET_KEY,
    minioBucket: process.env.MINIO_BUCKET || 'forcome-docs',
    minioPublicUrl: process.env.MINIO_PUBLIC_URL,
    // 客户端公开
    public: {
      appName: 'FORCOME 知识库管理',
      dingtalkAppKey: process.env.DINGTALK_APP_KEY,
    },
  },

  // Nitro 服务端配置
  nitro: {
    experimental: {
      asyncContext: true,
    },
  },

  // @nuxt/ui 配置 - 禁用内置字体模块，使用 CSS 直接导入 @fontsource 字体
  // 字体已在 assets/css/main.css 中通过 @import "@fontsource-variable/inter" 导入
  ui: {
    fonts: false,
  },

  // 图标配置 - 使用本地图标包
  icon: {
    // 明确指定使用的图标集合
    serverBundle: {
      collections: ['lucide', 'simple-icons'],
    },
    // 客户端预打包常用图标，减少网络请求
    clientBundle: {
      scan: true,
    },
  },

  compatibilityDate: '2025-01-01',
})
