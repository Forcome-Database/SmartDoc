# Pipeline Worker 使用说明

## 概述

Pipeline Worker 是数据处理管道的执行器，负责在 OCR 处理完成后执行用户自定义的 Python 脚本，对提取的数据进行二次处理。

## 工作流程

```
OCR完成/审核通过 → Pipeline队列 → Pipeline Worker → 执行用户脚本 → Push队列 → Webhook推送
```

## 脚本编写规范

### 可用变量

在脚本中可以直接使用以下变量：

```python
# 任务ID
task_id: str

# 提取的数据（字典格式）
extracted_data: dict

# OCR识别的全文
ocr_text: str

# 任务元信息
meta_info: dict  # 包含 file_name, page_count, rule_id, rule_version, confidence_scores, created_at
```

### 输出数据

将处理后的数据赋值给 `output_data` 变量：

```python
# 示例：数据转换
output_data = {
    'invoice_no': extracted_data.get('invoice_number', '').upper(),
    'amount': float(extracted_data.get('total_amount', 0)),
    'processed_at': datetime.now().isoformat()
}
```

### 示例脚本

#### 1. 简单数据转换

```python
# 将金额字符串转换为数字
amount_str = extracted_data.get('amount', '0')
amount = float(amount_str.replace(',', '').replace('¥', ''))

# 格式化日期
from datetime import datetime
date_str = extracted_data.get('date', '')
if date_str:
    date_obj = datetime.strptime(date_str, '%Y年%m月%d日')
    formatted_date = date_obj.strftime('%Y-%m-%d')
else:
    formatted_date = None

output_data = {
    **extracted_data,
    'amount': amount,
    'date': formatted_date
}
```

#### 2. 调用外部API

```python
import requests
import os

# 从环境变量获取API密钥
api_key = os.environ.get('EXTERNAL_API_KEY')

# 调用外部服务验证数据
response = requests.post(
    'https://api.example.com/validate',
    json={'invoice_no': extracted_data.get('invoice_no')},
    headers={'Authorization': f'Bearer {api_key}'}
)

validation_result = response.json()

output_data = {
    **extracted_data,
    'validation_status': validation_result.get('status'),
    'validation_message': validation_result.get('message')
}
```

#### 3. 数据聚合计算

```python
# 计算表格数据的汇总
items = extracted_data.get('items', [])

total_quantity = sum(item.get('quantity', 0) for item in items)
total_amount = sum(item.get('amount', 0) for item in items)

output_data = {
    **extracted_data,
    'summary': {
        'total_items': len(items),
        'total_quantity': total_quantity,
        'total_amount': total_amount
    }
}
```

## 依赖包配置

在 `requirements` 字段中配置需要的第三方包，每行一个：

```
requests==2.31.0
pandas==2.0.0
openpyxl==3.1.0
```

## 环境变量

敏感信息（如API密钥）应通过环境变量配置，不要硬编码在脚本中：

```json
{
  "EXTERNAL_API_KEY": "your-api-key",
  "DATABASE_URL": "mysql://..."
}
```

## 执行限制

- 默认超时时间：300秒（可配置）
- 默认内存限制：512MB（可配置）
- 最大重试次数：1次（可配置）

## 启动命令

```bash
# 独立启动
python -m app.tasks.pipeline_worker

# 使用 Docker
docker-compose up pipeline-worker
```

## 注意事项

1. 脚本在隔离的虚拟环境中执行，不会影响主系统
2. 每个管道有独立的虚拟环境，依赖包更新后会自动重建
3. 执行失败会根据配置进行重试
4. 所有执行记录都会保存，可通过API查询
