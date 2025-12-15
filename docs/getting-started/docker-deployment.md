# Docker 部署指南

## 服务列表

| 服务名 | 容器名 | 端口 | 说明 |
|--------|--------|------|------|
| mysql | idp-mysql | 3306 | MySQL 8.0 数据库 |
| redis | idp-redis | 6379 | Redis 7 缓存 |
| rabbitmq | idp-rabbitmq | 5672, 15672 | RabbitMQ 消息队列 |
| minio | idp-minio | 9000, 9001 | MinIO 对象存储 |
| backend | idp-backend | 8000 | FastAPI 后端服务 |
| frontend | idp-frontend | 80 | Nginx + Vue3 前端 |
| ocr-worker | idp-ocr-worker | - | OCR 处理 Worker |
| push-worker | idp-push-worker | - | 推送 Worker |

## 快速启动

### 生产环境

```bash
docker-compose up -d
docker-compose ps
docker-compose logs -f backend
```

### 开发环境（热重载）

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

## 常用命令

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

# 执行数据库迁移
docker-compose exec backend alembic upgrade head

# 查看资源使用
docker stats

# 停止所有服务
docker-compose down

# 停止并删除数据卷（警告：会删除所有数据）
docker-compose down -v

# 清理未使用的镜像和容器
docker system prune -a
```

## 生产环境部署建议

1. **修改默认密码**：更新 `.env` 文件中的所有密码和密钥
2. **配置HTTPS**：使用 Let's Encrypt 或其他 SSL 证书
3. **配置域名**：修改 `nginx.conf` 中的 `server_name`
4. **启用防火墙**：仅开放必要端口（80, 443）
5. **配置备份**：定期备份 MySQL 和 MinIO 数据
6. **监控告警**：配置日志收集和监控系统

## 扩展性

- **后端扩展**：增加 backend 服务实例数
- **Worker扩展**：增加 ocr-worker 和 push-worker 实例数
- **数据库扩展**：配置 MySQL 主从复制或集群
- **缓存扩展**：配置 Redis Sentinel 或 Cluster
- **存储扩展**：配置 MinIO 分布式模式
