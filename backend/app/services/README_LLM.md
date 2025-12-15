# LLM集成服务使用说明

## 概述

LLM集成服务（`llm_service.py`）提供了完整的大语言模型集成功能，包括：

1. **LLM客户端初始化** - 支持多种LLM提供商（OpenAI、ZhipuAI、Claude等）
2. **智能提取** - 使用LLM从文档中提取结构化数据
3. **熔断器机制** - 自动降级保护，确保系统稳定性
4. **一致性校验** - 对比OCR和LLM结果，提高准确性
5. **Token消耗跟踪** - 精确统计和计算LLM使用成本

## 安装依赖

```bash
# 安装Agently库（需要Python >= 3.10）
pip install agently>=4.0.6

# 或安装所有依赖
pip install -r requirements.txt
```

**重要提示**：
- 包名是小写的`agently`
- 导入时使用：`from agently import Agently`
- 创建实例：`Agently.create_agent()`
- 官方文档：https://agently.tech/
- GitHub：https://github.com/AgentEra/Agently

## 配置

在`.env`文件中配置以下环境变量（使用OpenAI兼容协议）：

```bash
# LLM API配置（OpenAI兼容协议）
LLM_BASE_URL=https://api.openai.com/v1  # API Base URL
LLM_API_KEY=your_api_key_here  # API Key
LLM_MODEL=gpt-3.5-turbo  # 模型名称
LLM_TIMEOUT=60  # LLM请求超时时间（秒）
LLM_TOKEN_PRICE=0.002  # Token单价（元/token）
LLM_MAX_TOKENS=4000  # 最大Token数
LLM_PROXY=  # 可选：代理地址，如 http://127.0.0.1:7890
```

### 支持的服务商示例

#### OpenAI官方
```bash
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-3.5-turbo
```

#### Azure OpenAI
```bash
LLM_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment
LLM_API_KEY=your_azure_key
LLM_MODEL=gpt-35-turbo
```

#### 本地模型（如Xinference、Ollama等）
```bash
LLM_BASE_URL=http://127.0.0.1:9997/v1
LLM_API_KEY=nothing
LLM_MODEL=your-model-name
```

#### 其他OpenAI兼容服务
```bash
LLM_BASE_URL=https://your-service-provider/v1
LLM_API_KEY=your_api_key
LLM_MODEL=model-name
```

## 核心功能

### 1. LLM提取

使用LLM从文档中提取字段值：

```python
from app.services.llm_service import llm_service

# OCR结果
ocr_result = {
    "merged_text": "发票号：NO.123456\n金额：100.50元",
    "page_results": [...]
}

# 提取规则
extraction_rule = {
    "context_scope": "all_pages",  # 使用全文
    "prompt": "请提取发票号",
    "output_schema": {
        "value": ("String", "发票号"),
        "confidence": ("Float", "置信度")
    }
}

# 执行提取
result = await llm_service.extract_by_llm(
    ocr_result=ocr_result,
    field_name="invoice_no",
    extraction_rule=extraction_rule
)

print(result)
# {
#     "value": "NO.123456",
#     "confidence": 95.0,
#     "explanation": "从文本中找到明确的发票号",
#     "token_count": 150,
#     "duration": 1.2
# }
```

### 2. 上下文范围控制

支持三种上下文范围：

```python
# 全文模式
rule_all = {"context_scope": "all_pages"}

# 前N页模式
rule_first_n = {
    "context_scope": "first_n_pages",
    "n_pages": 3,
    "separator": "\n"
}

# 指定区域模式
rule_region = {
    "context_scope": "region",
    "region": {
        "page": 1,
        "x": 100,
        "y": 200,
        "width": 500,
        "height": 300
    }
}
```

### 3. 熔断器保护

自动监控LLM服务健康状态，异常时自动降级：

```python
# 熔断器会自动工作
# 连续5次失败后触发熔断
# 熔断期间返回None，降级为纯OCR模式
# 5分钟后自动尝试恢复

result = await llm_service.extract_by_llm(...)
if result is None:
    # LLM服务不可用，使用OCR结果
    print("LLM服务降级，使用OCR结果")
```

### 4. 一致性校验

对比OCR和LLM提取结果：

```python
# 单字段对比
comparison = llm_service.compare_results(
    ocr_result="NO.123456",
    llm_result="NO.123456",
    threshold=0.8
)

print(comparison)
# {
#     "is_consistent": True,
#     "similarity": 1.0,
#     "ocr_value": "NO.123456",
#     "llm_value": "NO.123456",
#     "difference": "相似度100.00%，高于阈值80.00%"
# }

# 批量对比
ocr_results = {
    "invoice_no": "NO.123456",
    "amount": "100.50"
}

llm_results = {
    "invoice_no": "NO.123456",
    "amount": "100.5"
}

batch_comparison = llm_service.batch_compare_results(
    ocr_results, llm_results, threshold=0.8
)
```

