# Webhook API

## 端点列表

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | /api/v1/webhooks | Admin | 获取Webhook列表 |
| POST | /api/v1/webhooks | Admin | 创建Webhook |
| GET | /api/v1/webhooks/{id} | Admin | 获取Webhook详情 |
| PUT | /api/v1/webhooks/{id} | Admin | 更新Webhook |
| DELETE | /api/v1/webhooks/{id} | Admin | 删除Webhook |
| POST | /api/v1/webhooks/{id}/test | Admin | 测试连通性 |

## 认证类型

- `none`: 无认证
- `basic`: Basic Auth
- `bearer`: Bearer Token
- `api_key`: API Key

## 创建 Webhook

```bash
POST /api/v1/webhooks
Content-Type: application/json

{
  "name": "下游系统A",
  "endpoint_url": "https://api.example.com/webhook",
  "auth_type": "bearer",
  "auth_config": {
    "token": "downstream_bearer_token"
  },
  "secret_key": "hmac_secret_key",
  "request_template": {
    "task_id": "{{task_id}}",
    "result": "{{result_json}}",
    "file_url": "{{file_url}}"
  },
  "is_active": true
}
```

## 模版变量

| 变量 | 说明 |
|------|------|
| `{{task_id}}` | 任务ID |
| `{{result_json}}` | 提取结果JSON |
| `{{file_url}}` | 文件预签名URL |
| `{{meta_info}}` | 任务元信息 |

## 测试连通性

```bash
POST /api/v1/webhooks/WH_ABC123/test
Content-Type: application/json

{
  "mock_data": {
    "task_id": "T_TEST_001",
    "result": {"field1": "value1"},
    "file_url": "https://storage.example.com/test.pdf"
  }
}
```

## 安全特性

- 敏感信息加密存储
- API响应中敏感信息脱敏
- HMAC-SHA256 签名（放入 `X-IDP-Signature` 请求头）
- 5秒超时限制
