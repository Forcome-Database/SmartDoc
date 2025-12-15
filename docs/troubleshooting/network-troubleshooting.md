# 网络问题排查

## 快速诊断（5分钟）

### 1. 检查浏览器开发者工具

按 `F12` 打开开发者工具，切换到 `Network` 标签：

| 现象 | 原因 | 解决方法 |
|------|------|----------|
| 401 Unauthorized | 未登录或 Token 过期 | 清除缓存并重新登录 |
| 请求一直 Pending | 后端未响应 | 检查后端是否启动 |
| ERR_CONNECTION_REFUSED | 后端未启动 | 启动后端服务 |
| Timeout | 请求超时 | 检查后端日志 |
| CORS Error | 跨域配置问题 | 检查后端 CORS 配置 |

### 2. 检查 localStorage

在 Console 中执行：
```javascript
console.log('Token:', localStorage.getItem('access_token'))
console.log('User:', localStorage.getItem('user_info'))
```

### 3. 测试后端健康检查

访问：http://localhost:8000/health

## 常见问题解决

### 401 认证错误

```javascript
// 在浏览器 Console 执行
localStorage.clear()
location.href = '/login'
```

### 请求一直 Pending

**检查后端是否启动：**
```bash
netstat -ano | findstr :8000
```

**检查 Vite 代理配置：**
```javascript
// frontend/vite.config.js
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    secure: false
  }
}
```

**重启服务：**
```bash
taskkill /F /IM python.exe
.\start-dev.bat
```

### CORS 错误

检查后端 CORS 配置（`backend/main.py`）：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 数据库查询慢

添加索引：
```sql
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_rule_id ON tasks(rule_id);
```

### Redis 连接失败

Redis 连接失败不会导致服务无法启动，只是限流功能会被禁用。

## 诊断报告模板

如果问题仍未解决，请收集：

1. **浏览器信息**
   - 浏览器类型和版本
   - Console 错误截图
   - Network 标签截图

2. **后端信息**
   - 后端启动日志
   - 是否看到请求日志

3. **环境信息**
   - Python 版本：`python --version`
   - Node 版本：`node --version`
   - 端口占用：`netstat -ano | findstr :8000`
