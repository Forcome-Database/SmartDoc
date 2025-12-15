# 系统配置 API

## 端点列表

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | /api/v1/system/config | Admin | 获取所有系统配置 |
| PUT | /api/v1/system/config/{key} | Admin | 更新系统配置 |
| GET | /api/v1/system/retention | Admin | 获取数据生命周期配置 |
| PUT | /api/v1/system/retention | Admin | 更新数据生命周期配置 |

## 获取所有配置

```bash
GET /api/v1/system/config
```

**响应：**
```json
{
  "configs": [
    {
      "key": "file_retention_days",
      "value": 30,
      "description": "文件留存期（天）",
      "updated_by": "U_ADMIN001",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 12
}
```

## 更新配置

```bash
PUT /api/v1/system/config/ocr_timeout
Content-Type: application/json

{
  "value": 600,
  "description": "OCR超时时间（秒）- 已更新"
}
```

配置更新后立即生效，自动更新 Redis 缓存并记录审计日志。

## 数据生命周期配置

```bash
GET /api/v1/system/retention
```

**响应：**
```json
{
  "file_retention_days": 30,
  "data_retention_days": 0,
  "next_cleanup_time": "2024-01-02 02:00:00"
}
```

## 更新生命周期配置

```bash
PUT /api/v1/system/retention
Content-Type: application/json

{
  "file_retention_days": 60,
  "data_retention_days": 365
}
```

**验证规则：**
- `file_retention_days`: 1-365天
- `data_retention_days`: 0-3650天（0表示永久保留）

## 常用配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| ocr_timeout | OCR超时时间（秒） | 300 |
| ocr_max_parallel | 最大并行任务数 | 4 |
| llm_timeout | LLM超时时间（秒） | 60 |
| llm_token_price | Token单价 | 0.002 |
| file_retention_days | 文件留存期（天） | 30 |
| data_retention_days | 数据留存期（天） | 0 |
