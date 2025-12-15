# LLM 增强提取

## 功能说明

LLM 增强提取通过 Agently 4.0 调用配置的 LLM 模型，智能提取字段值。

## 配置要求

### 环境变量

```bash
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-xxxxxxxxxxxxx
LLM_MODEL=deepseek-chat
LLM_TIMEOUT=60
LLM_TOKEN_PRICE=0.002
LLM_MAX_TOKENS=4000
```

### 依赖包

```bash
pip install agently>=4.0.6
```

## 使用方法

### 前端配置

1. 进入"提取策略"标签页
2. 选择字段
3. 选择提取方式：**LLM智能提取**
4. 配置参数：
   - 上下文范围：全文 / 前N页
   - 提示词模板（可选）
   - 最大Token数

### 提示词模板

可用变量：
- `{field_name}` - 字段名
- `{context}` - 上下文文本
- `{field_type}` - 字段类型

**示例：**
```
请从以下文本中提取{field_name}的值：

{context}

要求：
1. 仔细阅读文本
2. 准确提取值
3. 如果找不到，返回空字符串
```

## 优势

### 智能理解

```
OCR文本：
"The invoice was issued to Forcome (Shanghai) Co., Ltd on 22nd September 2025"

正则表达式：难以匹配（格式不固定）
LLM提取：可以理解并提取公司名称
```

### 容错能力强

即使 OCR 有错误，LLM 也能理解：
```
OCR错误："Inv0ice No: FCM-250922" (o被识别为0)
LLM提取：可以理解这是"Invoice No"
```

### 多语言支持

自动处理中文、英文、日文等多语言文档。

## 成本控制

### Token 使用估算

- 平均上下文：2000 tokens
- 平均输出：100 tokens
- 每次调用：~2100 tokens

### 优化建议

1. 使用"前N页"而不是"全文"
2. 批量提取多个字段
3. 缓存相同文档的结果

## 熔断器保护

- 失败阈值：连续失败 5 次
- 熔断时间：5 分钟
- 降级策略：返回 None，使用纯 OCR 模式

## 与其他方式对比

| 特性 | 正则表达式 | 锚点定位 | LLM智能提取 |
|------|-----------|---------|------------|
| 配置难度 | 中等 | 简单 | 简单 |
| 可靠性 | 高 | 中等 | 高 |
| 容错能力 | 低 | 低 | 高 |
| 成本 | 免费 | 免费 | 付费 |
| 速度 | 快 | 快 | 慢 |

## 最佳实践

1. **混合使用**：结构化字段用正则，复杂字段用 LLM
2. **LLM 作为备用**：先尝试正则，失败时用 LLM
3. **优化上下文**：只发送相关页面
