# API模块使用指南

## 概述

本目录包含所有与后端API交互的模块，提供统一的请求封装和错误处理。

## 目录结构

```
api/
├── request.js      # Axios配置和拦截器
├── auth.js         # 认证相关API
├── task.js         # 任务管理API
├── rule.js         # 规则管理API
├── webhook.js      # Webhook配置API
├── user.js         # 用户管理API
├── system.js       # 系统配置API
├── dashboard.js    # 仪表盘数据API
├── audit.js        # 审核工作台API
├── auditLog.js     # 审计日志API
└── index.js        # 统一导出
```

## 使用方法

### 1. 导入API模块

```javascript
// 导入单个API模块
import { taskAPI } from '@/api'

// 导入多个API模块
import { taskAPI, ruleAPI, authAPI } from '@/api'

// 导入request实例（用于自定义请求）
import { request } from '@/api'
```

### 2. 调用API

所有API模块都使用统一的调用方式：

```javascript
// GET请求 - 获取列表
const response = await taskAPI.list({
  page: 1,
  page_size: 20,
  status: 'pending_audit'
})

// GET请求 - 获取详情
const task = await taskAPI.get('T_20251214_0001')

// POST请求 - 创建资源
const newRule = await ruleAPI.create({
  name: '发票识别规则',
  code: 'INVOICE_001',
  document_type: '发票'
})

// PUT请求 - 更新资源
const updated = await ruleAPI.update('RULE001', {
  name: '更新后的规则名称'
})

// DELETE请求 - 删除资源
await ruleAPI.delete('RULE001')
```

### 3. 文件上传

```javascript
// 创建FormData（支持单个或多个文件）
const formData = new FormData()
// 统一使用 files 字段名
formData.append('files', file1)
formData.append('files', file2)  // 可选，支持多文件
formData.append('rule_id', 'RULE001')

// 上传文件
const response = await taskAPI.upload(formData)
```

### 4. 文件下载

```javascript
// 导出任务
await taskStore.exportTasks({
  format: 'csv',
  status: 'completed'
})
```

## API响应格式

所有API响应都遵循统一的格式：

```javascript
{
  code: 200,           // 状态码
  message: "成功",     // 消息
  data: {              // 数据
    // 具体数据内容
  }
}
```

## 错误处理

### 自动错误处理

响应拦截器会自动处理以下错误：

- **400**: 请求参数错误
- **401**: 未认证（自动跳转登录页）
- **403**: 无权限访问
- **404**: 资源不存在
- **429**: 请求过于频繁
- **500**: 服务器错误
- **502/503/504**: 服务不可用

### 手动错误处理

```javascript
try {
  const response = await taskAPI.get('TASK001')
  // 处理成功响应
} catch (error) {
  // 处理错误
  console.error('获取任务失败:', error)
}
```

## 认证Token

### 自动添加Token

请求拦截器会自动从localStorage读取Token并添加到请求头：

```javascript
Authorization: Bearer <token>
```

### 手动设置Token

```javascript
// 登录后设置Token
const response = await authAPI.login({
  username: 'admin',
  password: 'password'
})

if (response.code === 200) {
  localStorage.setItem('access_token', response.data.access_token)
}
```

## 环境配置

在`.env`文件中配置API基础URL：

```bash
# 开发环境
VITE_API_BASE_URL=http://localhost:8000/api

# 生产环境
VITE_API_BASE_URL=/api
```

## API模块详解

### authAPI - 认证API

```javascript
// 登录
await authAPI.login({ username, password })

// 登出
await authAPI.logout()

// 获取当前用户信息
await authAPI.getCurrentUser()

// 刷新Token
await authAPI.refreshToken()
```

### taskAPI - 任务API

```javascript
// 获取任务列表
await taskAPI.list({ page, page_size, status })

// 获取任务详情
await taskAPI.get(taskId)

// 上传文件
await taskAPI.upload(formData)

// 更新任务状态
await taskAPI.updateStatus(taskId, { status, data })

// 导出任务
await taskAPI.export({ format, status })
```

### ruleAPI - 规则API

```javascript
// 获取规则列表
await ruleAPI.list({ page, page_size })

// 获取规则详情
await ruleAPI.get(ruleId)

// 创建规则
await ruleAPI.create(data)

// 更新规则
await ruleAPI.update(ruleId, data)

// 删除规则
await ruleAPI.delete(ruleId)

// 获取版本列表
await ruleAPI.getVersions(ruleId)

// 更新版本配置
await ruleAPI.updateVersion(ruleId, version, config)

// 发布规则
await ruleAPI.publish(ruleId)

// 回滚规则
await ruleAPI.rollback(ruleId, version)

// 沙箱测试
await ruleAPI.sandbox(ruleId, formData)
```

### webhookAPI - Webhook API

