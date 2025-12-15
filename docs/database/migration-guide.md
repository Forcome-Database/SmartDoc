# 数据库迁移指南

## 快速开始

### 首次部署

```bash
# 1. 配置环境变量
cp .env.example .env

# 2. 生成初始迁移
python scripts/db_migrate.py generate -m "Initial migration"

# 3. 执行迁移
python scripts/db_migrate.py upgrade

# 4. 导入初始化数据
mysql -u idp_user -p idp_platform < scripts/init.sql
```

### 开发环境

```bash
# 修改模型后生成迁移
python scripts/db_migrate.py generate -m "Add new column"

# 执行迁移
python scripts/db_migrate.py upgrade

# 如有问题，回滚
python scripts/db_migrate.py downgrade
```

## 常用命令

### 使用 db_migrate.py

```bash
python scripts/db_migrate.py generate -m "描述"  # 生成迁移
python scripts/db_migrate.py upgrade             # 升级数据库
python scripts/db_migrate.py downgrade           # 回滚一个版本
python scripts/db_migrate.py history             # 查看历史
python scripts/db_migrate.py sql                 # 查看SQL（不执行）
```

### 直接使用 Alembic

```bash
alembic revision --autogenerate -m "描述"  # 生成迁移
alembic upgrade head                        # 升级
alembic downgrade -1                        # 回滚
alembic current                             # 查看当前版本
alembic history                             # 查看历史
```

## 工作流程

### 1. 修改模型

```python
# app/models/user.py
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(50), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    phone = Column(String(20))  # 新增字段
```

### 2. 生成迁移

```bash
python scripts/db_migrate.py generate -m "Add phone column to users"
```

### 3. 检查迁移脚本

打开 `alembic/versions/xxxx_add_phone_column.py`，确认 SQL 正确。

### 4. 执行迁移

```bash
python scripts/db_migrate.py upgrade
```

### 5. 提交代码

```bash
git add app/models/user.py alembic/versions/xxxx_add_phone_column.py
git commit -m "feat: add phone column to users table"
```

## 生产环境部署

```bash
# 1. 备份数据库
mysqldump -u user -p database > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 查看将要执行的SQL
python scripts/db_migrate.py sql

# 3. 执行迁移
python scripts/db_migrate.py upgrade

# 4. 验证结果
python scripts/db_migrate.py history
```

## 故障排查

### 迁移失败

```bash
python scripts/db_migrate.py downgrade  # 回滚
# 修复问题后重新执行
python scripts/db_migrate.py upgrade
```

### 数据库状态不一致

```bash
alembic current   # 查看当前版本
alembic history   # 查看迁移历史
alembic stamp head  # 手动标记版本（谨慎使用）
```

### 多人开发冲突

```bash
alembic merge -m "Merge migrations" head1 head2
python scripts/db_migrate.py upgrade
```
