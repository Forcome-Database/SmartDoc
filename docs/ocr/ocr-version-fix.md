# OCR 版本兼容性修复

## PaddleOCR 2.x vs 3.x

### 初始化参数变更

**2.x（已废弃）：**
```python
self.paddleocr = PaddleOCR(
    use_angle_cls=True,
    lang='ch',
    use_gpu=False,  # ❌ 3.x不支持
    show_log=False  # ❌ 3.x不支持
)
```

**3.x（当前）：**
```python
self.paddleocr = PaddleOCR()  # 使用默认配置
```

### 调用方式变更

**2.x：**
```python
result = self.paddleocr.ocr(image_path, True)
# 结果: [[[(box), (text, confidence)], ...]]
```

**3.x：**
```python
result = self.paddleocr.predict(input=image_path)
# 结果: {'ocr_result': [{'text': ..., 'score': ..., 'position': ...}]}
```

### 结果解析

**3.x 解析方式：**
```python
if 'ocr_result' in result:
    for item in result['ocr_result']:
        text = item['text']
        confidence = item.get('score', 0.0)
        position = item.get('position', [[0,0], [0,0], [0,0], [0,0]])
```

## Tesseract 参数修复

**错误方式：**
```python
data = pytesseract.image_to_data(
    image,
    language,           # ❌ 位置参数
    self.tesseract_config,
    'dict'              # ❌ 字符串
)
```

**正确方式：**
```python
from pytesseract import Output

data = pytesseract.image_to_data(
    image,
    lang=language,      # ✓ 关键字参数
    config=self.tesseract_config,
    output_type=Output.DICT  # ✓ 使用枚举
)
```

## 常见错误

### Unknown argument: show_log

**原因：** PaddleOCR 3.x 移除了该参数

**解决：** 使用默认配置初始化

### Unknown argument: use_gpu

**原因：** PaddleOCR 3.x 移除了该参数

**解决：** 移除该参数，3.x 自动检测 GPU

### string indices must be integers

**原因：** pytesseract 参数传递方式错误

**解决：** 使用关键字参数和 Output 枚举
