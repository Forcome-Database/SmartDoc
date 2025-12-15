# 数据清洗与校验服务使用指南

## 概述

`ValidationService` 提供完整的数据清洗、类型转换和校验功能，支持：

- 数据清洗（正则替换、去空格、日期格式化）
- 类型转换（String、Int、Date、Decimal、Boolean）
- 数据校验（必填、格式、范围）
- 自定义JavaScript表达式校验

## 快速开始

```python
from app.services.validation_service import ValidationService

service = ValidationService()
```

## 功能详解

### 1. 数据清洗

#### 1.1 正则替换

```python
# 移除逗号分隔符
result = service.regex_replace("1,234.56", ",", "")
# 结果: "1234.56"
```

#### 1.2 去空格

```python
result = service.trim("  张三  ")
# 结果: "张三"
```

#### 1.3 日期格式化

```python
# 支持多种日期格式自动识别
result = service.format_date("2025年12月14日", "%Y-%m-%d")
# 结果: "2025-12-14"

result = service.format_date("14/12/2025", "%Y-%m-%d")
# 结果: "2025-12-14"
```

#### 1.4 清洗管道

```python
data = {
    "amount": "1,234.56",
    "name": "  张三  ",
    "date": "2025年12月14日"
}

cleaning_rules = [
    {
        "field": "amount",
        "operations": [
            {"type": "regex_replace", "pattern": ",", "replacement": ""},
            {"type": "trim"}
        ]
    },
    {
        "field": "name",
        "operations": [{"type": "trim"}]
    },
    {
        "field": "date",
        "operations": [{"type": "format_date", "target_format": "%Y-%m-%d"}]
    }
]

cleaned = service.clean_data(data, cleaning_rules)
# 结果: {'amount': '1234.56', 'name': '张三', 'date': '2025-12-14'}
```

### 2. 类型转换

#### 2.1 基本类型转换

```python
# String
value, error = service.convert_type(123, "String")
# 结果: ("123", None)

# Int
value, error = service.convert_type("1,234", "Int")
# 结果: (1234, None)

# Decimal（支持小数位数配置）
value, error = service.convert_type("1234.567", "Decimal", decimal_places=2)
# 结果: (1234.57, None)

# Boolean
value, error = service.convert_type("是", "Boolean")
# 结果: (True, None)

value, error = service.convert_type("否", "Boolean")
# 结果: (False, None)

# Date
value, error = service.convert_type("2025年12月14日", "Date")
# 结果: ("2025-12-14", None)
```

#### 2.2 批量类型转换

```python
data = {
    "amount": "1,234.56",
    "count": "5",
    "is_active": "是",
    "date": "2025年12月14日"
}

schema = {
    "amount": {"type": "Decimal", "decimal_places": 2},
    "count": {"type": "Int"},
    "is_active": {"type": "Boolean"},
    "date": {"type": "Date"}
}

converted_data, warnings = service.convert_schema_types(data, schema)
# 结果: {
#     'amount': 1234.56,
#     'count': 5,
#     'is_active': True,
#     'date': '2025-12-14'
# }
```

### 3. 数据校验

#### 3.1 必填校验

```python
validation_rules = [
    {
        "field": "name",
        "required": True
    }
]

data = {"name": ""}
result = service.validate(data, validation_rules)
# result.has_errors == True
# result.errors[0].message == "必填字段为空: name"
```

#### 3.2 格式校验

```python
validation_rules = [
    {
        "field": "email",
        "pattern": "email"  # 预定义模式
    },
    {
        "field": "phone",
        "pattern": "phone"  # 中国手机号
    },
    {
        "field": "custom_field",
        "custom_pattern": "^[A-Z]{3}\\d{3}$"  # 自定义正则
    }
]

data = {
    "email": "test@example.com",
    "phone": "13800138000",
    "custom_field": "ABC123"
}

result = service.validate(data, validation_rules)
# result.is_valid == True
```

支持的预定义模式：
- `email`: 邮箱格式
- `phone`: 中国手机号
- `url`: URL格式
- `id_card`: 中国身份证号

#### 3.3 范围校验

```python
validation_rules = [
    {
        "field": "age",
        "range": {"min": 0, "max": 150}
    },
    {
        "field": "price",
        "range": {"min": 0}  # 只限制最小值
    }
]

data = {"age": 25, "price": 99.99}
result = service.validate(data, validation_rules)
# result.is_valid == True
```

