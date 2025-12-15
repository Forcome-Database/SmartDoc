# 语言规范

## 交流语言
- AI助手：简体中文
- 用户沟通：优先简体中文

## 代码规范

| 内容 | 语言 |
|------|------|
| 代码注释 | 简体中文 |
| Docstring/JSDoc | 简体中文 |
| Git提交信息 | 简体中文 |
| 变量/函数/类名 | 英文 |
| 数据库字段 | 英文 |
| UI文本 | 简体中文 |

## 示例

```python
def process_document(file_path: str) -> dict:
    """处理上传的文档文件"""
    # 执行OCR识别
    result = perform_ocr(file_path)
    return result
```

```javascript
/**
 * 获取任务列表
 * @param {Object} params - 查询参数
 */
async function fetchTaskList(params) {
  // 发送请求到后端API
  return await api.get('/tasks', { params })
}
```
