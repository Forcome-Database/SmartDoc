# Alembic 数据库迁移

本目录包含使用Alembic进行数据库版本控制的迁移脚本。

## 目录结构

```
alembic/
├── versions/          # 迁移脚本目录
├── env.py            # Alembic环境配置
├── script.py.mako    # 迁移脚本模板
└── README.md         # 本文件
```

## 前置条件

1. 确保已安装所有依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量（.env文件）：
   ```bash
   DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/dbname
   ```

3. 确保MySQL数据库服务已启动并可访问

## 常用命令

### 1. 生成迁移脚本

自动检测模型变化并生成迁移脚本：

```bash
cd backend
alembic revision --autogenerate -m "描述变更内容"
```

手动创建空白迁移脚本：

```bash
alembic revision -m "描述变更内容"
```

### 2. 执行迁移

升级到最新版本：

```bash
alembic upgrade head
```

升级到特定版本：

```bash
alembic upgrade <revision_id>
```

升级一个版本：

```bash
alembic upgrade +1
```

### 3. 回滚迁移

回滚到上一个版本：

```bash
alembic downgrade -1
```

回滚到特定版本：

```bash
alembic downgrade <revision_id>
```

回滚所有迁移：

```bash
alembic downgrade base
```

### 4. 查看迁移历史

查看当前版本：

```bash
alembic current
```

查看迁移历史：

```bash
alembic history
```

查看详细历史（包含变更内容）：

```bash
alembic history --verbose
```

### 5. 查看SQL语句

查看升级SQL（不执行）：

```bash
alembic upgrade head --sql
```

查看回滚SQL（不执行）：

```bash
alembic downgrade -1 --sql
```

## 初始化流程

首次部署时，按以下步骤初始化数据库：

```bash
# 1. 进入backend目录
cd backend

# 2. 执行数据库迁移
alembic upgrade head

# 3. 执行初始化数据脚本
mysql -u idp_user -p idp_platform < scripts/init.sql
# 或使用Docker:
docker-compose exec mysql mysql -u idp_user -p idp_platform < scripts/init.sql
```

## 迁移脚本编写规范

### 升级函数（upgrade）

```python
def upgrade() -> None:
    # 创建表
    op.create_table(
        'table_name',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # 添加索引
    op.create_index('idx_name', 'table_name', ['name'])
    
    # 添加外键
    op.create_foreign_key(
        'fk_table_user',
        'table_name', 'users',
        ['user_id'], ['id']
    )
```

### 降级函数（downgrade）

```python
def downgrade() -> None:
    # 删除外键
    op.drop_constraint('fk_table_user', 'table_name', type_='foreignkey')
    
    # 删除索引
    op.drop_index('idx_name', 'table_name')
    
    # 删除表
    op.drop_table('table_name')
```

## 注意事项

1. **检查生成的迁移脚本**：自动生成的脚本可能不完美，务必检查并手动调整

2. **测试迁移**：在开发环境测试升级和降级操作

3. **备份数据**：生产环境执行迁移前务必备份数据库

4. **版本控制**：所有迁移脚本都应纳入Git版本控制

5. **不要修改已发布的迁移**：如需修改，应创建新的迁移脚本

6. **命名规范**：迁移描述应清晰明确，如：
   - "Add user_role column to users table"
   - "Create webhooks table"
   - "Add index on task_status"

## 常见问题

### Q: 迁移失败怎么办？

A: 
1. 检查错误信息
2. 回滚到上一个版本：`alembic downgrade -1`
3. 修复问题后重新执行：`alembic upgrade head`

### Q: 如何处理多人开发时的迁移冲突？

A:
1. 及时同步代码
2. 如有冲突，使用 `alembic merge` 合并分支
3. 测试合并后的迁移脚本

### Q: 生产环境如何安全执行迁移？

A:
1. 在测试环境完整测试
2. 备份生产数据库
3. 选择低峰期执行
4. 准备回滚方案
5. 监控执行过程

## 相关文档

- [Alembic官方文档](https://alembic.sqlalchemy.org/)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [项目数据库设计文档](../../.kiro/specs/enterprise-idp-platform/design.md)
