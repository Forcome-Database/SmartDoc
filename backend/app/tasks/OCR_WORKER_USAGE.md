# OCR Worker 使用指南

## 概述

OCR Worker是智能文档处理中台的核心组件，负责从RabbitMQ消费OCR任务，执行完整的文档处理流程。

## 快速开始

### 独立运行Worker

```bash
cd backend
python -m app.tasks.ocr_worker
```

### 在应用中集成

```python
from app.tasks.ocr_worker import ocr_worker
import asyncio

async def main():
    # 启动Worker
    await ocr_worker.start()

if __name__ == "__main__":
    asyncio.run(main())
```

## 处理流程

```
1. 接收任务消息 (从RabbitMQ)
   ↓
2. 更新状态: QUEUED → PROCESSING
   ↓
3. 下载文件 (MinIO → 本地临时目录)
   ↓
4. 加载规则配置 (从数据库)
   ↓
5. 执行OCR识别
   - 支持PaddleOCR、Tesseract、Azure
   - 自动降级备用引擎
   ↓
6. 执行数据提取
   - 正则提取
   - 锚点定位提取
   - 表格提取
   ↓
7. [可选] LLM增强
   - 熔断器保护
   - Token计费
   ↓
8. 数据清洗
   - 正则替换
   - 去空格
   - 日期格式化
   ↓
9. 数据校验
   - 类型转换
   - 必填校验
   - 格式校验
   - 范围校验
   ↓
10. 保存结果到数据库
    ↓
11. 判断是否需要审核
    ├─ 需要 → PENDING_AUDIT
    └─ 不需要 → COMPLETED → 触发推送任务
```

## 审核判断逻辑

任务会在以下情况下进入人工审核：

### 1. 校验失败
```python
# 示例：必填字段为空
validation_result = {
    'is_valid': False,
    'errors': [
        {
            'field': 'invoice_number',
            'message': '必填字段为空',
            'value': None
        }
    ]
}
# 结果：需要审核
```

### 2. 置信度低于阈值
```python
# 示例：OCR识别置信度低
confidence_scores = {
    'amount': 75.0,  # 低于阈值80
    'date': 90.0
}
audit_config = {
    'confidence_threshold': 80.0
}
# 结果：需要审核
```

### 3. 全部通过
```python
# 示例：校验通过且置信度高
validation_result = {'is_valid': True, 'errors': []}
confidence_scores = {
    'amount': 95.0,
    'date': 90.0
}
# 结果：不需要审核，直接完成
```

## 配置说明

### 环境变量

```bash
# OCR配置
OCR_MAX_PARALLEL=4  # OCR最大并行数

# Azure OCR（可选）
AZURE_FORM_RECOGNIZER_ENDPOINT=https://xxx.cognitiveservices.azure.com/
AZURE_FORM_RECOGNIZER_KEY=your_key

# RabbitMQ配置
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
RABBITMQ_QUEUE_OCR=ocr_tasks
RABBITMQ_QUEUE_PUSH=push_tasks

# MinIO配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=idp-files
```

### 规则配置示例

```json
{
  "schema": {
    "invoice_number": {"type": "String", "required": true},
    "amount": {"type": "Decimal", "decimal_places": 2},
    "date": {"type": "Date"}
  },
  "ocr_config": {
    "engine": "paddleocr",
    "page_strategy": {"mode": "multi_page"},
    "language": "ch",
    "enable_fallback": true,
    "fallback_engine": "tesseract"
  },
  "extraction_rules": [
    {
      "field": "invoice_number",
      "type": "regex",
      "pattern": "发票号码[：:](\\w+)"
    },
    {
      "field": "amount",
      "type": "anchor",
      "anchor_text": "金额",
      "direction": "right"
    }
  ],
  "llm_config": {
    "enabled": true,
    "fields": [
      {
        "field": "invoice_number",
        "context_scope": "first_n_pages",
        "n_pages": 1
      }
    ]
  },
  "cleaning_rules": [
    {
      "field": "amount",
      "operations": [
        {"type": "regex_replace", "pattern": ",", "replacement": ""},
        {"type": "trim"}
      ]
    }
  ],
  "validation_rules": [
    {
      "field": "invoice_number",
      "required": true
    },
    {
      "field": "amount",
      "range": {"min": 0, "max": 1000000}
    }
  ],
  "audit_config": {
    "confidence_threshold": 80.0
  }
}
```

## 错误处理

### 异常捕获

Worker会捕获所有异常并进行处理：

```python
try:
    # 处理任务
    await self.process_task(task_data)
except Exception as e:
    # 记录错误日志
    logger.error(f"任务处理失败: {str(e)}", exc_info=True)
    
    # 更新任务状态为FAILED
    await self._update_task_status(
        db, task_id, TaskStatus.FAILED, 
        error_message=str(e)
    )
    
    # Nack消息（不重新入队）
    # 避免死循环
```