### 4. 自定义脚本校验

使用JavaScript表达式进行复杂业务逻辑校验：

```python
data = {
    "amount": 100,
    "count": 5,
    "total": 500
}

script_rules = [
    {
        "name": "金额校验",
        "expression": "fields.amount * fields.count == fields.total",
        "error_message": "金额计算不正确"
    },
    {
        "name": "折扣校验",
        "expression": "fields.discount >= 0 && fields.discount <= 100",
        "error_message": "折扣必须在0-100之间"
    }
]

result = service.validate_custom_scripts(data, script_rules)
# result.is_valid == True
```

### 5. 综合处理流程

一次性完成清洗、转换、校验：

```python
# 原始数据
data = {
    "amount": "1,234.56",
    "count": "5",
    "total": "6,172.80",
    "email": "test@example.com",
    "date": "2025年12月14日"
}

# Schema定义
schema = {
    "amount": {"type": "Decimal", "decimal_places": 2},
    "count": {"type": "Int"},
    "total": {"type": "Decimal", "decimal_places": 2},
    "email": {"type": "String"},
    "date": {"type": "Date"}
}

# 清洗规则
cleaning_rules = [
    {
        "field": "amount",
        "operations": [
            {"type": "regex_replace", "pattern": ",", "replacement": ""}
        ]
    },
    {
        "field": "total",
        "operations": [
            {"type": "regex_replace", "pattern": ",", "replacement": ""}
        ]
    }
]

# 校验规则
validation_rules = [
    {
        "field": "email",
        "required": True,
        "pattern": "email"
    }
]

# 自定义脚本规则
script_rules = [
    {
        "name": "金额校验",
        "expression": "fields.amount * fields.count == fields.total",
        "error_message": "金额计算不正确"
    }
]

# 综合处理
processed_data, result = service.process_data(
    data,
    schema,
    cleaning_rules,
    validation_rules,
    script_rules
)

# 处理后的数据
print(processed_data)
# {
#     'amount': 1234.56,
#     'count': 5,
#     'total': 6172.80,
#     'email': 'test@example.com',
#     'date': '2025-12-14'
# }

# 校验结果
print(result.to_dict())
# {
#     'is_valid': True,
#     'errors': [],
#     'warnings': []
# }
```

## 在OCR Worker中使用

```python
from app.services.validation_service import ValidationService

class OCRWorker:
    def __init__(self):
        self.validation_service = ValidationService()
    
    async def process_task(self, task_data):
        # ... OCR和提取逻辑 ...
        
        # 获取规则配置
        rule_config = self._load_rule_config(task_data['rule_id'])
        
        # 综合处理数据
        processed_data, validation_result = self.validation_service.process_data(
            extracted_data,
            rule_config['schema'],
            rule_config.get('cleaning_rules'),
            rule_config.get('validation_rules'),
            rule_config.get('script_rules')
        )
        
        # 判断是否需要人工审核
        if validation_result.has_errors:
            # 转为待审核状态
            self._update_task_status(
                task_id,
                TaskStatus.PENDING_AUDIT,
                audit_reasons=[e.to_dict() for e in validation_result.errors]
            )
        else:
            # 直通完成
            self._update_task_status(task_id, TaskStatus.COMPLETED)
            self._publish_push_task(task_id)
        
        # 保存处理结果
        self._save_task_result(task_id, processed_data, validation_result)
```

## 错误处理

所有方法都会优雅地处理错误：

```python
# 类型转换失败
value, error = service.convert_type("abc", "Int")
# value: "abc" (保留原值)
# error: "类型转换失败: invalid literal for int() with base 10: 'abc'"

# 日期格式无法识别
result = service.format_date("invalid-date")
# 返回原值并记录警告日志

# JavaScript表达式执行失败
result = service.execute_js_expression("invalid syntax", {})
# 返回 (False, "JavaScript表达式执行失败: ...")
```

## 性能考虑

- JavaScript表达式执行有100毫秒超时限制
- 建议在规则配置中合理使用清洗和校验规则
- 对于大批量数据，考虑使用异步处理

## 相关需求

- Requirements: 11, 34, 44, 45, 58
