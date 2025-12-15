# 技术栈

## 后端
- Python 3.11+ / FastAPI 0.109+ (异步)
- MySQL 8.0 + SQLAlchemy 2.0 + Alembic
- Redis 7 (缓存) / RabbitMQ 3.12 (消息队列) / MinIO (对象存储)
- OCR: PaddleOCR 3.3 / Tesseract 5.5 / UmiOCR
- LLM: Agently 4.0 (OpenAI兼容协议)
- 安全: python-jose, passlib, bcrypt

## 前端
- Vue 3.5 (Composition API + `<script setup>`)
- Vite 5 / Ant Design Vue 4.2 / Pinia / Tailwind CSS 3.4
- Axios / ECharts 5

## 基础设施
- Docker + Docker Compose
- Nginx (静态文件 + 反向代理)

## 关键版本注意

**PaddleOCR 3.x API 变更：**
- 初始化: `PaddleOCR()` (移除 use_gpu, show_log 参数)
- 调用: `ocr.predict(input=image_path)` (非 `ocr.ocr()`)
- 结果: `{'ocr_result': [{'text': ..., 'score': ..., 'position': ...}]}`

**Tesseract 调用：**
```python
from pytesseract import Output
data = pytesseract.image_to_data(image, lang='eng', output_type=Output.DICT)
```

## 常用命令

```bash
# 开发环境
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 后端
uvicorn main:app --reload --host 0.0.0.0 --port 8000
alembic upgrade head

# 前端
npm run dev
```

## 服务端口
| 服务 | 端口 |
|------|------|
| Frontend | 80 / 5173 (dev) |
| Backend | 8000 |
| MySQL | 3306 |
| Redis | 6379 |
| RabbitMQ | 5672 / 15672 |
| MinIO | 9000 / 9001 |
