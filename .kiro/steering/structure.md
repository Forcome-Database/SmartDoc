# 项目结构

## 架构
前后端分离，Docker Compose 编排微服务。

## 目录结构

```
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/endpoints/  # API端点 (auth, tasks, rules, audit, webhook, dashboard, users, system)
│   │   ├── core/              # 核心配置 (config, security, dependencies)
│   │   ├── models/            # SQLAlchemy 模型
│   │   ├── schemas/           # Pydantic 验证
│   │   ├── services/          # 业务逻辑 (OCR, extraction, validation)
│   │   └── tasks/             # 异步Worker (ocr_worker, push_worker)
│   ├── alembic/               # 数据库迁移
│   └── scripts/               # 工具脚本
│
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── api/               # API封装
│   │   ├── components/        # 公共组件
│   │   ├── views/             # 页面视图
│   │   ├── router/            # 路由配置
│   │   ├── stores/            # Pinia状态管理
│   │   └── utils/             # 工具函数
│   └── nginx.conf             # Nginx配置
│
├── docs/                       # 技术文档
├── .kiro/                      # Kiro配置
│   ├── specs/                 # 功能规格
│   └── steering/              # AI指导规则
└── docker-compose.yml          # 服务编排
```

## 代码规范

### 后端
- API版本: `/api/v1/`
- 模型: `app/models/` 一个文件一个实体
- 服务: `app/services/` 无状态服务类
- 命名: snake_case (函数/变量), PascalCase (类)
- 类型提示: 必须使用
- 异步: I/O操作使用 async/await

### 前端
- 组件: PascalCase (`TaskList.vue`)
- API: `src/api/` 按功能模块组织
- 状态: `src/stores/` 一个store一个领域
- 路由: 懒加载
- 命名: camelCase (函数/变量), PascalCase (组件)

### 配置
- 环境变量: `.env` 文件，不提交敏感信息
- 数据库: SQLAlchemy连接池 + Alembic迁移
- CORS: `main.py` 配置
