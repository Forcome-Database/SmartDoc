# 用户管理 API

## 端点列表

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | /api/v1/users | Admin | 获取用户列表 |
| POST | /api/v1/users | Admin | 创建用户 |
| GET | /api/v1/users/{id} | Admin | 获取用户详情 |
| PUT | /api/v1/users/{id} | Admin | 更新用户信息 |
| PATCH | /api/v1/users/{id}/status | Admin | 更新用户状态 |
| DELETE | /api/v1/users/{id} | Admin | 删除用户 |

## 角色类型

- `admin`: 超级管理员
- `architect`: 规则架构师
- `auditor`: 业务审核员
- `visitor`: API访客

## 创建用户

```bash
POST /api/v1/users
Content-Type: application/json

{
  "username": "new_user",
  "email": "user@example.com",
  "password": "password123",
  "role": "architect"
}
```

## 更新用户

```bash
PUT /api/v1/users/{user_id}
Content-Type: application/json

{
  "email": "new_email@example.com",
  "role": "auditor"
}
```

## 修改密码

```bash
PUT /api/v1/users/{user_id}
Content-Type: application/json

{
  "old_password": "oldpass",
  "new_password": "newpass"
}
```

## 禁用用户

```bash
PATCH /api/v1/users/{user_id}/status
Content-Type: application/json

{
  "is_active": false
}
```

## 筛选参数

- `username`: 用户名（模糊匹配）
- `email`: 邮箱（模糊匹配）
- `role`: 角色（精确匹配）
- `is_active`: 状态
- `page`: 页码
- `page_size`: 每页数量

## 限制

- 不能禁用或删除自己的账号
- 不能删除最后一个Admin用户
- 用户名和邮箱必须唯一
