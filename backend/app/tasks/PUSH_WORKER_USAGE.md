# 推送Worker使用说明

## 概述

推送Worker负责消费推送任务队列，将处理完成的任务结果推送到下游Webhook目标。支持并行推送、指数退避重试和死信队列处理。

## 功能特性

### 1. 并行推送
- 支持同时推送到多个Webhook目标
- 使用`asyncio.gather`实现并发推送
- 每个Webhook的推送结果独立记录

### 2. 指数退避重试
- 默认重试策略：10秒、30秒、90秒
- 最多重试3次
- 支持配置自定义重试延迟

### 3. 死信队列处理
- 重试失败后自动移入死信队列
- 记录详细的失败原因
- 支持手动重推

### 4. 智能重试判断
- 2xx状态码：成功，不重试
- 4xx客户端错误（除429）：不重试
- 429 Too Many Requests：重试
- 5xx服务器错误：重试
- 超时/网络错误：重试

## 启动方式

### 开发环境

```bash
# 直接运行
cd backend
python -m app.tasks.push_worker

# 或使用uvicorn（如果需要）
python app/tasks/push_worker.py
```

### Docker环境

```bash
# 使用docker-compose启动
docker-compose up -d worker-push

# 查看日志
docker-compose logs -f worker-push

# 重启Worker
docker-compose restart worker-push
```

### 生产环境

```bash
# 使用systemd管理
sudo systemctl start idp-push-worker
sudo systemctl status idp-push-worker
sudo systemctl enable idp-push-worker

# 或使用supervisor
supervisorctl start idp-push-worker
supervisorctl status idp-push-worker
```

## 配置说明

### 环境变量

在`.env`文件中配置以下参数：

```bash
# 数据库连接
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/idp_platform

# RabbitMQ连接
RABBITMQ_URL=amqp://user:password@localhost:5672/

# 推送配置
PUSH_TIMEOUT=30  # 推送超时时间（秒）
PUSH_RETRY_MAX=3  # 最大重试次数
PUSH_RETRY_DELAYS=10,30,90  # 重试延迟时间（秒）

# 队列名称
RABBITMQ_QUEUE_PUSH=push_tasks
RABBITMQ_QUEUE_DLQ=push_dlq
```

### 配置文件

在`app/core/config.py`中定义配置类：

```python
class Settings(BaseSettings):
    # 推送配置
    PUSH_TIMEOUT: int = 30
    PUSH_RETRY_MAX: int = 3
    PUSH_RETRY_DELAYS: list[int] = [10, 30, 90]
    
    # 队列配置
    RABBITMQ_QUEUE_PUSH: str = "push_tasks"
    RABBITMQ_QUEUE_DLQ: str = "push_dlq"
```

## 工作流程

### 1. 任务消费

```
1. Worker从push_tasks队列消费消息
2. 解析任务数据（task_id, webhook_id, retry_count）
3. 加载任务和Webhook配置
4. 更新任务状态为PUSHING
```

### 2. 并行推送

```
1. 创建推送服务实例
2. 调用batch_push并行推送到所有Webhook
3. 收集所有推送结果
```

### 3. 结果处理

```
如果全部成功：
  - 更新任务状态为PUSH_SUCCESS
  - 完成处理

如果有失败且未达重试上限：
  - 判断是否应该重试
  - 计算延迟时间
  - 发布延迟重试任务
  - 更新任务状态为PUSHING

如果已达重试上限：
  - 移入死信队列
  - 更新任务状态为PUSH_FAILED
  - 记录失败原因
```

## 消息格式

### 推送任务消息

```json
{
  "task_id": "T_20250115_0001",
  "webhook_id": "WH_001",  // 可选，用于单个Webhook重试
  "retry_count": 0
}
```

### 死信队列消息

任务失败后，相关信息会记录在数据库中，不会发送到死信队列。死信队列主要用于存储无法处理的消息。

## 监控指标

### 日志输出

Worker会输出以下关键日志：

```
INFO - 推送Worker已启动，监听队列: push_tasks
INFO - 开始处理推送任务: task_id=T_xxx, webhook_id=all, retry_count=0
INFO - 推送结果统计: task_id=T_xxx, 成功=2, 失败=0, 总数=2
INFO - 所有推送成功: task_id=T_xxx
INFO - 已安排重试: task_id=T_xxx, webhook=系统A, retry_count=1, delay=10s
WARNING - 推送失败且不应重试，已移入死信队列: task_id=T_xxx, webhook=系统B
ERROR - 推送失败，已达最大重试次数: task_id=T_xxx, retry_count=3, failed=1/2
```

