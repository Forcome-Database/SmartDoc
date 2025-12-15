# Enterprise IDP Platform

智能文档处理中台 (Intelligent Document Processing Platform)

## 项目简介

Enterprise IDP Platform 是一个高可用、可溯源、智能化的文档处理平台，支持单页及多页长文档的自动化解析，实现从规则定义、合并提取、人机协同审核到下游安全推送的全链路闭环。

### 核心特性

- 🚀 **高性能处理**: API响应<200ms，单页OCR<3s，支持并行处理
- 🔄 **智能去重**: 基于文件哈希的秒传机制，节省算力成本
- 🤖 **多引擎OCR**: 支持PaddleOCR、Tesseract、UmiOCR
- 🧠 **LLM增强**: 智能提取、一致性校验、自动降级
- 📊 **可视化审核**: 多页PDF预览、OCR高亮、跨页跳转
- 🔐 **安全推送**: HMAC签名、多目标推送、失败重试
- 📈 **实时监控**: 仪表盘、效能分析、异常追踪
- 🔧 **规则引擎**: 版本控制、沙箱测试、配置热更新

## 技术栈

### 后端
- **框架**: FastAPI 0.109+
- **数据库**: MySQL 8.0 + SQLAlchemy 2.0
- **缓存**: Redis 7
- **消息队列**: RabbitMQ 3.12
- **对象存储**: MinIO
- **OCR**: PaddleOCR, Tesseract, UmiOCR
- **LLM**: Agently4

### 前端
- **框架**: Vue 3.5 + Vite 5
- **UI库**: Ant Design Vue 4.2
- **状态管理**: Pinia
- **样式**: Tailwind CSS 3.4
- **图表**: ECharts 5

### 基础设施
- **容器化**: Docker + Docker Compose
- **Web服务器**: Nginx
- **数据库迁移**: Alembic

## 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- Node.js 20+ (本地开发)
- Python 3.11+ (本地开发)

### 使用Docker Compose启动（推荐）

1. **克隆项目**
```bash
git clone <repository-url>
cd enterprise-idp-platform
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，修改以下关键配置：
# - 所有密码（MYSQL_PASSWORD, REDIS_PASSWORD, RABBITMQ_PASSWORD, MINIO_ROOT_PASSWORD）
# - SECRET_KEY（至少32字符）
# - ENCRYPTION_KEY（32字节）
# - AGENTLY_API_KEY（如果使用LLM功能）
```

3. **启动所有服务**

**生产环境部署：**
```bash
# 启动所有服务（MySQL, Redis, RabbitMQ, MinIO, Backend, Frontend, Workers）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
docker-compose logs -f ocr-worker
```

**开发环境部署（包含热重载）：**
```bash
# 启动开发环境（支持代码热重载）
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 查看实时日志
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f
```

4. **初始化数据库**
```bash
# 等待所有服务健康检查通过（约30秒）
docker-compose ps

# 执行数据库迁移
docker-compose exec backend alembic upgrade head

# 创建默认管理员账号（可选）
docker-compose exec backend python scripts/create_admin.py
```

5. **访问应用**
- **前端界面**: http://localhost
- **后端API文档**: http://localhost:8000/api/docs
- **ReDoc文档**: http://localhost:8000/api/redoc
- **RabbitMQ管理界面**: http://localhost:15672 (默认: admin/admin_password)
- **MinIO控制台**: http://localhost:9001 (默认: minioadmin/minioadmin)

6. **停止服务**
```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（警告：会删除所有数据）
docker-compose down -v
```

### Docker 服务说明

| 服务名 | 容器名 | 端口 | 说明 |
|--------|--------|------|------|
| mysql | idp-mysql | 3306 | MySQL 8.0 数据库 |
| redis | idp-redis | 6379 | Redis 7 缓存 |
| rabbitmq | idp-rabbitmq | 5672, 15672 | RabbitMQ 消息队列 |
| minio | idp-minio | 9000, 9001 | MinIO 对象存储 |
| backend | idp-backend | 8000 | FastAPI 后端服务 |
| frontend | idp-frontend | 80 | Nginx + Vue3 前端 |
| ocr-worker | idp-ocr-worker | - | OCR 处理 Worker（2个实例）|
| push-worker | idp-push-worker | - | 推送 Worker |

### Docker 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f [service_name]

# 重启特定服务
docker-compose restart backend

# 重新构建镜像
docker-compose build backend
docker-compose up -d backend

# 进入容器
docker-compose exec backend bash
docker-compose exec mysql mysql -u root -p

# 查看资源使用
docker stats

# 清理未使用的镜像和容器
docker system prune -a
```

### 本地开发

#### 后端开发

1. **创建虚拟环境**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件
```

4. **启动开发服务器**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端开发

1. **安装依赖**
```bash
cd frontend
npm install
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件
```

3. **启动开发服务器**
```bash
npm run dev
```

访问 http://localhost:5173

## 项目结构

