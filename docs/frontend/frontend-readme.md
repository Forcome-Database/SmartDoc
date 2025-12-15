# 前端项目说明

## 技术栈

- **框架**: Vue 3.5 (Composition API with `<script setup>`)
- **构建工具**: Vite 5
- **UI库**: Ant Design Vue 4.2
- **状态管理**: Pinia
- **样式**: Tailwind CSS 3.4
- **HTTP客户端**: Axios
- **图表**: ECharts 5 with vue-echarts

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API模块
│   │   ├── auth.js       # 认证API
│   │   ├── task.js       # 任务管理API
│   │   ├── rule.js       # 规则管理API
│   │   ├── dashboard.js  # 仪表盘API
│   │   ├── request.js    # Axios实例
│   │   └── index.js      # API导出
│   ├── components/       # 可复用组件
│   │   └── Layout/       # 布局组件
│   ├── views/            # 页面组件
│   ├── router/           # Vue Router配置
│   ├── stores/           # Pinia stores
│   ├── utils/            # 工具函数
│   ├── App.vue           # 根组件
│   ├── main.js           # 应用入口
│   └── style.css         # 全局样式
├── vite.config.js        # Vite配置
├── tailwind.config.js    # Tailwind配置
└── package.json          # 依赖配置
```

## 开发命令

```bash
npm install      # 安装依赖
npm run dev      # 启动开发服务器
npm run build    # 构建生产版本
npm run preview  # 预览生产构建
npm run lint     # 代码检查
```

## 环境变量

```bash
VITE_API_BASE_URL=/api
VITE_API_TARGET=http://localhost:8000
VITE_APP_TITLE=Enterprise IDP Platform
VITE_APP_VERSION=1.0.0
```

## API 代理配置

开发服务器代理 API 请求到后端：
- `/api/*` → `http://localhost:8000/api/*`

## 代码规范

- 使用 Vue 3 Composition API with `<script setup>`
- JavaScript 使用 camelCase
- Vue 组件使用 PascalCase
- 模板中组件使用 kebab-case

## 已实现功能

- ✅ 认证系统（登录、登出、Token管理）
- ✅ API层（Axios实例、拦截器）
- ✅ 工具函数（常量、格式化）
- ✅ 布局系统（Header、Sidebar、Content）
- ✅ 仪表盘
- ✅ 规则管理
- ✅ 任务列表
- ✅ 审核工作台
- ✅ Webhook配置
- ✅ 用户管理
- ✅ 系统设置
