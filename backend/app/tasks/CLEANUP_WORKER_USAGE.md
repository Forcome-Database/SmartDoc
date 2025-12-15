# 清理Worker使用文档

## 概述

清理Worker是一个定时任务服务，负责自动清理超过留存期的文件，释放存储空间。

## 功能特性

- **定时执行**：每日凌晨02:00自动执行清理任务
- **智能清理**：仅删除已完成或已驳回状态的任务文件
- **配置灵活**：通过系统配置表动态调整留存期
- **详细日志**：记录清理数量、释放空间、执行耗时等信息
- **异常通知**：清理失败时通知管理员

## 清理规则

### 清理条件

文件必须同时满足以下条件才会被清理：

1. **时间条件**：创建时间早于（当前时间 - 留存期）
2. **状态条件**：任务状态为 `Completed` 或 `Rejected`
3. **文件存在**：任务的 `file_path` 字段不为空

### 留存期配置

留存期通过系统配置表 `system_configs` 管理：

```sql
-- 查看当前配置
SELECT * FROM system_configs WHERE `key` = 'file_retention_days';

-- 设置留存期为30天
INSERT INTO system_configs (`key`, `value`, `description`)
VALUES ('file_retention_days', 30, '文件留存期（天）')
ON DUPLICATE KEY UPDATE `value` = 30;

-- 设置留存期为60天
UPDATE system_configs 
SET `value` = 60 
WHERE `key` = 'file_retention_days';
```

**默认值**：如果未配置，默认为 30 天

## 运行方式

### 1. 独立运行

```bash
# 进入backend目录
cd backend

# 运行清理Worker
python -m app.tasks.cleanup_worker
```

### 2. Docker运行

在 `docker-compose.yml` 中添加清理Worker服务：

```yaml
worker-cleanup:
  build:
    context: ./backend
    dockerfile: Dockerfile
  container_name: idp-worker-cleanup
  environment:
    DATABASE_URL: mysql+aiomysql://${MYSQL_USER}:${MYSQL_PASSWORD}@mysql:3306/idp_platform
    MINIO_ENDPOINT: minio:9000
    MINIO_ACCESS_KEY: ${MINIO_ROOT_USER}
    MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD}
  volumes:
    - ./backend:/app
  depends_on:
    - backend
  command: python -m app.tasks.cleanup_worker
```

启动服务：

```bash
docker-compose up -d worker-cleanup
```

### 3. 手动触发清理

如果需要立即执行清理（不等待定时任务），可以调用清理方法：

```python
from app.tasks.cleanup_worker import cleanup_worker
import asyncio

# 手动执行清理
asyncio.run(cleanup_worker.execute_cleanup())
```

## 日志示例

### 正常执行日志

```
2025-12-14 02:00:00 [INFO] ============================================================
2025-12-14 02:00:00 [INFO] 开始执行定时清理任务
2025-12-14 02:00:00 [INFO] ============================================================
2025-12-14 02:00:00 [INFO] 文件留存期配置: 30 天
2025-12-14 02:00:00 [INFO] 清理截止日期: 2025-11-14 02:00:00
2025-12-14 02:00:01 [INFO] 找到 15 个任务需要清理
2025-12-14 02:00:02 [INFO] 文件已删除: 2025/11/10/T_20251110_0001/invoice.pdf (任务ID: T_20251110_0001, 大小: 2.35 MB)
2025-12-14 02:00:02 [INFO] 文件已删除: 2025/11/10/T_20251110_0002/contract.pdf (任务ID: T_20251110_0002, 大小: 1.87 MB)
...
2025-12-14 02:00:05 [INFO] ============================================================
2025-12-14 02:00:05 [INFO] 清理任务完成: 删除文件数=15, 失败数=0, 释放空间=45.67 MB, 耗时=5.23秒
2025-12-14 02:00:05 [INFO] ============================================================
```

### 无文件需要清理

