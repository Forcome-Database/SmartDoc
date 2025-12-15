# API 连接问题排查

## 问题现象

前端请求显示"待处理"（pending）状态，最终超时失败。

## 可能原因

### 1. 后端服务未启动（最常见）

**检查方法：**
```bash
netstat -ano | findstr :8000
```

**解决方案：**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**预期输出：**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 2. 端口配置不匹配

检查前端代理配置 `frontend/vite.config.js`：
```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',  // 确认端口正确
    changeOrigin: true,
    secure: false
  }
}
```

### 3. CORS 跨域问题

检查浏览器控制台是否有 CORS 错误。

### 4. 请求超时

当前配置：`timeout: 30000` (30秒)

如果后端查询很慢，可以增加超时时间：
```javascript
// frontend/src/api/request.js
const request = axios.create({
  timeout: 60000,  // 增加到 60 秒
})
```

## 快速诊断步骤

### 步骤 1：检查后端服务

```bash
# Windows PowerShell
Get-Process | Where-Object {$_.ProcessName -like "*python*"}
netstat -ano | findstr :8000
```

### 步骤 2：启动后端服务

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 步骤 3：测试后端 API

访问：
- Swagger UI: http://localhost:8000/api/docs
- 健康检查: http://localhost:8000/health

### 步骤 4：检查前端代理

确保前端开发服务器正在运行：
```bash
cd frontend
npm run dev
```

### 步骤 5：检查浏览器网络面板

1. 打开开发者工具（F12）
2. 切换到"网络"标签
3. 刷新页面
4. 查看请求状态

## 调试技巧

### 查看详细的网络请求

```javascript
// 在浏览器控制台执行
fetch('http://localhost:8000/api/v1/dashboard/metrics?time_range=7days', {
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('access_token')
  }
})
.then(res => res.json())
.then(data => console.log(data))
.catch(err => console.error(err))
```

### 检查环境变量

```javascript
// 在浏览器控制台
console.log(import.meta.env.VITE_API_BASE_URL)
```

## 快速修复脚本

创建 `start-dev.bat`：
```batch
@echo off
echo Starting Enterprise IDP Platform...

echo [1/2] Starting Backend...
start cmd /k "cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 5

echo [2/2] Starting Frontend...
start cmd /k "cd frontend && npm run dev"

echo Done!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
```
