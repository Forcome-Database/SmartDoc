# Pipeline 数据处理管道

## 功能概述

Pipeline 是一个轻量级的数据后处理功能，允许在 OCR 识别和数据提取完成后，通过自定义 Python 脚本对数据进行二次处理。

## 核心特性

- **独立运行环境**：每个管道在独立的 Python 虚拟环境中执行
- **支持第三方包**：可配置 requirements.txt
- **简单配置**：在规则中关联管道
- **安全隔离**：脚本在沙箱环境中执行
- **完整日志**：记录每次执行的输入、输出、日志和耗时

## 数据流程

```
OCR完成/审核通过
       ↓
Pipeline Worker 消费任务
       ↓
检查是否有管道 → 否 → 直接触发推送
       ↓ 是
创建虚拟环境，安装依赖
       ↓
执行用户脚本
       ↓
更新任务数据，触发Webhook
```

## 脚本编写

### 可用变量

```python
task_id: str           # 任务ID
extracted_data: dict   # 提取的数据
ocr_text: str          # OCR识别的全文
meta_info: dict        # 任务元信息
```

### 输出数据

```python
output_data = {
    'processed_field': 'value'
}
```

### 示例：数据格式化

```python
# 金额格式化
amount_str = extracted_data.get('amount', '0')
amount = float(amount_str.replace(',', '').replace('¥', ''))

# 日期格式化
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

### 示例：调用外部API

```python
import requests
import os

api_key = os.environ.get('EXTERNAL_API_KEY')

response = requests.post(
    'https://api.example.com/validate',
    json={'invoice_no': extracted_data.get('invoice_no')},
    headers={'Authorization': f'Bearer {api_key}'},
    timeout=10
)

result = response.json()

output_data = {
    **extracted_data,
    'validation_status': result.get('status')
}
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/pipelines | 创建管道 |
| GET | /api/v1/pipelines | 获取管道列表 |
| GET | /api/v1/pipelines/{id} | 获取管道详情 |
| PUT | /api/v1/pipelines/{id} | 更新管道 |
| DELETE | /api/v1/pipelines/{id} | 删除管道 |
| POST | /api/v1/pipelines/{id}/test | 测试管道 |

## 配置项

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| name | string | - | 管道名称 |
| rule_id | string | - | 关联的规则ID |
| script_content | string | - | Python脚本内容 |
| requirements | string | - | 依赖包列表 |
| timeout_seconds | int | 300 | 执行超时时间 |
| max_retries | int | 1 | 最大重试次数 |
| memory_limit_mb | int | 512 | 内存限制 |