```
2025-12-14 02:00:00 [INFO] ============================================================
2025-12-14 02:00:00 [INFO] 开始执行定时清理任务
2025-12-14 02:00:00 [INFO] ============================================================
2025-12-14 02:00:00 [INFO] 文件留存期配置: 30 天
2025-12-14 02:00:00 [INFO] 清理截止日期: 2025-11-14 02:00:00
2025-12-14 02:00:01 [INFO] 没有需要清理的文件
```

### 清理失败日志

```
2025-12-14 02:00:02 [WARNING] 文件删除失败: 2025/11/10/T_20251110_0003/doc.pdf (任务ID: T_20251110_0003)
2025-12-14 02:00:05 [INFO] 清理任务完成: 删除文件数=14, 失败数=1, 释放空间=43.21 MB, 耗时=5.45秒
```

## 监控与维护

### 查看清理统计

可以通过日志文件查看历史清理记录：

```bash
# 查看最近的清理日志
grep "清理任务完成" backend/logs/idp.log | tail -10

# 统计本月清理的文件数
grep "清理任务完成" backend/logs/idp.log | \
  grep "2025-12" | \
  awk -F'删除文件数=' '{print $2}' | \
  awk -F',' '{sum+=$1} END {print sum}'
```

### 调整清理时间

如果需要修改清理时间（默认02:00），编辑 `cleanup_worker.py`：

```python
# 修改为每日凌晨03:30执行
self.scheduler.add_job(
    self.execute_cleanup,
    trigger=CronTrigger(hour=3, minute=30),  # 修改这里
    id='daily_cleanup',
    name='每日文件清理任务',
    replace_existing=True
)
```

### 暂停清理任务

如果需要临时暂停清理任务：

```bash
# 停止清理Worker容器
docker-compose stop worker-cleanup

# 或者删除容器
docker-compose rm -f worker-cleanup
```

## 注意事项

1. **不可恢复**：文件删除后无法恢复，请谨慎配置留存期
2. **状态限制**：只会删除已完成或已驳回的任务文件，处理中的任务不受影响
3. **数据库记录**：清理只删除MinIO中的文件，数据库中的任务记录保留
4. **存储空间**：定期检查MinIO存储空间，确保有足够空间
5. **性能影响**：清理任务在凌晨执行，避免影响业务高峰期

## 故障排查

### 问题1：清理任务未执行

**可能原因**：
- Worker进程未启动
- 调度器配置错误
- 数据库连接失败

**解决方法**：
```bash
# 检查Worker进程状态
docker-compose ps worker-cleanup

# 查看Worker日志
docker-compose logs -f worker-cleanup

# 重启Worker
docker-compose restart worker-cleanup
```

### 问题2：文件删除失败

**可能原因**：
- MinIO连接失败
- 文件路径不存在
- 权限不足

**解决方法**：
```bash
# 检查MinIO连接
docker-compose exec backend python -c "from app.services.file_service import file_service; print(file_service.client.bucket_exists('idp-files'))"

# 检查文件是否存在
docker-compose exec backend python -c "from app.services.file_service import file_service; print(file_service.file_exists('2025/11/10/T_20251110_0001/invoice.pdf'))"
```

### 问题3：留存期配置未生效

**可能原因**：
- 配置表中没有记录
- 配置值格式错误

**解决方法**：
```sql
-- 检查配置
SELECT * FROM system_configs WHERE `key` = 'file_retention_days';

-- 重新设置配置
UPDATE system_configs 
SET `value` = 30 
WHERE `key` = 'file_retention_days';
```

## 相关需求

- **需求4**：数据生命周期策略
- **需求62**：定时清理任务执行

## 相关文件

- `app/tasks/cleanup_worker.py`：清理Worker实现
- `app/services/file_service.py`：文件服务（删除文件）
- `app/models/system_config.py`：系统配置模型
- `app/models/task.py`：任务模型