```javascript
// 获取Webhook列表
await webhookAPI.list()

// 获取Webhook详情
await webhookAPI.get(webhookId)

// 创建Webhook
await webhookAPI.create(data)

// 更新Webhook
await webhookAPI.update(webhookId, data)

// 删除Webhook
await webhookAPI.delete(webhookId)

// 测试Webhook
await webhookAPI.test(webhookId)

// 获取规则关联的Webhook
await webhookAPI.getRuleWebhooks(ruleId)

// 关联规则和Webhook
await webhookAPI.associateRule(ruleId, webhookId)

// 解除关联
await webhookAPI.disassociateRule(ruleId, webhookId)
```

### userAPI - 用户API

```javascript
// 获取用户列表
await userAPI.list({ page, page_size, role })

// 获取用户详情
await userAPI.get(userId)

// 创建用户
await userAPI.create({ username, email, password, role })

// 更新用户
await userAPI.update(userId, data)

// 更新用户状态
await userAPI.updateStatus(userId, isActive)

// 删除用户
await userAPI.delete(userId)

// 获取API Key列表
await userAPI.getApiKeys()

// 生成API Key
await userAPI.createApiKey({ expires_days })

// 撤销API Key
await userAPI.revokeApiKey(keyId)
```

### systemAPI - 系统API

```javascript
// 获取系统配置
await systemAPI.getConfigs()

// 更新系统配置
await systemAPI.updateConfig(key, value)

// 获取数据生命周期配置
await systemAPI.getRetentionConfig()

// 更新数据生命周期配置
await systemAPI.updateRetentionConfig({
  file_retention_days: 30,
  data_retention_days: -1
})
```

### dashboardAPI - 仪表盘API

```javascript
// 获取核心指标
await dashboardAPI.getMetrics({ time_range: '7days' })

// 获取任务吞吐趋势
await dashboardAPI.getThroughput({ time_range: '7days' })

// 获取异常分布
await dashboardAPI.getExceptions({ time_range: '7days' })

// 获取规则效能
await dashboardAPI.getRulePerformance({ time_range: '7days' })
```

## 最佳实践

### 1. 使用Store管理API调用

推荐在Store中封装API调用，而不是直接在组件中调用：

```javascript
// ❌ 不推荐：在组件中直接调用
const response = await taskAPI.list()

// ✅ 推荐：通过Store调用
const taskStore = useTaskStore()
await taskStore.fetchTasks()
```

### 2. 统一错误处理

```javascript
async function fetchData() {
  try {
    const response = await taskAPI.list()
    // 处理数据
  } catch (error) {
    // 错误已经被拦截器处理，这里只需要记录或执行特殊逻辑
    console.error('获取数据失败:', error)
  }
}
```

### 3. 加载状态管理

```javascript
const loading = ref(false)

async function loadData() {
  loading.value = true
  try {
    await taskAPI.list()
  } finally {
    loading.value = false
  }
}
```

### 4. 请求取消

对于可能重复触发的请求，建议实现请求取消：

```javascript
let cancelToken = null

async function search(keyword) {
  // 取消之前的请求
  if (cancelToken) {
    cancelToken.cancel('新的搜索请求')
  }
  
  // 创建新的取消令牌
  cancelToken = axios.CancelToken.source()
  
  try {
    const response = await taskAPI.list({
      search: keyword
    }, {
      cancelToken: cancelToken.token
    })
  } catch (error) {
    if (axios.isCancel(error)) {
      console.log('请求已取消:', error.message)
    }
  }
}
```

## 调试技巧

### 开发环境日志

在开发环境中，请求和响应会自动打印到控制台：

```
[Request] GET /api/v1/tasks { params: { page: 1 } }
[Response] GET /api/v1/tasks { code: 200, data: {...} }
```

### 查看网络请求

使用浏览器开发者工具的Network面板查看详细的请求信息。

### 模拟错误

```javascript
// 模拟401错误
localStorage.removeItem('access_token')
await taskAPI.list() // 将自动跳转到登录页

// 模拟网络错误
// 断开网络连接后发起请求
```

## 常见问题

### Q: 如何处理Token过期？

A: 响应拦截器会自动处理401错误，清除Token并跳转到登录页。

### Q: 如何自定义请求超时时间？

A: 在调用API时传入配置：

```javascript
await taskAPI.list({}, { timeout: 60000 }) // 60秒
```

### Q: 如何添加自定义请求头？

A: 使用request实例直接发起请求：

```javascript
import { request } from '@/api'

await request.get('/custom-endpoint', {
  headers: {
    'X-Custom-Header': 'value'
  }
})
```

### Q: 如何处理文件下载？

A: 设置responseType为blob：

```javascript
const response = await request.get('/download', {
  responseType: 'blob'
})

// 创建下载链接
const url = window.URL.createObjectURL(new Blob([response]))
const link = document.createElement('a')
link.href = url
link.download = 'filename.pdf'
link.click()
```
