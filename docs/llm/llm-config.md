# LLM 配置示例

所有服务商都使用 OpenAI 兼容协议。

## 核心配置

```bash
LLM_BASE_URL=<API服务地址>
LLM_API_KEY=<API密钥>
LLM_MODEL=<模型名称>
```

## 常见服务商

### OpenAI 官方

```bash
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-proj-xxxxxxxxxxxxx
LLM_MODEL=gpt-3.5-turbo
```

### DeepSeek（国内）

```bash
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-xxxxxxxxxxxxx
LLM_MODEL=deepseek-chat
```

### 阿里云百炼（通义千问）

```bash
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=sk-xxxxxxxxxxxxx
LLM_MODEL=qwen-turbo
```

### 月之暗面（Moonshot/Kimi）

```bash
LLM_BASE_URL=https://api.moonshot.cn/v1
LLM_API_KEY=sk-xxxxxxxxxxxxx
LLM_MODEL=moonshot-v1-8k
```

### 智谱AI（GLM）

```bash
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_API_KEY=your_zhipu_api_key
LLM_MODEL=glm-4
```

## 本地部署

### Ollama

```bash
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=llama2
```

### vLLM

```bash
LLM_BASE_URL=http://localhost:8000/v1
LLM_API_KEY=token-abc123
LLM_MODEL=your-model-name
```

## 完整配置示例

```bash
# LLM配置
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-xxxxxxxxxxxxx
LLM_MODEL=deepseek-chat
LLM_TIMEOUT=60
LLM_TOKEN_PRICE=0.001
LLM_MAX_TOKENS=4000
```

## 模型选择建议

| 需求 | 推荐模型 |
|------|---------|
| 准确性优先 | GPT-4、DeepSeek-V2 |
| 速度优先 | GPT-3.5-turbo、Qwen-turbo |
| 成本优先 | 本地部署、DeepSeek |
| 中文优化 | Qwen、GLM、Moonshot |

## 测试配置

```bash
cd backend
python test_llm_service.py
```
