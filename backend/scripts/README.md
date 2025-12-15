# 数据库脚本工具

本目录包含数据库迁移和初始化相关的脚本工具。

## 文件说明

- `db_migrate.py` - 数据库迁移管理工具（推荐使用）
- `generate_migration.py` - 简单的迁移生成工具
- `init.sql` - 初始化数据SQL脚本

## 快速开始

### 1. 首次部署初始化

```bash
# 进入backend目录
cd backend

# 生成初始迁移脚本
python scripts/db_migrate.py generate -m "Initial migration: create all tables"

# 检查生成的迁移脚本
# 文件位置: backend/alembic/versions/xxxx_initial_migration.py

# 执行数据库迁移
python scripts/db_migrate.py upgrade

# 导入初始化数据
mysql -u idp_user -p idp_platform < scripts/init.sql
# 或使用Docker:
docker-compose exec mysql mysql -u idp_user -p idp_platform < scripts/init.sql
```

### 2. 日常开发流程

当你修改了数据库模型（app/models/）后：

```bash
# 1. 生成迁移脚本
python scripts/db_migrate.py generate -m "描述你的变更"

# 2. 检查生成的迁移脚本
# 确保upgrade()和downgrade()函数正确

# 3. 执行迁移
python scripts/db_migrate.py upgrade

# 4. 测试功能
# ...

# 5. 如果有问题，可以回滚
python scripts/db_migrate.py downgrade
```

## db_migrate.py 使用说明

### 生成迁移脚本

```bash
# 自动检测模型变化并生成迁移
python scripts/db_migrate.py generate -m "Add webhook table"

# 不指定消息（将使用时间戳）
python scripts/db_migrate.py generate
```

### 升级数据库

```bash
# 升级到最新版本
python scripts/db_migrate.py upgrade

# 升级到特定版本
python scripts/db_migrate.py upgrade abc123def456

# 升级一个版本
python scripts/db_migrate.py upgrade +1
```

### 降级数据库

```bash
# 回滚一个版本
python scripts/db_migrate.py downgrade

# 回滚到特定版本
python scripts/db_migrate.py downgrade abc123def456

# 回滚所有迁移
python scripts/db_migrate.py downgrade base
```

### 查看迁移历史

```bash
# 查看当前版本和历史记录
python scripts/db_migrate.py history
```

### 查看SQL语句（不执行）

```bash
# 查看升级SQL
python scripts/db_migrate.py sql

# 查看降级SQL
python scripts/db_migrate.py sql --direction downgrade

# 查看升级到特定版本的SQL
python scripts/db_migrate.py sql --revision abc123
```

### 初始化数据

```bash
# 显示初始化数据导入说明
python scripts/db_migrate.py init
```

## init.sql 说明

初始化数据脚本包含：

1. **默认管理员账号**
   - 用户名: `admin`
   - 密码: `admin123`
   - ⚠️ **生产环境必须修改默认密码！**

2. **系统配置**
   - OCR超时时间
   - LLM超时时间
   - 最大并行任务数
   - Token单价
   - 数据留存期
   - 限流配置
   - 熔断器配置

3. **示例规则**（可选）
   - 增值税发票识别规则示例

## 使用Docker执行迁移

如果使用Docker Compose部署：

```bash
# 进入backend容器
docker-compose exec backend bash

# 在容器内执行迁移
python scripts/db_migrate.py upgrade

# 或直接从宿主机执行
docker-compose exec backend python scripts/db_migrate.py upgrade

# 导入初始化数据
docker-compose exec mysql mysql -u idp_user -p idp_platform < scripts/init.sql
```

## 注意事项

1. **备份数据库**
   - 生产环境执行迁移前务必备份数据库
   - 建议使用 `mysqldump` 或数据库管理工具备份

2. **测试迁移**
   - 在开发环境充分测试升级和降级操作
   - 确保降级函数能正确回滚变更

3. **检查生成的脚本**
   - 自动生成的迁移脚本可能不完美
   - 务必检查并手动调整

4. **版本控制**
   - 所有迁移脚本都应纳入Git版本控制
   - 不要修改已发布的迁移脚本

5. **命名规范**
   - 使用清晰的描述信息
   - 例如: "Add user_role column", "Create webhooks table"

## 常见问题

### Q: 迁移失败怎么办？

```bash
# 1. 查看错误信息
# 2. 回滚到上一个版本
python scripts/db_migrate.py downgrade

# 3. 修复问题后重新执行
python scripts/db_migrate.py upgrade
```

### Q: 如何查看将要执行的SQL？

```bash
# 查看SQL但不执行
python scripts/db_migrate.py sql
```

### Q: 如何重置数据库？

```bash
# 1. 回滚所有迁移
python scripts/db_migrate.py downgrade base

# 2. 重新执行迁移
python scripts/db_migrate.py upgrade

# 3. 重新导入初始化数据
mysql -u idp_user -p idp_platform < scripts/init.sql
```

## 相关文档

- [Alembic迁移文档](../alembic/README.md)
- [数据库设计文档](../../.kiro/specs/enterprise-idp-platform/design.md)
- [Alembic官方文档](https://alembic.sqlalchemy.org/)
