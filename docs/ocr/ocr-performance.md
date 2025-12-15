# OCR 性能优化

## 问题描述

沙箱测试时 PaddleOCR 加载大型模型（PP-OCRv5_server），导致：
- 首次加载时间长（30-60秒）
- 内存占用高（2-3GB）

## 解决方案

### 方案1：使用 Mobile 模型（推荐）

```python
self.paddleocr = PaddleOCR(
    text_detection_model_name='PP-OCRv4_mobile_det',
    text_recognition_model_name='PP-OCRv4_mobile_rec',
    lang='ch'
)
```

**效果：**
- 启动：5-10秒（vs 30-60秒）
- 内存：~500MB（vs ~2GB）

### 方案2：使用 Tesseract 作为主引擎

沙箱测试使用 Tesseract，生产环境使用 PaddleOCR：

```python
# 沙箱测试
ocr_service = OCRService(fast_mode=True)
result = await ocr_service.process_document(
    file_path=file_path,
    engine='tesseract',
    language='eng'
)
```

### 方案3：预加载模型

在应用启动时预加载：

```python
@app.on_event("startup")
async def startup_event():
    logger.info("Preloading OCR engines...")
    ocr_service = OCRService()
    logger.info("OCR engines loaded")
```

## 性能对比

| 配置 | 沙箱测试时间 |
|------|-------------|
| 修复前（PP-OCRv5 server） | 30-60秒 |
| 修复后（Tesseract） | 3-8秒 |

## 配置建议

### 开发/测试环境

```python
ocr_service = OCRService(fast_mode=True)
result = await ocr_service.process_document(
    engine='tesseract',
    language='eng'
)
```

### 生产环境

```python
ocr_service = OCRService(fast_mode=False)
result = await ocr_service.process_document(
    engine='paddleocr',
    enable_fallback=True,
    fallback_engine='tesseract'
)
```

## 环境变量优化

```bash
# 禁用自动下载
PADDLEOCR_AUTO_DOWNLOAD=false

# 使用本地缓存
PADDLEOCR_HOME=C:/Users/leo/.paddlex

# 限制CPU线程数
OMP_NUM_THREADS=4
```
