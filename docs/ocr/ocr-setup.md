# OCR 引擎配置指南

## 支持的 OCR 引擎

- **PaddleOCR**: 中文识别效果最佳
- **Tesseract**: 速度快，英文效果好
- **UmiOCR**: 开源离线服务

## Tesseract 配置

### 安装语言包

**Windows:**
```bash
# 下载中文语言包
https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata

# 放置到 tessdata 目录
copy chi_sim.traineddata "D:\Work\software\Tesseract\tessdata\"

# 验证
tesseract --list-langs
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr-chi-sim
```

### 环境变量配置

在 `backend/.env` 中：
```bash
TESSERACT_CMD=D:/Work/software/Tesseract/tesseract.exe
TESSDATA_PREFIX=D:/Work/software/Tesseract/tessdata
```

**注意：** 使用正斜杠 `/` 而不是反斜杠 `\`

### 语言代码映射

| 前端配置 | Tesseract | PaddleOCR |
|---------|-----------|-----------|
| zh | chi_sim | ch |
| en | eng | en |
| zh_en | chi_sim+eng | ch |

## PaddleOCR 配置

### 安装

```bash
pip install paddleocr==3.3.0
pip install paddlepaddle==3.0.0
```

### PaddleOCR 3.x API 变更

**初始化（3.x 风格）：**
```python
from paddleocr import PaddleOCR
ocr = PaddleOCR()  # 使用默认配置
```

**调用方式：**
```python
# 3.x 使用 predict()
result = ocr.predict(input=image_path)

# 结果格式
{
  'ocr_result': [
    {'text': '...', 'score': 0.95, 'position': [[x1,y1], ...]}
  ]
}
```

## 性能优化

### 模型选择

| 模型 | 大小 | 加载时间 | 准确度 |
|------|------|----------|--------|
| PP-OCRv5 server | ~150MB | 30-60s | 最高 |
| PP-OCRv4 mobile | ~10MB | 5-10s | 高 |
| Tesseract | ~5MB | <1s | 中 |

### 快速模式配置

```python
# 使用 mobile 模型
self.paddleocr = PaddleOCR(
    text_detection_model_name='PP-OCRv4_mobile_det',
    text_recognition_model_name='PP-OCRv4_mobile_rec',
    lang='ch'
)
```

### 降低 DPI

```python
images = convert_from_path(pdf_path, dpi=200)  # 默认300
```

## 测试验证

```bash
cd backend

# 测试 Tesseract
python -c "import pytesseract; print(pytesseract.get_languages())"

# 测试 PaddleOCR
python -c "from paddleocr import PaddleOCR; print('OK')"

# 完整测试
python test_ocr_engines.py
```
