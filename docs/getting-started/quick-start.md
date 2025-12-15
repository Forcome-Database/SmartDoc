# 快速启动指南

## 前置要求

- Docker 20.10+ 和 Docker Compose 2.0+
- Node.js 20+ (本地开发)
- Python 3.11+ (本地开发)

## Docker Compose 启动（推荐）

### 1. 克隆项目并配置环境变量

```bash
git clone <repository-url>
cd enterprise-idp-platform
cp .env.example .env
# 编辑 .env 文件，修改密码和密钥
```

### 2. 启动所有服务

**生产环境：**
```bash
docker-compose up -d
docker-compose ps  # 查看服务状态
docker-compose logs -f backend  # 查看日志
```

**开发环境（支持热重载）：**
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### 3. 初始化数据库

```bash
docker-compose exec backend alembic upgrade head
docker-compose exec backend python scripts/create_admin.py  # 可选
```

### 4. 访问应用

- **前端界面**: http://localhost
- **API文档**: http://localhost:8000/api/docs
- **RabbitMQ管理**: http://localhost:15672
- **MinIO控制台**: http://localhost:9001

## 本地开发启动

### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

访问 http://localhost:5173

## 常见问题

### 端口被占用

```bash
# 查找占用进程
netstat -ano | findstr :8000
# 结束进程
taskkill /PID <PID> /F
```

### 后端服务未启动

前端请求一直"待处理"状态，通常是后端未启动。确保看到：
```
INFO:     Application startup complete.
```

### 数据库连接失败

检查 `.env` 文件中的 `DATABASE_URL` 配置，确保 MySQL 服务正在运行。

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 80 (生产) / 5173 (开发) | Vue3 前端 |
| Backend | 8000 | FastAPI 后端 |
| MySQL | 3306 | 数据库 |
| Redis | 6379 | 缓存 |
| RabbitMQ | 5672 / 15672 | 消息队列 |
| MinIO | 9000 / 9001 | 对象存储 |