### 5. Token消耗跟踪

精确统计和计算LLM使用成本：

```python
# 计算Token数量
text = "这是一段测试文本"
token_count = llm_service.count_tokens(text)

# 计算费用
cost = llm_service.calculate_cost(token_count)
print(f"Token数: {token_count}, 费用: ¥{cost}")

# 跟踪使用记录
usage_record = llm_service.track_token_usage(
    task_id="T_20251214_0001",
    field_name="invoice_no",
    input_tokens=100,
    output_tokens=50,
    metadata={"model": "gpt-3.5-turbo"}
)

# 聚合统计
usage_records = [...]  # 多条使用记录
aggregation = llm_service.aggregate_token_usage(usage_records)
print(f"总Token: {aggregation['total_tokens']}")
print(f"总费用: ¥{aggregation['total_cost']}")
```

## OpenAI兼容协议

本服务使用Agently v4框架，通过OpenAI兼容协议支持多种LLM提供商。

### ⚠️ Agently v4 重要变更

Agently v4使用 **`OAIClient`** 而不是 `OpenAI` 作为OpenAI兼容客户端的名称。

### 工作原理

Agently通过配置`model.OAIClient.url`和`model.OAIClient.auth`来支持任何OpenAI兼容的API：

```python
from agently import Agently

# 使用Agently.create_agent()创建实例并链式配置
agent = (
    Agently.create_agent()
        .set_settings("current_model", "OAIClient")  # ⚠️ 注意：使用OAIClient
        .set_settings("model.OAIClient.auth", {"api_key": "your_key"})
        .set_settings("model.OAIClient.url", "https://your-api-url/v1")
        .set_settings("model.OAIClient.options", {"model": "model-name"})
)

# 使用Agent
result = (
    agent
        .input("你的问题")
        .output("String")
        .start()
)
```

### 配置路径对照表

| 配置项 | Agently v4路径 |
|--------|---------------|
| 当前模型 | `current_model` = `"OAIClient"` |
| API Key | `model.OAIClient.auth` = `{"api_key": "..."}` |
| Base URL | `model.OAIClient.url` = `"https://..."` |
| 模型名称 | `model.OAIClient.options` = `{"model": "..."}` |

### 兼容的服务商

只要服务商提供OpenAI兼容的API接口，都可以使用：

- ✅ OpenAI官方API
- ✅ Azure OpenAI Service
- ✅ 本地模型服务（Xinference、Ollama、LocalAI等）
- ✅ 第三方转发服务
- ✅ 私有部署的模型服务
- ✅ 其他兼容OpenAI协议的服务

## 错误处理

服务内置了完善的错误处理机制：

1. **超时处理** - LLM请求超过配置时间自动超时
2. **熔断降级** - 连续失败自动触发熔断，降级为纯OCR模式
3. **异常捕获** - 所有异常都会被捕获并记录日志
4. **优雅降级** - LLM不可用时返回None，不影响主流程

## 测试

运行测试套件：

```bash
cd backend
python test_llm_service.py
```

测试包括：
- 熔断器功能测试
- Token计数测试
- 费用计算测试
- 一致性校验测试
- 批量对比测试
- Token跟踪测试
- 上下文提取测试
- Prompt构建测试

## 性能优化建议

1. **合理设置超时时间** - 根据实际情况调整`LLM_TIMEOUT`
2. **控制上下文长度** - 使用`first_n_pages`或`region`减少Token消耗
3. **启用缓存** - 对相同内容的提取结果进行缓存
4. **批量处理** - 尽可能批量调用LLM API
5. **监控Token消耗** - 定期查看Token使用统计，优化Prompt

## 注意事项

1. Agently库需要Python >= 3.10
2. 首次使用需要配置有效的API Key
3. LLM调用会产生费用，请合理控制使用
4. 熔断器触发后会自动恢复，无需手动干预
5. 建议在生产环境启用一致性校验，提高准确性

## 常见问题

### Q: 如何处理LLM服务不可用的情况？

A: 服务内置了熔断器机制，会自动降级为纯OCR模式。你的代码只需要检查返回值是否为None：

```python
result = await llm_service.extract_by_llm(...)
if result is None:
    # 使用OCR结果作为备选
    use_ocr_result()
```

### Q: 如何减少Token消耗？

A: 
1. 使用`first_n_pages`只处理前几页
2. 使用`region`只提取特定区域
3. 优化Prompt，使其更简洁
4. 对常见内容使用缓存

### Q: 如何提高提取准确性？

A:
1. 编写更精确的Prompt
2. 启用一致性校验
3. 调整置信度阈值
4. 使用更强大的模型（如GPT-4）

## 更新日志

### v1.0.0 (2025-12-14)
- 初始版本
- 支持OpenAI、ZhipuAI、Claude
- 实现熔断器机制
- 实现一致性校验
- 实现Token消耗跟踪
