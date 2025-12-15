# 认证流程测试指南

## 前置条件

1. 后端服务运行中
2. 数据库已初始化
3. 前端开发服务器运行中

## 测试步骤

### 1. 正常登录

1. 访问 http://localhost:5173/login
2. 输入用户名：`admin`
3. 输入密码：`admin123`
4. 点击"登录"

**预期结果：**
- 显示"登录成功"
- 跳转到 /dashboard
- Header显示用户名和角色

### 2. 错误密码

1. 输入错误密码
2. 点击"登录"

**预期结果：**
- 显示"用户名或密码错误"
- 停留在登录页面

### 3. 页面刷新

1. 登录成功后刷新页面

**预期结果：**
- 保持登录状态
- 不会跳转到登录页

### 4. 路由守卫

1. 清除 localStorage
2. 访问 /dashboard

**预期结果：**
- 重定向到 /login?redirect=/dashboard
- 登录后跳转回 /dashboard

### 5. 登出

1. 点击用户头像
2. 点击"退出登录"
3. 确认

**预期结果：**
- 显示"已退出登录"
- 跳转到 /login
- localStorage 被清除

## localStorage 检查

```javascript
console.log('Token:', localStorage.getItem('access_token'))
console.log('User:', localStorage.getItem('user_info'))
```

## 角色权限

| 角色 | 可见菜单 |
|------|---------|
| Admin | 全部 |
| Architect | 仪表盘、规则管理、任务列表 |
| Auditor | 仪表盘、任务列表、审核工作台 |
| Visitor | API密钥管理 |

## 常见问题

### 登录后立即跳转到登录页

**排查：**
1. 检查 localStorage 是否有 `access_token`
2. 检查控制台错误
3. 检查 `authStore.isAuthenticated`

### 刷新页面后丢失登录状态

**排查：**
1. 检查 main.js 是否调用 `authStore.initAuth()`
2. 检查 localStorage 是否持久化

### 401 错误但未跳转到登录页

**排查：**
1. 检查 `frontend/src/api/request.js` 响应拦截器