### 常见错误

1. **文件下载失败**
   - 原因：MinIO连接失败或文件不存在
   - 处理：任务标记为FAILED

2. **OCR处理失败**
   - 原因：文件格式不支持或引擎异常
   - 处理：尝试备用引擎，失败则标记FAILED

3. **LLM服务异常**
   - 原因：API超时或熔断器打开
   - 处理：降级为纯OCR模式，继续处理

4. **数据库异常**
   - 原因：连接失败或事务冲突
   - 处理：回滚事务，任务标记为FAILED

## 监控指标

### 日志示例

```
2025-12-04 18:16:05 - INFO - 开始处理任务: T_20251204_0001
2025-12-04 18:16:06 - INFO - 文件下载成功: 2025/12/04/T_20251204_0001/invoice.pdf
2025-12-04 18:16:07 - INFO - 规则配置加载成功: RULE_001 (版本: 1.0.0)
2025-12-04 18:16:10 - INFO - OCR处理完成: 页数=3, 引擎=paddleocr, 文本长度=1234
2025-12-04 18:16:11 - INFO - 数据提取完成: 5 个字段
2025-12-04 18:16:13 - INFO - LLM增强完成: 总Token=150, 总费用=¥0.0003
2025-12-04 18:16:13 - INFO - 数据清洗完成
2025-12-04 18:16:13 - INFO - 数据校验完成: 有效=True, 错误数=0, 警告数=0
2025-12-04 18:16:13 - INFO - 任务结果已保存: T_20251204_0001
2025-12-04 18:16:13 - INFO - 任务处理完成: T_20251204_0001
2025-12-04 18:16:13 - INFO - 推送任务已触发: T_20251204_0001
```

### 性能指标

- **OCR处理时间**: 通常 < 3秒/页
- **数据提取时间**: 通常 < 1秒
- **LLM增强时间**: 通常 < 5秒/字段
- **总处理时间**: 单页文档通常 < 10秒

## 测试

### 运行测试

```bash
cd backend
python test_ocr_worker.py
```

### 测试覆盖

- ✅ Worker初始化
- ✅ 服务初始化（OCR、提取）
- ✅ 审核判断逻辑（3个场景）

## 故障排查

### Worker无法启动

**问题**: Worker启动失败

**检查**:
1. RabbitMQ是否运行: `docker-compose ps rabbitmq`
2. 数据库是否可访问
3. 环境变量是否配置正确

### 任务处理缓慢

**问题**: 任务处理时间过长

**检查**:
1. OCR引擎是否正常（查看日志）
2. LLM服务是否超时
3. 文件大小和页数
4. 并行处理数配置

### 任务一直失败

**问题**: 任务反复失败

**检查**:
1. 查看任务错误信息: `SELECT error_message FROM tasks WHERE id='xxx'`
2. 查看Worker日志
3. 检查规则配置是否正确
4. 检查文件是否损坏

## 最佳实践

### 1. 资源管理

```python
# ✅ 好的做法：使用临时文件并清理
try:
    local_file = await self._download_file(task)
    # 处理文件
finally:
    if os.path.exists(local_file):
        os.remove(local_file)

# ❌ 不好的做法：不清理临时文件
local_file = await self._download_file(task)
# 处理文件
# 文件未清理，占用磁盘空间
```

### 2. 错误处理

```python
# ✅ 好的做法：捕获具体异常
try:
    result = await self._execute_ocr(task, file_path, config)
except FileNotFoundError:
    logger.error("文件不存在")
except OCREngineError:
    logger.error("OCR引擎异常")
except Exception as e:
    logger.error(f"未知错误: {str(e)}")

# ❌ 不好的做法：忽略异常
try:
    result = await self._execute_ocr(task, file_path, config)
except:
    pass  # 静默失败
```

### 3. 日志记录

```python
# ✅ 好的做法：记录关键信息
logger.info(
    f"OCR处理完成: 页数={page_count}, "
    f"引擎={engine}, 耗时={duration}s"
)

# ❌ 不好的做法：日志信息不足
logger.info("OCR完成")
```

## 相关文档

- [OCR服务文档](../services/ocr_service.py)
- [提取服务文档](../services/extraction_service.py)
- [LLM服务文档](../services/llm_service.py)
- [校验服务文档](../services/validation_service.py)
- [任务模型文档](../models/task.py)

## 支持

如有问题，请查看：
1. Worker日志文件
2. RabbitMQ管理界面: http://localhost:15672
3. 数据库任务表: `SELECT * FROM tasks WHERE status='failed'`
