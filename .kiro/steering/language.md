# 语言规范 (Language Guidelines)

## 交流语言

- **AI 助手交流**：使用简体中文进行所有对话和回答
- **用户沟通**：优先使用简体中文，除非用户明确使用其他语言

## 代码注释和文档

- **代码注释**：所有 Python、JavaScript/Vue 代码中的注释使用简体中文
- **文档字符串**：Python docstrings 和 JSDoc 使用简体中文
- **提交信息**：Git commit messages 使用简体中文
- **README 和文档**：项目文档使用简体中文

## 代码命名

- **变量和函数名**：使用英文（遵循各语言的命名规范）
- **类名**：使用英文
- **常量**：使用英文
- **数据库字段**：使用英文

## 示例

### Python 代码示例
```python
def process_document(file_path: str) -> dict:
    """
    处理上传的文档文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        包含处理结果的字典
    """
    # 读取文件内容
    content = read_file(file_path)
    
    # 执行 OCR 识别
    ocr_result = perform_ocr(content)
    
    return ocr_result
```

### Vue 代码示例
```javascript
/**
 * 获取任务列表
 * @param {Object} params - 查询参数
 * @returns {Promise} 任务列表数据
 */
async function fetchTaskList(params) {
  // 发送请求到后端 API
  const response = await api.get('/tasks', { params })
  
  // 返回处理后的数据
  return response.data
}
```

## 用户界面

- **UI 文本**：所有界面文字使用简体中文
- **错误提示**：使用简体中文
- **表单标签**：使用简体中文
- **按钮文字**：使用简体中文
