# Webhook组件

## 概述

Webhook组件用于管理下游业务系统的回调接口配置，支持多种鉴权方式和自定义请求体模版。

## 组件列表

### WebhookDialog.vue

Webhook配置对话框组件，用于创建和编辑Webhook配置。

#### 功能特性

1. **基础配置**
   - 系统名称：标识下游系统
   - Endpoint URL：回调接口地址
   - 状态开关：启用/禁用

2. **鉴权方式**
   - 无鉴权（None）
   - Basic Auth：用户名+密码
   - Bearer Token：Token认证
   - API Key：自定义Header认证

3. **安全签名**
   - Secret Key：用于HMAC-SHA256签名
   - 系统自动在请求头添加X-IDP-Signature

4. **请求体模版**
   - JSON格式编辑器
   - 支持变量注入：
     - `{{task_id}}`：任务ID
     - `{{result_json}}`：提取结果JSON
     - `{{file_url}}`：文件访问URL
     - `{{meta_info}}`：任务元信息
   - 实时JSON格式验证

#### Props

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| visible | Boolean | false | 对话框是否可见 |
| webhook | Object | null | 编辑的Webhook对象（null表示新建） |

#### Events

| 事件名 | 参数 | 说明 |
|--------|------|------|
| update:visible | Boolean | 更新对话框可见状态 |
| success | Object | 表单提交成功，返回表单数据 |

#### 使用示例

```vue
<template>
  <WebhookDialog
    v-model:visible="dialogVisible"
    :webhook="currentWebhook"
    @success="handleDialogSuccess"
  />
</template>

<script setup>
import { ref } from 'vue'
import WebhookDialog from '@/components/Webhook/WebhookDialog.vue'

const dialogVisible = ref(false)
const currentWebhook = ref(null)

function handleDialogSuccess(formData) {
  console.log('表单数据:', formData)
  // 处理保存逻辑
}
</script>
```

## 页面使用

### WebhookConfig.vue

Webhook配置管理页面，提供完整的CRUD功能。

#### 功能特性

1. **列表展示**
   - 系统名称
   - Endpoint URL（支持省略显示和Tooltip）
   - 鉴权方式（带颜色标签）
   - 状态（启用/禁用）

2. **操作功能**
   - 新建：创建新的Webhook配置
   - 编辑：修改现有配置
   - 删除：删除配置（带二次确认）
   - 测试：发送测试请求验证连通性

3. **连通性测试**
   - 使用Mock数据发送测试请求
   - 显示HTTP状态码
   - 显示响应头
   - 显示响应体
   - 显示请求耗时
   - 5秒超时限制

#### 路由配置

```javascript
{
  path: 'webhooks',
  name: 'WebhookConfig',
  component: () => import('@/views/WebhookConfig.vue'),
  meta: { 
    title: 'Webhook配置',
    icon: 'ApiOutlined',
    roles: ['admin']  // 仅管理员可访问
  }
}
```

## API接口

### webhook.js

提供Webhook相关的API接口封装。

#### 接口列表

| 方法 | 说明 |
|------|------|
| getWebhookList() | 获取Webhook列表 |
| getWebhookDetail(webhookId) | 获取Webhook详情 |
| createWebhook(data) | 创建Webhook |
| updateWebhook(webhookId, data) | 更新Webhook |
| deleteWebhook(webhookId) | 删除Webhook |
| testWebhook(webhookId) | 测试Webhook连通性 |
| getRuleWebhooks(ruleId) | 获取规则关联的Webhook列表 |
| associateRuleWebhook(ruleId, webhookId) | 关联规则和Webhook |
| disassociateRuleWebhook(ruleId, webhookId) | 解除规则和Webhook关联 |

#### 使用示例

```javascript
import { 
  getWebhookList, 
  createWebhook, 
  testWebhook 
} from '@/api/webhook'

// 获取列表
const response = await getWebhookList()
const webhooks = response.data

// 创建Webhook
await createWebhook({
  name: '财务系统',
  endpoint_url: 'https://api.example.com/webhook',
  auth_type: 'bearer',
  auth_config: { token: 'your-token' },
  secret_key: 'your-secret',
  request_template: {
    task_id: '{{task_id}}',
    data: '{{result_json}}'
  },
  is_active: true
})

// 测试连通性
const testResult = await testWebhook(webhookId)
console.log('状态码:', testResult.data.status)
console.log('响应体:', testResult.data.response_body)
```

## 数据结构

### Webhook对象

```typescript
interface Webhook {
  id: string                    // Webhook ID
  name: string                  // 系统名称
  endpoint_url: string          // Endpoint URL
  auth_type: 'none' | 'basic' | 'bearer' | 'api_key'  // 鉴权方式
  auth_config: {                // 鉴权配置
    username?: string           // Basic Auth用户名
    password?: string           // Basic Auth密码
    token?: string              // Bearer Token
    header_name?: string        // API Key Header名称
    api_key?: string            // API Key值
  }
  secret_key: string            // HMAC签名密钥
  request_template: object      // 请求体模版（JSON对象）
  is_active: boolean            // 是否启用
  created_at: string            // 创建时间
  updated_at: string            // 更新时间
}
```

### 测试结果对象

```typescript
interface TestResult {
  status: number                // HTTP状态码
  response_headers: object      // 响应头
  response_body: string | object  // 响应体
  duration_ms: number           // 耗时（毫秒）
}
```

## 样式说明

### 响应式设计

- 桌面端：完整布局，表格横向滚动
- 移动端：
  - 页面头部改为纵向布局
  - 按钮占满宽度
  - 表格自适应

### 主题色

- 鉴权方式标签：
  - 无鉴权：default（灰色）
  - Basic Auth：blue（蓝色）
  - Bearer Token：green（绿色）
  - API Key：purple（紫色）

- 状态徽章：
  - 启用：success（绿色）
  - 禁用：default（灰色）

## 注意事项

1. **权限控制**
   - Webhook配置页面仅管理员（admin）可访问
   - 需要在路由守卫中验证用户角色

2. **数据验证**
   - Endpoint URL必须是有效的URL格式
   - 请求体模版必须是有效的JSON格式
   - 鉴权配置根据鉴权方式进行必填验证

3. **安全性**
   - Secret Key使用密码输入框，不明文显示
   - 鉴权配置中的密码和Token使用密码输入框
   - 后端应对敏感字段进行加密存储

4. **用户体验**
   - 删除操作需要二次确认
   - 测试按钮显示加载状态
   - 长URL使用省略显示和Tooltip
   - JSON编辑器提供变量插入辅助

5. **错误处理**
   - API调用失败显示错误提示
   - JSON格式错误实时提示
   - 表单验证失败阻止提交

## 后续优化

1. **功能增强**
   - 支持批量测试
   - 支持测试历史记录
   - 支持Webhook日志查看
   - 支持请求体模版预览

2. **性能优化**
   - 列表分页
   - 虚拟滚动
   - 请求防抖

3. **用户体验**
   - 拖拽排序
   - 批量操作
   - 导入导出配置
   - 模版库