### 性能指标

- 推送成功率：成功推送数 / 总推送数
- 平均推送耗时：所有推送的平均duration_ms
- 重试率：需要重试的推送数 / 总推送数
- 死信队列大小：push_failed状态的任务数

### 数据库查询

```sql
-- 查看推送统计
SELECT 
  status,
  COUNT(*) as count
FROM tasks
WHERE status IN ('pushing', 'push_success', 'push_failed')
GROUP BY status;

-- 查看推送日志
SELECT 
  task_id,
  webhook_id,
  http_status,
  retry_count,
  duration_ms,
  created_at
FROM push_logs
ORDER BY created_at DESC
LIMIT 100;

-- 查看死信队列
SELECT 
  id,
  file_name,
  rule_id,
  error_message,
  completed_at
FROM tasks
WHERE status = 'push_failed'
ORDER BY completed_at DESC;
```

## 故障排查

### 问题1：Worker无法启动

**症状**：Worker启动后立即退出

**可能原因**：
- 数据库连接失败
- RabbitMQ连接失败
- 配置错误

**解决方法**：
```bash
# 检查数据库连接
mysql -h localhost -u user -p -e "SELECT 1"

# 检查RabbitMQ连接
rabbitmqctl status

# 检查配置文件
cat .env | grep -E "DATABASE_URL|RABBITMQ_URL"

# 查看详细日志
python -m app.tasks.push_worker 2>&1 | tee push_worker.log
```

### 问题2：推送一直失败

**症状**：所有推送都失败，不断重试

**可能原因**：
- Webhook URL不可达
- 认证配置错误
- 网络问题

**解决方法**：
```bash
# 测试Webhook连通性
curl -X POST https://webhook.example.com/callback \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# 检查Webhook配置
SELECT id, name, endpoint_url, auth_type, is_active 
FROM webhooks 
WHERE id = 'WH_xxx';

# 查看推送日志
SELECT http_status, error_message, request_body, response_body
FROM push_logs
WHERE task_id = 'T_xxx'
ORDER BY created_at DESC;
```

### 问题3：任务堆积

**症状**：队列中任务数量持续增长

**可能原因**：
- Worker处理速度慢
- Worker数量不足
- 下游系统响应慢

**解决方法**：
```bash
# 查看队列长度
rabbitmqctl list_queues name messages

# 增加Worker数量
docker-compose up -d --scale worker-push=3

# 查看Worker处理速度
# 统计最近1小时的推送数量
SELECT 
  DATE_FORMAT(created_at, '%Y-%m-%d %H:00:00') as hour,
  COUNT(*) as push_count
FROM push_logs
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY hour;
```

### 问题4：内存泄漏

**症状**：Worker内存使用持续增长

**可能原因**：
- 数据库连接未正确关闭
- 大量对象未释放

**解决方法**：
```bash
# 监控内存使用
docker stats worker-push

# 定期重启Worker
# 在crontab中添加
0 2 * * * docker-compose restart worker-push

# 检查数据库连接池
# 在代码中添加监控
logger.info(f"连接池状态: size={engine.pool.size()}, checked_out={engine.pool.checkedout()}")
```

## 最佳实践

### 1. 水平扩展

```yaml
# docker-compose.yml
services:
  worker-push:
    deploy:
      replicas: 3  # 运行3个Worker实例
```

### 2. 优雅关闭

Worker已实现信号处理，支持优雅关闭：

```bash
# 发送SIGTERM信号
kill -TERM <worker_pid>

# Worker会完成当前任务后退出
```

### 3. 监控告警

建议配置以下告警规则：

- 推送成功率 < 95%
- 死信队列大小 > 100
- Worker进程异常退出
- 队列堆积 > 1000

### 4. 日志管理

```python
# 使用结构化日志
logger.info(
    "推送完成",
    extra={
        "task_id": task.id,
        "webhook_id": webhook.id,
        "http_status": result.http_status,
        "duration_ms": result.duration_ms,
        "retry_count": retry_count
    }
)
```

### 5. 性能优化

- 使用连接池复用HTTP连接
- 合理设置超时时间
- 限制并发推送数量
- 使用批量数据库操作

## 相关文档

- [推送服务API文档](../services/push_service.py)
- [消息队列配置](../core/mq.py)
- [Webhook配置说明](../../docs/webhook_config.md)
- [任务状态流转](../../docs/task_status.md)

## 更新日志

### v1.0.0 (2025-01-15)
- 初始版本
- 实现基本推送功能
- 支持指数退避重试
- 支持死信队列处理
- 支持并行推送
