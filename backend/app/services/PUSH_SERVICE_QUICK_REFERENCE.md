# Webhook推送服务快速参考

## 快速开始

```python
from app.services.push_service import PushService
from app.core.database import get_db

# 创建推送服务
async with get_db() as db:
    push_service = PushService(db)
    
    # 推送到单个Webhook
    result = await push_service.push_to_webhook(task, webhook)
    
    # 推送并自动重试
    result = await push_service.push_with_retry(task, webhook)
    
    # 批量推送到多个Webhook
    results = await push_service.batch_push(task, webhooks)
```

## 核心API

### 推送函数

```python
# 基本推送
result = await push_service.push_to_webhook(task, webhook, retry_count=0)

# 带重试的推送
result = await push_service.push_with_retry(task, webhook, max_retries=3)

# 批量推送
results = await push_service.batch_push(task, webhooks)
```

### 日志管理

```python
# 保存推送日志（通常自动调用）
log = await push_service.save_push_log(
    task_id="T_20251214_0001",
    webhook_id="WH_001",
    http_status=200,
    request_headers={},
    request_body="{}",
    response_headers={},
    response_body="{}",
    duration_ms=150,
    retry_count=0
)

# 查询推送日志
logs = await push_service.get_push_logs(task_id="T_20251214_0001")
```

### 死信队列

```python
# 移入死信队列
await push_service.move_to_dlq(
    task_id="T_20251214_0001",
    webhook_id="WH_001",
    failure_reason="连接超时",
    retry_count=3
)

# 获取死信队列任务
dlq_tasks = await push_service.get_dlq_tasks(limit=100)

# 手动重推
result = await push_service.retry_dlq_task(
    task_id="T_20251214_0001",
    webhook_id="WH_001"  # 可选
)
```

## 模版变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `{{task_id}}` | string | 任务ID |
| `{{result_json}}` | object | 提取结果JSON |
| `{{file_url}}` | string | 文件预签名URL |
| `{{meta_info}}` | object | 任务元信息 |

## 认证配置

### Basic Auth
```python
webhook.auth_type = AuthType.BASIC
webhook.auth_config = {
    "username": "user",
    "password": encrypt_sensitive_data("pass")
}
```

### Bearer Token
```python
webhook.auth_type = AuthType.BEARER
webhook.auth_config = {
    "token": encrypt_sensitive_data("token123")
}
```

### API Key
```python
webhook.auth_type = AuthType.API_KEY
webhook.auth_config = {
    "key_name": "X-API-Key",
    "key_value": encrypt_sensitive_data("key123")
}
```

## 重试策略

- **延迟时间**: 10s → 30s → 90s
- **最大次数**: 3次
- **重试条件**: 5xx错误、429限流、超时、网络错误
- **不重试**: 2xx成功、4xx错误（除429）

## 请求头

```
Content-Type: application/json
User-Agent: Enterprise IDP Platform/1.0.0
X-IDP-Timestamp: 1705219200
X-IDP-Signature: sha256=abc123...
Authorization: <根据auth_type>
```

## 返回结果

```python
class PushResult:
    success: bool           # 是否成功
    http_status: int        # HTTP状态码
    response_body: str      # 响应体
    error_message: str      # 错误信息
    duration_ms: int        # 耗时（毫秒）
```

## 常见场景

### 场景1: Worker中推送
```python
# OCR处理完成后
if task.status == TaskStatus.COMPLETED:
    webhooks = task.rule.webhooks
    results = await push_service.batch_push(task, webhooks)
    
    if all(r.success for r in results):
        task.status = TaskStatus.PUSH_SUCCESS
    else:
        # 处理失败的推送
        for i, result in enumerate(results):
            if not result.success:
                await push_service.move_to_dlq(
                    task.id,
                    webhooks[i].id,
                    result.error_message,
                    retry_count=3
                )
```

### 场景2: API端点重推
```python
@router.post("/tasks/{task_id}/retry-push")
async def retry_push(
    task_id: str,
    push_service: PushService = Depends(get_push_service)
):
    result = await push_service.retry_dlq_task(task_id)
    return result
```

### 场景3: 查询推送状态
```python
@router.get("/tasks/{task_id}/push-logs")
async def get_push_logs(
    task_id: str,
    push_service: PushService = Depends(get_push_service)
):
    logs = await push_service.get_push_logs(task_id)
    return {"logs": logs}
```

## 配置项

```python
# settings.py
PUSH_TIMEOUT = 30                    # 推送超时（秒）
PUSH_RETRY_MAX = 3                   # 最大重试次数
PUSH_RETRY_DELAYS = [10, 30, 90]    # 重试延迟（秒）
```

## 监控指标

```sql
-- 推送成功率
SELECT 
    COUNT(CASE WHEN http_status BETWEEN 200 AND 299 THEN 1 END) * 100.0 / COUNT(*) as success_rate
FROM push_logs
WHERE created_at >= NOW() - INTERVAL 1 DAY;

-- 平均响应时间
SELECT AVG(duration_ms) as avg_duration_ms
FROM push_logs
WHERE created_at >= NOW() - INTERVAL 1 DAY;

-- 重试次数分布
SELECT retry_count, COUNT(*) as count
FROM push_logs
GROUP BY retry_count
ORDER BY retry_count;

-- 死信队列大小
SELECT COUNT(*) as dlq_size
FROM tasks
WHERE status = 'push_failed';
```

## 故障排查

### 问题1: 推送超时
- 检查网络连接
- 增加超时时间
- 检查下游系统负载

### 问题2: 签名验证失败
- 确认secret_key正确
- 检查请求体是否被修改
- 验证签名算法一致

### 问题3: 认证失败
- 检查auth_config配置
- 确认凭证未过期
- 验证加密/解密正确

### 问题4: 重试无效
- 检查should_retry逻辑
- 确认HTTP状态码
- 查看错误日志

## 最佳实践

1. **幂等性**: 下游系统应实现幂等性处理
2. **签名验证**: 下游系统应验证X-IDP-Signature
3. **超时设置**: 合理设置超时时间（建议30秒）
4. **日志清理**: 定期清理过期推送日志
5. **监控告警**: 监控推送成功率和死信队列大小
6. **错误处理**: 优雅处理推送失败，避免影响主流程
7. **批量推送**: 使用batch_push提高性能
8. **重试策略**: 根据业务需求调整重试次数和延迟

## 相关文档

- `PUSH_SERVICE_USAGE.md` - 详细使用说明
- `TASK_12_SUMMARY.md` - 任务完成总结
- `test_push_service.py` - 单元测试示例
