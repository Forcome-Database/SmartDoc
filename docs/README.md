# 智能文档处理中台 - 文档中心

本目录包含项目的所有技术文档，按功能模块分类整理。

## 📚 文档目录

### 快速开始
- [快速启动指南](./getting-started/quick-start.md) - 项目启动和基本使用
- [环境配置指南](./getting-started/environment-setup.md) - 开发环境配置
- [Docker部署指南](./getting-started/docker-deployment.md) - 容器化部署

### API 参考
- [认证授权 API](./api/auth-api.md) - 登录、登出、Token管理
- [仪表盘 API](./api/dashboard-api.md) - 核心指标、图表数据
- [审核工作台 API](./api/audit-api.md) - 任务审核、草稿管理
- [Webhook API](./api/webhook-api.md) - Webhook配置和测试
- [用户管理 API](./api/user-api.md) - 用户CRUD操作
- [系统配置 API](./api/system-api.md) - 系统参数配置

### OCR 配置
- [OCR 引擎配置](./ocr/ocr-setup.md) - PaddleOCR、Tesseract配置
- [OCR 版本兼容性](./ocr/ocr-version-fix.md) - 版本升级和API变更
- [OCR 性能优化](./ocr/ocr-performance.md) - 沙箱测试性能优化

### 数据提取
- [提取配置指南](./extraction/extraction-guide.md) - Schema定义和提取策略
- [提取问题排查](./extraction/extraction-troubleshooting.md) - 常见问题解决
- [锚点 vs 正则](./extraction/anchor-vs-regex.md) - 提取方式选择

### LLM 集成
- [LLM 配置示例](./llm/llm-config.md) - 各服务商配置
- [LLM 增强提取](./llm/llm-extraction.md) - 智能提取功能

### 数据库
- [数据库迁移指南](./database/migration-guide.md) - Alembic迁移操作

### 故障排查
- [网络问题排查](./troubleshooting/network-troubleshooting.md) - 请求超时、连接问题
- [API连接问题](./troubleshooting/api-connection.md) - 前后端连接问题

### 功能模块
- [Pipeline 数据处理](./features/pipeline.md) - 数据后处理管道
- [UmiOCR 集成](./features/umiocr.md) - UmiOCR服务集成

### 前端开发
- [前端项目说明](./frontend/frontend-readme.md) - Vue3项目结构
- [认证流程测试](./frontend/auth-flow-test.md) - 登录流程测试指南

## 🔗 相关链接

- **API文档**: http://localhost:8000/api/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/api/redoc
- **产品需求文档**: [Prd.md](../Prd.md)
- **技术栈说明**: [TechnologyStack.md](../TechnologyStack.md)
- **目录结构**: [DirectoryStructure.md](../DirectoryStructure.md)

## 📝 文档维护说明

- 所有文档使用简体中文编写
- 代码示例使用英文命名
- 文档更新后请同步更新本索引
