# 核心配置模块

本目录包含系统的核心配置和基础设施客户端。

## 模块说明

### 1. config.py - 配置管理

使用Pydantic BaseSettings从环境变量加载配置。

**主要配置项：**
- 数据库连接（DATABASE_URL, DB_POOL_SIZE等）
- Redis连接（REDIS_URL）
- RabbitMQ连接（RABBITMQ_URL）
- MinIO存储（MINIO_ENDPOINT, MINIO_ACCESS_KEY等）
- 安全配置（SECRET_KEY, ALGORITHM等）
- OCR配置（OCR_TIMEOUT, OCR_MAX_PARALLEL等）
- LLM配置（LLM_TIMEOUT, LLM_TOKEN_PRICE等）

**使用方式：**
```python
from app.core.config import settings

# 访问配置
database_url = settings.DATABASE_URL
max_file_size = settings.MAX_FILE_SIZE
```

### 2. database.py - 数据库连接池

使用SQLAlchemy创建异步数据库引擎和会话管理。

**主要功能：**
- 异步数据库引擎（支持连接池）
- SessionLocal工厂函数
- get_db依赖注入函数
- 数据库初始化和关闭
- 连接池状态监控

**使用方式：**
```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

@router.get("/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    items = result.scalars().all()
    return items
```

### 3. cache.py - Redis缓存

提供Redis缓存操作和限流功能。

**主要功能：**
- 基础缓存操作（get, set, delete, exists）
- 计数器操作（incr）
- 过期时间管理（expire, ttl）
- 限流检查（check_rate_limit）

**使用方式：**
```python
from app.core.cache import redis_client

# 设置缓存
await redis_client.set("key", "value", expire=3600)

# 获取缓存
value = await redis_client.get("key")

# 限流检查
allowed, remaining = await redis_client.check_rate_limit(
    "api:user123:upload",
    limit=100,
    window=60
)
```

### 4. mq.py - RabbitMQ消息队列

提供消息发布和消费功能。

**主要功能：**
- 队列声明（ocr_tasks, push_tasks, push_dlq）
- 消息发布（publish_task）
- 消息消费（consume_tasks）
- 队列管理（get_queue_size, purge_queue）

**使用方式：**
```python
from app.core.mq import rabbitmq_client

# 发布任务
await rabbitmq_client.publish_task(
    "ocr_tasks",
    {"task_id": "T_001", "file_path": "/path/to/file.pdf"}
)

# 消费任务
async def process_task(task_data):
    print(f"处理任务: {task_data['task_id']}")

await rabbitmq_client.consume_tasks("ocr_tasks", process_task)
```

### 5. storage.py - MinIO对象存储

提供文件上传、下载、删除和预签名URL生成功能。

**主要功能：**
- 文件上传（upload_file）
- 文件下载（download_file, download_file_to_path）
- 文件删除（delete_file）
- 预签名URL生成（generate_presigned_url）
- 文件信息查询（file_exists, get_file_info）
- 对象列表（list_objects）

**使用方式：**
```python
from app.core.storage import minio_client

# 上传文件
with open("file.pdf", "rb") as f:
    path = minio_client.upload_file(
        f,
        "2025/12/14/T_001/file.pdf",
        content_type="application/pdf"
    )

# 生成预签名URL
url = minio_client.generate_presigned_url(
    "2025/12/14/T_001/file.pdf",
    expires=timedelta(hours=1)
)

# 下载文件
data = minio_client.download_file("2025/12/14/T_001/file.pdf")
```

## 环境变量配置

在项目根目录创建`.env`文件（参考`.env.example`）：

```bash
# 数据库
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/idp_platform

# Redis
REDIS_URL=redis://localhost:6379/0

# RabbitMQ
RABBITMQ_URL=amqp://user:password@localhost:5672/

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password

# 安全
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256

# OCR
OCR_TIMEOUT=300
OCR_MAX_PARALLEL=4

# LLM
LLM_TIMEOUT=60
LLM_TOKEN_PRICE=0.002
AGENTLY_API_KEY=your-agently-api-key
```

## 测试

运行测试脚本验证配置：

```bash
cd backend
python test_config.py
```

## 依赖项

所有依赖项已在`requirements.txt`中定义：

- `pydantic-settings`: 配置管理
- `sqlalchemy[asyncio]`: 异步数据库ORM
- `aiomysql`: MySQL异步驱动
- `redis[hiredis]`: Redis异步客户端
- `aio-pika`: RabbitMQ异步客户端
- `minio`: MinIO对象存储客户端

## 注意事项

1. **连接池配置**：数据库连接池默认大小为20，最大溢出10，可根据实际负载调整
2. **Redis连接**：使用连接池，最大连接数50
3. **RabbitMQ队列**：所有队列都配置为持久化，消息TTL为1小时
4. **MinIO Bucket**：首次连接时会自动创建bucket（如果不存在）
5. **异步操作**：所有客户端都支持异步操作，需要在async函数中使用await

## 架构设计

所有客户端都采用单例模式，在应用启动时初始化，关闭时清理资源：

```python
# main.py
from app.core import redis_client, rabbitmq_client, minio_client, close_db

@app.on_event("startup")
async def startup():
    await redis_client.connect()
    await rabbitmq_client.connect()
    minio_client.connect()

@app.on_event("shutdown")
async def shutdown():
    await redis_client.close()
    await rabbitmq_client.close()
    await close_db()
```
