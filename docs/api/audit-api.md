# 审核工作台 API

## 端点列表

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | /api/v1/audit/tasks | Admin, Auditor | 获取待审核任务列表 |
| GET | /api/v1/audit/tasks/{task_id} | Admin, Auditor | 获取审核任务详情 |
| GET | /api/v1/audit/tasks/{task_id}/preview/{page} | Admin, Auditor | 获取PDF页面预览图 |
| POST | /api/v1/audit/tasks/{task_id}/draft | Admin, Auditor | 保存审核草稿 |
| GET | /api/v1/audit/tasks/{task_id}/draft | Admin, Auditor | 获取审核草稿 |
| POST | /api/v1/audit/tasks/{task_id}/submit | Admin, Auditor | 提交审核结果 |

## 获取待审核任务列表

```bash
GET /api/v1/audit/tasks?page=1&page_size=20
```

**查询参数：**
- `page`: 页码
- `page_size`: 每页数量
- `rule_id`: 规则ID筛选
- `start_date`: 开始日期
- `end_date`: 结束日期

## 获取任务详情

```bash
GET /api/v1/audit/tasks/T_20250105_0001
```

**响应包含：**
- 任务基本信息
- PDF文件预签名URL（1小时有效）
- OCR结果（含坐标信息）
- 提取结果和置信度
- 审核原因

## 获取PDF预览图

```bash
GET /api/v1/audit/tasks/T_20250105_0001/preview/1
```

返回 PNG 格式图片，使用 Redis 缓存1小时。

## 保存草稿

```bash
POST /api/v1/audit/tasks/T_20250105_0001/draft
Content-Type: application/json

{
  "extracted_data": {
    "invoice_no": "NO.123456",
    "amount": 100.50
  }
}
```

草稿存储在 Redis，TTL 24小时。

## 提交审核

```bash
POST /api/v1/audit/tasks/T_20250105_0001/submit
Content-Type: application/json

{
  "decision": "approved",
  "extracted_data": {
    "invoice_no": "NO.123456",
    "amount": 100.50
  },
  "comment": "数据已确认无误"
}
```

**decision 可选值：**
- `approved`: 审核通过 → 状态变为 `completed`
- `rejected`: 审核驳回 → 状态变为 `rejected`

## 典型审核流程

1. 获取待审核任务列表
2. 查看任务详情
3. 加载PDF预览
4. 保存草稿（可选）
5. 提交审核
