# Webhook推送服务使用说明

## 概述

`push_service.py` 实现了完整的Webhook推送功能，包括：
- 推送核心逻辑（模版渲染、签名生成、HTTP请求）
- 推送日志记录
- 指数退避重试机制
- 死信队列处理

## 核心功能

### 1. 推送核心（push_to_webhook）

推送任务结果到Webhook目标，支持：
- 请求体模版变量替换（{{task_id}}、{{result_json}}、{{file_url}}、{{meta_info}}）
- HMAC-SHA256签名生成
- 多种认证方式（Basic Auth、Bearer Token、API Key）
- 自动记录推送日志

```python
from app.services.push_service import PushService

# 创建推送服务实例
push_service = PushService(db)

# 推送到单个Webhook
result = await push_service.push_to_webhook(task, webhook, retry_count=0)

if result.success:
    print(f"推送成功: status={result.http_status}, duration={result.duration_ms}ms")
else:
    print(f"推送失败: {result.error_message}")
```

### 2. 推送日志记录（save_push_log）

自动记录每次推送的详细信息：
- HTTP状态码
- 请求头和请求体
- 响应头和响应体
- 耗时（毫秒）
- 重试次数
- 错误信息

```python
# 保存推送日志（通常由push_to_webhook自动调用）
log = await push_service.save_push_log(
    task_id="T_20251214_0001",
    webhook_id="WH_001",
    http_status=200,
    request_headers={"Content-Type": "application/json"},
    request_body='{"task_id": "T_20251214_0001"}',
    response_headers={"Content-Type": "application/json"},
    response_body='{"success": true}',
    duration_ms=150,
    retry_count=0
)

# 查询推送日志
logs = await push_service.get_push_logs(task_id="T_20251214_0001")
for log in logs:
    print(f"Log {log.id}: status={log.http_status}, retry={log.retry_count}")
```

### 3. 指数退避重试（push_with_retry）

自动重试失败的推送，使用指数退避算法：
- 第1次重试：延迟10秒
- 第2次重试：延迟30秒
- 第3次重试：延迟90秒
- 最多重试3次

```python
# 推送并自动重试
result = await push_service.push_with_retry(task, webhook, max_retries=3)

if result.success:
    print("推送成功（可能经过重试）")
else:
    print("推送失败，已达最大重试次数")
```

### 4. 死信队列处理（move_to_dlq）

将推送失败的任务移入死信队列：
- 更新任务状态为PUSH_FAILED
- 记录失败原因和重试次数
- 支持手动重推

```python
# 移入死信队列
success = await push_service.move_to_dlq(
    task_id="T_20251214_0001",
    webhook_id="WH_001",
    failure_reason="连接超时",
    retry_count=3
)

# 获取死信队列任务
dlq_tasks = await push_service.get_dlq_tasks(limit=100, offset=0)
print(f"死信队列中有 {len(dlq_tasks)} 个任务")

# 手动重推死信队列任务
retry_result = await push_service.retry_dlq_task(
    task_id="T_20251214_0001",
    webhook_id="WH_001"  # 可选，不指定则推送到所有关联Webhook
)

if retry_result["success"]:
    print("重推成功")
else:
    print(f"重推失败: {retry_result['message']}")
```

### 5. 批量推送（batch_push）

并行推送到多个Webhook目标：

```python
# 批量推送
webhooks = task.rule.webhooks  # 获取规则关联的所有Webhook
results = await push_service.batch_push(task, webhooks)

for i, result in enumerate(results):
    webhook = webhooks[i]
    if result.success:
        print(f"推送到 {webhook.name} 成功")
    else:
        print(f"推送到 {webhook.name} 失败: {result.error_message}")
```

## 请求体模版变量

支持以下变量替换：

| 变量 | 说明 | 示例 |
|------|------|------|
| `{{task_id}}` | 任务ID | "T_20251214_0001" |
| `{{result_json}}` | 提取结果JSON对象 | {"name": "张三", "amount": 1000} |
| `{{file_url}}` | 文件预签名URL（1小时有效） | "https://minio.example.com/..." |
| `{{meta_info}}` | 任务元信息对象 | {"file_name": "invoice.pdf", "page_count": 3, ...} |

### 模版示例

```json
{
  "task_id": "{{task_id}}",
  "data": {{result_json}},
  "file_url": "{{file_url}}",
  "metadata": {{meta_info}}
}
```

渲染后：

