# 仪表盘 API

## 端点列表

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/v1/dashboard/metrics | 获取核心指标 |
| GET | /api/v1/dashboard/throughput | 获取任务吞吐趋势 |
| GET | /api/v1/dashboard/rule-performance | 获取规则效能Top10 |
| GET | /api/v1/dashboard/exceptions | 获取异常分布 |

## 核心指标

```bash
GET /api/v1/dashboard/metrics?time_range=7days
Authorization: Bearer <token>
```

**参数：** `time_range` - today / 7days / 30days

**响应：**
```json
{
  "total_tasks": 150,
  "total_pages": 450,
  "processing_count": 5,
  "pending_audit_count": 12,
  "push_failed_count": 3,
  "straight_through_rate": 85.5,
  "cost_savings": {
    "instant_count": 20,
    "instant_pages": 60,
    "saved_hours": 0.05
  },
  "llm_consumption": {
    "total_tokens": 15000,
    "total_cost": 30.0
  }
}
```

## 任务吞吐趋势

```bash
GET /api/v1/dashboard/throughput?time_range=7days
```

**响应：**
```json
{
  "throughput": [
    {
      "date": "2025-12-07",
      "success": 20,
      "pending_audit": 3,
      "failed": 1,
      "rejected": 0,
      "total": 24
    }
  ]
}
```

## 规则效能 Top10

```bash
GET /api/v1/dashboard/rule-performance?time_range=7days
```

**响应：**
```json
{
  "rules": [
    {
      "rule_id": "RULE_001",
      "rule_name": "发票识别规则",
      "task_count": 150,
      "avg_duration": 12.5,
      "intervention_rate": 8.5,
      "intervention_level": "low"
    }
  ]
}
```

**干预率等级：**
- `low`: < 10%（绿色）
- `medium`: 10-30%（黄色）
- `high`: > 30%（红色）

## 异常分布

```bash
GET /api/v1/dashboard/exceptions?time_range=7days
```

**响应：**
```json
{
  "total_exceptions": 45,
  "exceptions": [
    {
      "type": "required_field_missing",
      "label": "必填校验失败",
      "count": 18,
      "percentage": 40.0
    }
  ]
}
```

**异常类型：**
- `ocr_empty`: OCR识别空
- `required_field_missing`: 必填校验失败
- `format_validation_failed`: 格式校验失败
- `llm_inconsistent`: LLM不一致
- `downstream_error`: 下游接口错误
- `processing_timeout`: 处理超时

## 缓存策略

核心指标端点使用 Redis 缓存5分钟，减少数据库查询压力。
