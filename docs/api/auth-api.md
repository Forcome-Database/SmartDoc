# 认证授权 API

## 端点列表

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | /api/v1/auth/login | 用户登录 |
| POST | /api/v1/auth/logout | 用户登出 |
| GET | /api/v1/auth/me | 获取当前用户信息 |
| POST | /api/v1/auth/refresh | 刷新Token |

## 用户登录

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

## 获取当前用户

```bash
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "id": "U_20251214_0001",
  "username": "admin",
  "email": "admin@example.com",
  "role": "admin",
  "is_active": true
}
```

## 权限依赖注入

```python
from app.core.dependencies import require_role, require_admin

# 方式1：使用装饰器工厂
@router.post("/rules")
async def create_rule(
    current_user: User = Depends(require_role("admin", "architect"))
):
    ...

# 方式2：使用预定义依赖
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin)
):
    ...
```

## API 限流

使用 Redis 实现分布式限流，滑动窗口算法。

| 端点 | 限制 |
|------|------|
| /api/v1/ocr/upload | 100次/分钟 |
| /api/v1/tasks | 1000次/分钟 |
| /api/v1/rules | 500次/分钟 |
| 默认 | 200次/分钟 |

**响应头：**
- `X-RateLimit-Limit`: 限流阈值
- `X-RateLimit-Remaining`: 剩余请求次数
- `X-RateLimit-Reset`: 重置时间戳

## 安全特性

- JWT Token：HS256算法，默认30分钟过期
- 密码加密：bcrypt算法
- 安全响应头：防止XSS、点击劫持
- 请求日志：记录所有API访问