```
enterprise-idp-platform/
├── backend/                    # 后端应用
│   ├── app/
│   │   ├── api/               # API端点
│   │   │   └── v1/
│   │   │       └── endpoints/ # 各功能模块端点
│   │   ├── core/              # 核心配置
│   │   ├── models/            # 数据库模型
│   │   ├── services/          # 业务逻辑
│   │   └── tasks/             # 异步任务Worker
│   ├── alembic/               # 数据库迁移
│   ├── scripts/               # 初始化脚本
│   ├── Dockerfile
│   ├── main.py                # 应用入口
│   └── requirements.txt       # Python依赖
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── api/               # API封装
│   │   ├── components/        # 公共组件
│   │   ├── views/             # 页面视图
│   │   ├── router/            # 路由配置
│   │   ├── stores/            # 状态管理
│   │   └── utils/             # 工具函数
│   ├── Dockerfile
│   ├── nginx.conf             # Nginx配置
│   ├── package.json
│   └── vite.config.js
├── .kiro/                      # Kiro配置
│   └── specs/                 # 功能规格文档
├── docker-compose.yml          # Docker编排配置
├── docker-compose.dev.yml      # 开发环境覆盖配置
├── .env.example               # 环境变量模板
├── .gitignore
└── README.md
```

## 核心功能模块

### 1. 文档上传与处理
- 支持PDF和图片格式
- 文件大小限制：20MB
- 页数限制：50页
- 基于SHA256的哈希去重
- 秒传机制节省算力

### 2. OCR识别
- 多引擎支持：PaddleOCR、Tesseract、UmiOCR
- 多页并行处理（最大4并发）
- 备用引擎自动降级
- 跨页文本合并

### 3. 数据提取
- 正则表达式提取
- 锚点定位提取
- 表格提取（支持跨页合并）
- LLM智能提取

### 4. 质量检查
- 必填字段校验
- 格式校验（Email、Phone等）
- 数值范围校验
- 自定义JavaScript表达式校验
- 置信度阈值检查

### 5. 人工审核
- 多页PDF预览
- OCR结果高亮
- 跨页跳转
- 划词回填
- 草稿自动保存

### 6. 安全推送
- HMAC-SHA256签名
- 多目标并行推送
- 指数退避重试（3次）
- 死信队列管理

### 7. 规则管理
- 版本控制（草稿/已发布/归档）
- 沙箱测试
- 配置热更新
- 回滚机制

### 8. 仪表盘
- 核心指标监控
- 任务吞吐趋势
- 规则效能Top10
- 异常分布分析

## API文档

启动后端服务后，访问以下地址查看完整API文档：

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 数据库迁移

```bash
# 创建新迁移
docker-compose exec backend alembic revision --autogenerate -m "description"

# 执行迁移
docker-compose exec backend alembic upgrade head

# 回滚迁移
docker-compose exec backend alembic downgrade -1
```

## 测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm run test
```

## 部署

### 生产环境部署建议

1. **修改默认密码**: 更新 `.env` 文件中的所有密码和密钥
2. **配置HTTPS**: 使用Let's Encrypt或其他SSL证书
3. **配置域名**: 修改 `nginx.conf` 中的 `server_name`
4. **启用防火墙**: 仅开放必要端口（80, 443）
5. **配置备份**: 定期备份MySQL和MinIO数据
6. **监控告警**: 配置日志收集和监控系统

### 扩展性

- **后端扩展**: 增加backend服务实例数
- **Worker扩展**: 增加ocr-worker和push-worker实例数
- **数据库扩展**: 配置MySQL主从复制或集群
- **缓存扩展**: 配置Redis Sentinel或Cluster
- **存储扩展**: 配置MinIO分布式模式

## 故障排查

### 常见问题

1. **数据库连接失败**
   - 检查MySQL服务是否启动
   - 验证数据库连接字符串
   - 确认网络连通性

2. **OCR处理超时**
   - 检查文件大小和页数
   - 调整OCR_TIMEOUT配置
   - 增加Worker实例数

3. **推送失败**
   - 检查Webhook配置
   - 验证网络连通性
   - 查看死信队列

4. **前端无法访问后端**
   - 检查CORS配置
   - 验证代理配置
   - 确认后端服务状态

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

[MIT License](LICENSE)

## 文档

详细的技术文档请查看 [docs](./docs/README.md) 目录：

- [快速启动指南](./docs/getting-started/quick-start.md)
- [环境配置指南](./docs/getting-started/environment-setup.md)
- [Docker部署指南](./docs/getting-started/docker-deployment.md)
- [API参考文档](./docs/api/)
- [OCR配置指南](./docs/ocr/)
- [数据提取指南](./docs/extraction/)
- [故障排查指南](./docs/troubleshooting/)

## 相关文档

- [产品需求文档](./Prd.md)
- [技术栈说明](./TechnologyStack.md)
- [目录结构](./DirectoryStructure.md)

## 许可证

[MIT License](LICENSE)

---

**注意**: 本项目仅供学习和研究使用，生产环境部署前请进行充分的安全评估和性能测试。