```json
{
  "task_id": "T_20251214_0001",
  "data": {
    "invoice_number": "INV-2025-001",
    "amount": 1000.00
  },
  "file_url": "https://minio.example.com/idp-files/2025/01/14/T_20251214_0001/invoice.pdf?...",
  "metadata": {
    "file_name": "invoice.pdf",
    "page_count": 3,
    "rule_id": "RULE_001",
    "rule_version": "V1.0",
    "created_at": "2025-01-14T10:30:00",
    "completed_at": "2025-01-14T10:30:15",
    "confidence_scores": {"invoice_number": 95, "amount": 88},
    "llm_token_count": 1500,
    "llm_cost": 3.0
  }
}
```

## 认证方式

### 1. 无认证（None）

```python
webhook.auth_type = AuthType.NONE
# 不添加任何认证信息
```

### 2. Basic Auth

```python
webhook.auth_type = AuthType.BASIC
webhook.auth_config = {
    "username": "api_user",
    "password": "encrypted_password"  # 加密存储
}
# 添加 Authorization: Basic base64(username:password)
```

### 3. Bearer Token

```python
webhook.auth_type = AuthType.BEARER
webhook.auth_config = {
    "token": "encrypted_token"  # 加密存储
}
# 添加 Authorization: Bearer <token>
```

### 4. API Key

```python
webhook.auth_type = AuthType.API_KEY
webhook.auth_config = {
    "key_name": "X-API-Key",  # 自定义请求头名称
    "key_value": "encrypted_key_value"  # 加密存储
}
# 添加 X-API-Key: <key_value>
```

## HMAC签名

所有推送请求都会自动添加HMAC-SHA256签名：

```
X-IDP-Signature: sha256=<signature>
```

签名计算方式：
```python
signature = hmac.new(
    secret_key.encode(),
    request_body.encode(),
    hashlib.sha256
).hexdigest()
```

下游系统可以使用相同的方式验证签名，确保请求来自IDP平台且未被篡改。

## 请求头

每个推送请求都包含以下标准请求头：

```
Content-Type: application/json
User-Agent: Enterprise IDP Platform/1.0.0
X-IDP-Timestamp: 1705219200
X-IDP-Signature: sha256=abc123...
Authorization: <根据auth_type添加>
```

## 重试策略

### 重试条件

以下情况会触发重试：
- 5xx服务器错误
- 429 Too Many Requests
- 网络超时
- 连接错误

以下情况不会重试：
- 2xx成功响应
- 4xx客户端错误（除了429）
- 已达最大重试次数

### 延迟时间

```python
# 配置在 settings.PUSH_RETRY_DELAYS
[10, 30, 90]  # 秒

# 第1次重试：10秒后
# 第2次重试：30秒后
# 第3次重试：90秒后
```

## 错误处理

### 超时处理

```python
# 配置推送超时时间（默认30秒）
settings.PUSH_TIMEOUT = 30

# 超时后会记录错误并触发重试
```

### 异常处理

所有异常都会被捕获并记录：
- 保存错误日志到数据库
- 记录详细的错误信息
- 不影响其他Webhook的推送

## 性能优化

### 并行推送

使用 `asyncio.gather` 并行推送到多个Webhook：

```python
# 并行推送到3个Webhook，总耗时约等于最慢的那个
results = await push_service.batch_push(task, webhooks)
```

### 连接池

使用 `httpx.AsyncClient` 的连接池功能，复用TCP连接。

## 监控指标

推送服务会记录以下指标：
- 推送成功率
- 平均响应时间
- 重试次数分布
- 死信队列大小

可以通过查询 `push_logs` 表获取这些指标。

## 依赖注入

在FastAPI端点中使用：

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.push_service import get_push_service, PushService

@router.post("/tasks/{task_id}/push")
async def push_task(
    task_id: str,
    push_service: PushService = Depends(get_push_service),
    db: AsyncSession = Depends(get_db)
):
    # 使用push_service
    pass
```

## 注意事项

1. **敏感数据加密**：所有认证信息（密码、Token、API Key）都使用AES-256加密存储
2. **签名验证**：下游系统应验证X-IDP-Signature签名，确保请求合法性
3. **幂等性**：推送可能重试，下游系统应实现幂等性处理
4. **超时设置**：合理设置超时时间，避免长时间阻塞
5. **日志清理**：定期清理过期的推送日志，避免数据库膨胀

## 相关需求

- Requirement 18: Result Push and Retry Mechanism
- Requirement 19: Dead Letter Queue Management
- Requirement 31: Push Mechanism - Exponential Backoff Retry
- Requirement 61: Webhook Template - Variable Injection
