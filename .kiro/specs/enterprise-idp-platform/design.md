# Design Document - Enterprise IDP Platform

## Overview

本文档描述智能文档处理中台（IDP Platform）的技术设计方案。系统采用前后端分离架构，基于FastAPI + Vue 3技术栈，实现高可用、可扩展的文档智能处理能力。

### 核心设计目标

1. **高性能**：API响应<200ms，单页OCR<3s，支持并行处理
2. **高可用**：无状态设计，支持K8s水平扩展，消息队列持久化
3. **可溯源**：完整的审计日志，版本控制，操作记录
4. **安全性**：TLS加密传输，AES-256数据加密，HMAC签名验证
5. **智能化**：OCR + LLM双引擎，自动增强，一致性校验

### 技术栈总览

**后端**：Python 3.11+ | FastAPI | SQLAlchemy 2.0 | MySQL 8.0 | Redis 7 | RabbitMQ | MinIO | PaddleOCR | Agently4

**前端**：Vue 3.5 | Vite 7 | Ant Design Vue 4.2 | Pinia | Tailwind CSS 3.4 | Axios

**基础设施**：Docker | Docker Compose | Nginx | Alembic

## Architecture

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Web Browser │  │  Mobile App  │  │  API Client  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Nginx (Proxy)  │
                    └────────┬────────┘
                             │
          ┌──────────────────┴──────────────────┐
          │                                     │
┌─────────▼─────────┐              ┌───────────▼──────────┐
│  Frontend (Vue3)  │              │  Backend (FastAPI)   │
│  - Dashboard      │              │  - API Endpoints     │
│  - Rule Editor    │              │  - Business Logic    │
│  - Audit Workbench│              │  - Authentication    │
│  - Task List      │              │  - File Upload       │
└───────────────────┘              └───────────┬──────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
          ┌─────────▼─────────┐    ┌──────────▼──────────┐   ┌──────────▼──────────┐
          │  MySQL Database   │    │  Redis Cache        │   │  RabbitMQ Queue     │
          │  - Users          │    │  - Rule Config      │   │  - Task Queue       │
          │  - Rules          │    │  - Session          │   │  - DLQ              │
          │  - Tasks          │    │  - Rate Limit       │   └──────────┬──────────┘
          │  - Audit Logs     │    └─────────────────────┘              │
          └───────────────────┘                                         │
                                                              ┌──────────▼──────────┐
                                                              │  Worker Processes   │
                                                              │  - OCR Processing   │
                                                              │  - LLM Extraction   │
                                                              │  - Data Validation  │
                                                              └──────────┬──────────┘
                                                                         │
                    ┌────────────────────────────────────────────────────┼──────────┐
                    │                                                    │          │
          ┌─────────▼─────────┐              ┌────────────────────┐    │    ┌─────▼──────┐
          │  MinIO Storage    │              │  External Services │    │    │  Webhook   │
          │  - PDF Files      │              │  - PaddleOCR       │    │    │  Targets   │
          │  - Images         │              │  - Tesseract       │    │    └────────────┘
          │  - Results        │              │  - Azure OCR       │    │
          └───────────────────┘              │  - Agently4 (LLM)  │    │
                                             └────────────────────┘    │
                                                                       │
                                             ┌─────────────────────────▼──┐
                                             │  Scheduled Tasks           │
                                             │  - Data Cleanup (02:00)    │
                                             │  - Metrics Aggregation     │
                                             └────────────────────────────┘
```

### 核心处理流程

```
1. 文件上传 → 2. 哈希去重 → 3. 入队列 → 4. Worker消费
                    ↓ Hit                      ↓
                5. 秒传返回              6. OCR识别
                                              ↓
                                        7. 文本合并
                                              ↓
                                        8. 数据提取
                                              ↓
                                        9. 质量检查
                                         ↙        ↘
                                   10a. 直通      10b. 待审核
                                        ↓              ↓
                                   11. 推送      12. 人工修正
                                        ↓              ↓
                                   13. 成功      14. 提交推送
                                        ↓              ↓
                                   15. 记录日志  16. 记录日志
```

## Components and Interfaces

### 后端组件结构

#### 1. API Layer (app/api/)

**职责**：处理HTTP请求，参数验证，路由分发

**主要模块**：
- `v1/endpoints/auth.py`：用户认证、登录、登出
- `v1/endpoints/upload.py`：文件上传、哈希去重
- `v1/endpoints/tasks.py`：任务查询、状态更新
- `v1/endpoints/rules.py`：规则CRUD、版本管理、沙箱测试
- `v1/endpoints/audit.py`：审核工作台API、任务修正
- `v1/endpoints/webhook.py`：Webhook配置、连通性测试
- `v1/endpoints/dashboard.py`：仪表盘数据、统计图表
- `v1/endpoints/users.py`：用户管理、角色分配
- `v1/endpoints/system.py`：系统配置、数据生命周期

**接口设计原则**：
- RESTful风格，使用标准HTTP方法
- 统一响应格式：`{"code": int, "message": str, "data": any}`
- 使用Pydantic Schema进行请求/响应验证
- 支持分页、筛选、排序

#### 2. Core Layer (app/core/)

**职责**：核心配置、安全机制、工具函数

**主要模块**：
- `config.py`：环境变量加载、配置管理
- `security.py`：JWT生成/验证、密码加密、API Key管理
- `database.py`：数据库连接池、Session管理
- `cache.py`：Redis连接、缓存操作
- `mq.py`：RabbitMQ连接、消息发布/消费
- `storage.py`：MinIO客户端、文件上传/下载
- `logger.py`：日志配置、结构化日志
- `exceptions.py`：自定义异常类
- `middleware.py`：请求日志、限流、CORS

**关键设计**：
```python
# config.py
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    
    # Redis
    REDIS_URL: str
    
    # RabbitMQ
    RABBITMQ_URL: str
    
    # MinIO
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OCR
    OCR_TIMEOUT: int = 300
    OCR_MAX_PARALLEL: int = 4
    
    # LLM
    LLM_TIMEOUT: int = 60
    LLM_TOKEN_PRICE: float = 0.002
    
    class Config:
        env_file = ".env"
```


#### 3. Models Layer (app/models/)

**职责**：数据库模型定义，ORM映射

**主要模型**：
- `user.py`：用户表、角色枚举
- `rule.py`：规则表、规则版本表
- `task.py`：任务表、任务状态枚举
- `webhook.py`：Webhook配置表
- `audit_log.py`：审计日志表
- `push_log.py`：推送日志表
- `api_key.py`：API Key表
- `system_config.py`：系统配置表

**关键模型设计**：
```python
# task.py
class TaskStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    PENDING_AUDIT = "pending_audit"
    COMPLETED = "completed"
    REJECTED = "rejected"
    PUSHING = "pushing"
    PUSH_SUCCESS = "push_success"
    PUSH_FAILED = "push_failed"

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String(50), primary_key=True)  # T_20251214_0001
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    page_count = Column(Integer, default=1)
    
    rule_id = Column(String(50), ForeignKey("rules.id"), nullable=False)
    rule_version = Column(String(20), nullable=False)
    
    status = Column(Enum(TaskStatus), default=TaskStatus.QUEUED, index=True)
    is_instant = Column(Boolean, default=False)  # 秒传标识
    
    # OCR结果
    ocr_text = Column(Text)  # 合并后的全文
    ocr_result = Column(JSON)  # 完整OCR结果（含坐标）
    
    # 提取结果
    extracted_data = Column(JSON)
    confidence_scores = Column(JSON)  # 字段置信度
    
    # 审核信息
    audit_reasons = Column(JSON)  # 审核原因列表
    auditor_id = Column(String(50), ForeignKey("users.id"))
    audited_at = Column(DateTime)
    
    # LLM信息
    llm_token_count = Column(Integer, default=0)
    llm_cost = Column(Numeric(10, 4), default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # 关系
    rule = relationship("Rule", back_populates="tasks")
    push_logs = relationship("PushLog", back_populates="task")
```

```python
# rule.py
class RuleStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class Rule(Base):
    __tablename__ = "rules"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    document_type = Column(String(50))
    
    # 当前发布版本
    current_version = Column(String(20))
    
    created_by = Column(String(50), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # 关系
    versions = relationship("RuleVersion", back_populates="rule")
    tasks = relationship("Task", back_populates="rule")

class RuleVersion(Base):
    __tablename__ = "rule_versions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(String(50), ForeignKey("rules.id"), nullable=False)
    version = Column(String(20), nullable=False)  # V1.0, V1.1
    status = Column(Enum(RuleStatus), default=RuleStatus.DRAFT)
    
    # 配置内容（JSON格式）
    config = Column(JSON, nullable=False)
    # {
    #   "ocr_engine": "paddleocr",
    #   "language": "zh",
    #   "page_strategy": "multi_page",
    #   "page_separator": "\n",
    #   "schema": {...},
    #   "extraction_rules": [...],
    #   "validation_rules": [...],
    #   "enhancement": {...}
    # }
    
    published_at = Column(DateTime)
    published_by = Column(String(50), ForeignKey("users.id"))
    
    # 关系
    rule = relationship("Rule", back_populates="versions")
```

#### 4. Services Layer (app/services/)

**职责**：核心业务逻辑实现

**主要服务**：
- `hash_service.py`：文件哈希计算、去重判断
- `ocr_service.py`：OCR引擎调用、结果解析
- `llm_service.py`：LLM调用、Prompt构建
- `extraction_service.py`：数据提取引擎（正则/锚点/表格/LLM）
- `validation_service.py`：数据校验、清洗
- `push_service.py`：Webhook推送、签名计算
- `rule_service.py`：规则管理、版本控制
- `task_service.py`：任务管理、状态流转
- `file_service.py`：文件上传、下载、清理
- `metrics_service.py`：指标统计、数据聚合

**关键服务设计**：
```python
# ocr_service.py
class OCRService:
    def __init__(self):
        self.paddleocr = PaddleOCR(use_angle_cls=True, lang='ch')
        self.tesseract_config = '--oem 3 --psm 6'
    
    async def process_document(
        self, 
        file_path: str, 
        engine: str, 
        page_strategy: dict
    ) -> OCRResult:
        """处理文档OCR"""
        # 1. 判断文件类型和页数
        page_count = self._get_page_count(file_path)
        pages_to_process = self._parse_page_strategy(page_strategy, page_count)
        
        # 2. 并行OCR处理
        if len(pages_to_process) > 5:
            results = await self._parallel_ocr(file_path, pages_to_process, engine)
        else:
            results = await self._sequential_ocr(file_path, pages_to_process, engine)
        
        # 3. 合并文本
        merged_text = self._merge_ocr_text(results, page_strategy.get('separator', '\n'))
        
        return OCRResult(
            merged_text=merged_text,
            page_results=results,
            page_count=len(pages_to_process)
        )
    
    async def _parallel_ocr(self, file_path: str, pages: List[int], engine: str):
        """并行OCR处理"""
        tasks = []
        for page_num in pages:
            task = asyncio.create_task(self._ocr_single_page(file_path, page_num, engine))
            tasks.append(task)
        return await asyncio.gather(*tasks)
    
    def _merge_ocr_text(self, results: List[PageOCRResult], separator: str) -> str:
        """合并多页OCR文本"""
        texts = [r.text for r in results]
        return separator.join(texts)
```

```python
# extraction_service.py
class ExtractionService:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
    
    async def extract_fields(
        self, 
        ocr_result: OCRResult, 
        schema: dict, 
        extraction_rules: List[dict]
    ) -> dict:
        """根据规则提取字段"""
        extracted = {}
        
        for field_name, field_config in schema.items():
            rule = self._find_extraction_rule(field_name, extraction_rules)
            
            if rule['type'] == 'regex':
                value = self._extract_by_regex(ocr_result.merged_text, rule)
            elif rule['type'] == 'anchor':
                value = self._extract_by_anchor(ocr_result, rule)
            elif rule['type'] == 'table':
                value = self._extract_table(ocr_result, rule)
            elif rule['type'] == 'llm':
                value = await self._extract_by_llm(ocr_result, rule)
            else:
                value = None
            
            extracted[field_name] = {
                'value': value,
                'confidence': self._calculate_confidence(value, rule),
                'source_page': self._get_source_page(value, ocr_result)
            }
        
        return extracted
    
    def _extract_by_regex(self, text: str, rule: dict) -> str:
        """正则提取"""
        pattern = rule['pattern']
        match = re.search(pattern, text)
        return match.group(1) if match else None
    
    def _extract_table(self, ocr_result: OCRResult, rule: dict) -> List[dict]:
        """表格提取（支持跨页合并）"""
        tables = []
        current_table = None
        
        for page_result in ocr_result.page_results:
            page_tables = self._detect_tables(page_result)
            
            for table in page_tables:
                if current_table and self._is_continuation(current_table, table):
                    # 跨页表格合并
                    current_table['rows'].extend(table['rows'][1:])  # 跳过重复表头
                else:
                    if current_table:
                        tables.append(current_table)
                    current_table = table
        
        if current_table:
            tables.append(current_table)
        
        return tables
```


#### 5. Tasks Layer (app/tasks/)

**职责**：异步任务处理，Worker进程

**主要任务**：
- `ocr_worker.py`：OCR处理Worker
- `push_worker.py`：推送Worker
- `cleanup_worker.py`：定时清理任务

**Worker设计**：
```python
# ocr_worker.py
import pika
from app.services import OCRService, ExtractionService, ValidationService
from app.core.database import get_db

class OCRWorker:
    def __init__(self):
        self.ocr_service = OCRService()
        self.extraction_service = ExtractionService()
        self.validation_service = ValidationService()
        
        # RabbitMQ连接
        self.connection = pika.BlockingConnection(
            pika.URLParameters(settings.RABBITMQ_URL)
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='ocr_tasks', durable=True)
    
    def start(self):
        """启动Worker"""
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue='ocr_tasks',
            on_message_callback=self.process_task
        )
        print("OCR Worker started. Waiting for messages...")
        self.channel.start_consuming()
    
    def process_task(self, ch, method, properties, body):
        """处理单个任务"""
        try:
            task_data = json.loads(body)
            task_id = task_data['task_id']
            
            # 1. 更新任务状态为Processing
            self._update_task_status(task_id, TaskStatus.PROCESSING)
            
            # 2. 下载文件
            file_path = self._download_file(task_data['file_path'])
            
            # 3. 加载规则配置
            rule_config = self._load_rule_config(
                task_data['rule_id'], 
                task_data['rule_version']
            )
            
            # 4. OCR处理
            ocr_result = await self.ocr_service.process_document(
                file_path, 
                rule_config['ocr_engine'],
                rule_config['page_strategy']
            )
            
            # 5. 数据提取
            extracted = await self.extraction_service.extract_fields(
                ocr_result,
                rule_config['schema'],
                rule_config['extraction_rules']
            )
            
            # 6. LLM增强（如果配置）
            if rule_config.get('enhancement', {}).get('enabled'):
                extracted = await self._enhance_with_llm(extracted, ocr_result, rule_config)
            
            # 7. 数据清洗
            cleaned = self.validation_service.clean_data(
                extracted, 
                rule_config['cleaning_rules']
            )
            
            # 8. 数据校验
            validation_result = self.validation_service.validate(
                cleaned,
                rule_config['validation_rules']
            )
            
            # 9. 判断是否需要人工审核
            if validation_result.has_errors or self._low_confidence(cleaned):
                self._update_task_status(
                    task_id, 
                    TaskStatus.PENDING_AUDIT,
                    audit_reasons=validation_result.errors
                )
            else:
                self._update_task_status(task_id, TaskStatus.COMPLETED)
                # 触发推送
                self._publish_push_task(task_id)
            
            # 10. 保存结果
            self._save_task_result(task_id, ocr_result, cleaned)
            
            # 11. 确认消息
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}")
            self._update_task_status(task_id, TaskStatus.FAILED, error=str(e))
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
```

```python
# push_worker.py
class PushWorker:
    def __init__(self):
        self.push_service = PushService()
        self.connection = pika.BlockingConnection(
            pika.URLParameters(settings.RABBITMQ_URL)
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='push_tasks', durable=True)
        self.channel.queue_declare(queue='push_dlq', durable=True)  # 死信队列
    
    def process_push(self, ch, method, properties, body):
        """处理推送任务"""
        task_data = json.loads(body)
        task_id = task_data['task_id']
        retry_count = task_data.get('retry_count', 0)
        
        try:
            # 1. 加载任务和Webhook配置
            task = self._load_task(task_id)
            webhooks = self._load_webhooks(task.rule_id)
            
            # 2. 并行推送到所有目标
            results = await asyncio.gather(*[
                self.push_service.push(task, webhook)
                for webhook in webhooks
            ])
            
            # 3. 检查推送结果
            all_success = all(r.success for r in results)
            
            if all_success:
                self._update_task_status(task_id, TaskStatus.PUSH_SUCCESS)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                # 部分失败，重试
                if retry_count < 3:
                    self._retry_push(task_id, retry_count + 1)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    # 进入死信队列
                    self._move_to_dlq(task_data)
                    self._update_task_status(task_id, TaskStatus.PUSH_FAILED)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
        
        except Exception as e:
            logger.error(f"Push failed for task {task_id}: {str(e)}")
            if retry_count < 3:
                self._retry_push(task_id, retry_count + 1)
            else:
                self._move_to_dlq(task_data)
    
    def _retry_push(self, task_id: str, retry_count: int):
        """指数退避重试"""
        delay = 10 * (3 ** (retry_count - 1))  # 10s, 30s, 90s
        
        # 延迟发布消息
        self.channel.basic_publish(
            exchange='',
            routing_key='push_tasks',
            body=json.dumps({'task_id': task_id, 'retry_count': retry_count}),
            properties=pika.BasicProperties(
                delivery_mode=2,
                expiration=str(delay * 1000)  # 毫秒
            )
        )
```

### 前端组件结构

#### 1. Views (src/views/)

**主要页面**：
- `Dashboard.vue`：仪表盘
- `RuleList.vue`：规则列表
- `RuleEditor.vue`：规则编辑器
- `TaskList.vue`：任务列表
- `AuditWorkbench.vue`：审核工作台
- `WebhookConfig.vue`：Webhook配置
- `UserManagement.vue`：用户管理
- `SystemSettings.vue`：系统设置

#### 2. Components (src/components/)

**公共组件**：
- `MetricCard.vue`：指标卡片
- `ChartContainer.vue`：图表容器
- `PDFViewer.vue`：PDF预览器（支持分页、缩放、高亮）
- `SchemaEditor.vue`：Schema编辑器（树形结构）
- `RuleVersionSelector.vue`：版本选择器
- `ConfidenceBadge.vue`：置信度徽章
- `StatusTag.vue`：状态标签
- `FileUploader.vue`：文件上传器

#### 3. Stores (src/stores/)

**状态管理**：
- `authStore.js`：用户认证状态
- `ruleStore.js`：规则数据缓存
- `taskStore.js`：任务列表状态
- `dashboardStore.js`：仪表盘数据

**Store设计示例**：
```javascript
// taskStore.js
import { defineStore } from 'pinia'
import { taskAPI } from '@/api/task'

export const useTaskStore = defineStore('task', {
  state: () => ({
    tasks: [],
    currentTask: null,
    filters: {
      status: null,
      rule_id: null,
      date_range: null
    },
    pagination: {
      page: 1,
      page_size: 20,
      total: 0
    }
  }),
  
  actions: {
    async fetchTasks() {
      const response = await taskAPI.list({
        ...this.filters,
        ...this.pagination
      })
      this.tasks = response.data.items
      this.pagination.total = response.data.total
    },
    
    async fetchTaskDetail(taskId) {
      const response = await taskAPI.get(taskId)
      this.currentTask = response.data
    },
    
    async updateTaskStatus(taskId, status, data) {
      await taskAPI.updateStatus(taskId, status, data)
      await this.fetchTasks()
    }
  }
})
```

#### 4. API Layer (src/api/)

**API封装**：
```javascript
// api/task.js
import axios from '@/utils/request'

export const taskAPI = {
  list(params) {
    return axios.get('/api/v1/tasks', { params })
  },
  
  get(taskId) {
    return axios.get(`/api/v1/tasks/${taskId}`)
  },
  
  upload(formData) {
    return axios.post('/api/v1/ocr/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  updateStatus(taskId, status, data) {
    return axios.patch(`/api/v1/tasks/${taskId}/status`, { status, ...data })
  },
  
  exportTasks(params) {
    return axios.get('/api/v1/tasks/export', {
      params,
      responseType: 'blob'
    })
  }
}
```

## Data Models

### 核心数据库表设计

#### users表
```sql
CREATE TABLE users (
    id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'architect', 'auditor', 'visitor') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### rules表
```sql
CREATE TABLE rules (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    document_type VARCHAR(50),
    current_version VARCHAR(20),
    created_by VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_code (code),
    INDEX idx_document_type (document_type),
    FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### rule_versions表
```sql
CREATE TABLE rule_versions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    rule_id VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    status ENUM('draft', 'published', 'archived') DEFAULT 'draft',
    config JSON NOT NULL,
    published_at DATETIME,
    published_by VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_rule_version (rule_id, version),
    INDEX idx_status (status),
    FOREIGN KEY (rule_id) REFERENCES rules(id) ON DELETE CASCADE,
    FOREIGN KEY (published_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### tasks表
```sql
CREATE TABLE tasks (
    id VARCHAR(50) PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    page_count INT DEFAULT 1,
    rule_id VARCHAR(50) NOT NULL,
    rule_version VARCHAR(20) NOT NULL,
    status ENUM('queued', 'processing', 'pending_audit', 'completed', 
                'rejected', 'pushing', 'push_success', 'push_failed') DEFAULT 'queued',
    is_instant BOOLEAN DEFAULT FALSE,
    ocr_text TEXT,
    ocr_result JSON,
    extracted_data JSON,
    confidence_scores JSON,
    audit_reasons JSON,
    auditor_id VARCHAR(50),
    audited_at DATETIME,
    llm_token_count INT DEFAULT 0,
    llm_cost DECIMAL(10, 4) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    completed_at DATETIME,
    INDEX idx_file_hash (file_hash),
    INDEX idx_rule_id (rule_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (rule_id) REFERENCES rules(id),
    FOREIGN KEY (auditor_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```


#### webhooks表
```sql
CREATE TABLE webhooks (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    endpoint_url VARCHAR(500) NOT NULL,
    auth_type ENUM('none', 'basic', 'bearer', 'api_key') DEFAULT 'none',
    auth_config JSON,
    secret_key VARCHAR(255),
    request_template JSON NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### rule_webhooks表（规则与Webhook多对多关系）
```sql
CREATE TABLE rule_webhooks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    rule_id VARCHAR(50) NOT NULL,
    webhook_id VARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_rule_webhook (rule_id, webhook_id),
    FOREIGN KEY (rule_id) REFERENCES rules(id) ON DELETE CASCADE,
    FOREIGN KEY (webhook_id) REFERENCES webhooks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### push_logs表
```sql
CREATE TABLE push_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id VARCHAR(50) NOT NULL,
    webhook_id VARCHAR(50) NOT NULL,
    http_status INT,
    request_headers JSON,
    request_body TEXT,
    response_headers JSON,
    response_body TEXT,
    duration_ms INT,
    retry_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_webhook_id (webhook_id),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (webhook_id) REFERENCES webhooks(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### api_keys表
```sql
CREATE TABLE api_keys (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    key_id VARCHAR(50) UNIQUE NOT NULL,
    secret_hash VARCHAR(255) NOT NULL,
    expires_at DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_key_id (key_id),
    INDEX idx_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### audit_logs表
```sql
CREATE TABLE audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(50),
    action_type VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(50),
    changes JSON,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_action_type (action_type),
    INDEX idx_resource_type (resource_type),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### system_configs表
```sql
CREATE TABLE system_configs (
    key VARCHAR(100) PRIMARY KEY,
    value JSON NOT NULL,
    description VARCHAR(255),
    updated_by VARCHAR(50),
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Redis数据结构设计

#### 1. 规则配置缓存
```
Key: rule:config:{rule_id}:{version}
Type: String (JSON)
TTL: 3600s
Value: {完整的规则配置JSON}
```

#### 2. 用户Session
```
Key: session:{token}
Type: String (JSON)
TTL: 1800s
Value: {user_id, role, permissions}
```

#### 3. API限流计数器
```
Key: ratelimit:{api_key}:{endpoint}:{minute}
Type: String
TTL: 60s
Value: 请求次数
```

#### 4. 任务状态缓存
```
Key: task:status:{task_id}
Type: String
TTL: 300s
Value: 任务状态
```

#### 5. 仪表盘指标缓存
```
Key: metrics:dashboard:{date_range}
Type: String (JSON)
TTL: 300s
Value: {聚合后的指标数据}
```

### MinIO存储结构

```
Bucket: idp-files
├── 2025/
│   ├── 12/
│   │   ├── 14/
│   │   │   ├── T_20251214_0001/
│   │   │   │   ├── original.pdf
│   │   │   │   ├── page_1.png
│   │   │   │   ├── page_2.png
│   │   │   │   └── result.json
│   │   │   └── T_20251214_0002/
│   │   │       └── ...
```

## Error Handling

### 统一错误响应格式

```python
# app/core/exceptions.py
class APIException(Exception):
    def __init__(self, code: int, message: str, detail: any = None):
        self.code = code
        self.message = message
        self.detail = detail

class ValidationError(APIException):
    def __init__(self, message: str, detail: any = None):
        super().__init__(400, message, detail)

class AuthenticationError(APIException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(401, message)

class PermissionError(APIException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(403, message)

class NotFoundError(APIException):
    def __init__(self, resource: str):
        super().__init__(404, f"{resource} not found")

class RateLimitError(APIException):
    def __init__(self):
        super().__init__(429, "Too many requests")

# 全局异常处理器
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.code,
        content={
            "code": exc.code,
            "message": exc.message,
            "detail": exc.detail
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "Internal server error",
                "detail": str(exc),
                "traceback": traceback.format_exc()
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "Internal server error"
            }
        )
```

### OCR处理错误处理

```python
class OCRService:
    async def process_document(self, file_path: str, engine: str, page_strategy: dict):
        try:
            # OCR处理逻辑
            ...
        except TimeoutError:
            raise APIException(408, "OCR processing timeout")
        except FileNotFoundError:
            raise NotFoundError("File")
        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            raise APIException(500, "OCR processing failed", str(e))
```

### LLM服务熔断

```python
class LLMService:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=300,
            expected_exception=LLMServiceError
        )
    
    async def extract(self, text: str, prompt: str):
        try:
            return await self.circuit_breaker.call(
                self._call_llm_api, text, prompt
            )
        except CircuitBreakerOpen:
            logger.warning("LLM circuit breaker open, falling back to OCR only")
            return None  # 降级为纯OCR模式
    
    async def _call_llm_api(self, text: str, prompt: str):
        try:
            response = await asyncio.wait_for(
                self.agently_client.extract(text, prompt),
                timeout=60
            )
            return response
        except asyncio.TimeoutError:
            raise LLMServiceError("LLM request timeout")
        except Exception as e:
            raise LLMServiceError(f"LLM request failed: {str(e)}")
```

## Testing Strategy

### 1. 单元测试

**测试框架**：pytest + pytest-asyncio + pytest-cov

**测试覆盖**：
- Services层：OCR、提取、校验、推送等核心逻辑
- Utils层：哈希计算、签名生成、数据转换等工具函数
- Models层：数据模型验证、关系映射

**示例测试**：
```python
# tests/services/test_extraction_service.py
import pytest
from app.services.extraction_service import ExtractionService

@pytest.fixture
def extraction_service():
    return ExtractionService()

@pytest.fixture
def sample_ocr_result():
    return OCRResult(
        merged_text="发票号：NO.123456\n金额：100.50元",
        page_results=[...],
        page_count=1
    )

def test_extract_by_regex(extraction_service, sample_ocr_result):
    rule = {
        'type': 'regex',
        'pattern': r'发票号：([\w]+)'
    }
    
    result = extraction_service._extract_by_regex(
        sample_ocr_result.merged_text, 
        rule
    )
    
    assert result == "NO.123456"

@pytest.mark.asyncio
async def test_extract_fields(extraction_service, sample_ocr_result):
    schema = {
        'invoice_no': {'type': 'string'},
        'amount': {'type': 'decimal'}
    }
    
    extraction_rules = [
        {'field': 'invoice_no', 'type': 'regex', 'pattern': r'发票号：([\w]+)'},
        {'field': 'amount', 'type': 'regex', 'pattern': r'金额：([\d.]+)'}
    ]
    
    result = await extraction_service.extract_fields(
        sample_ocr_result,
        schema,
        extraction_rules
    )
    
    assert result['invoice_no']['value'] == "NO.123456"
    assert result['amount']['value'] == "100.50"
```

### 2. 集成测试

**测试范围**：
- API端点测试：使用TestClient测试所有API接口
- 数据库集成：使用测试数据库验证CRUD操作
- 消息队列集成：验证任务发布和消费

**示例测试**：
```python
# tests/api/test_upload.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_upload_file():
    with open("tests/fixtures/sample.pdf", "rb") as f:
        response = client.post(
            "/api/v1/ocr/upload",
            files={"file": ("sample.pdf", f, "application/pdf")},
            data={"rule_id": "RULE001"},
            headers={"Authorization": "Bearer test_token"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data["data"]
    assert data["data"]["status"] == "processing"

def test_upload_file_too_large():
    # 创建超过20MB的文件
    large_file = b"x" * (21 * 1024 * 1024)
    
    response = client.post(
        "/api/v1/ocr/upload",
        files={"file": ("large.pdf", large_file, "application/pdf")},
        data={"rule_id": "RULE001"},
        headers={"Authorization": "Bearer test_token"}
    )
    
    assert response.status_code == 400
    assert "文件大小超过20MB限制" in response.json()["message"]
```

### 3. 端到端测试

**测试场景**：
- 完整的文档处理流程：上传 → OCR → 提取 → 审核 → 推送
- 秒传机制验证
- 人工审核流程
- 死信队列处理

### 4. 性能测试

**测试工具**：Locust

**测试指标**：
- API响应时间：P50、P95、P99
- 并发处理能力：TPS、QPS
- 资源使用：CPU、内存、数据库连接数

**示例测试**：
```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class IDPUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # 登录获取token
        response = self.client.post("/api/v1/auth/login", json={
            "username": "test_user",
            "password": "test_pass"
        })
        self.token = response.json()["data"]["access_token"]
    
    @task(3)
    def upload_file(self):
        with open("sample.pdf", "rb") as f:
            self.client.post(
                "/api/v1/ocr/upload",
                files={"file": f},
                data={"rule_id": "RULE001"},
                headers={"Authorization": f"Bearer {self.token}"}
            )
    
    @task(10)
    def query_task(self):
        self.client.get(
            "/api/v1/tasks/T_20251214_0001",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(5)
    def list_tasks(self):
        self.client.get(
            "/api/v1/tasks",
            params={"page": 1, "page_size": 20},
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

## Security Considerations

### 1. 认证与授权

**JWT Token设计**：
```python
# Token payload
{
    "sub": "user_id",
    "role": "admin",
    "exp": 1702540800,
    "iat": 1702537200
}

# Token生成
def create_access_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# Token验证
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise AuthenticationError()
        return await get_user_by_id(user_id)
    except JWTError:
        raise AuthenticationError()
```

**权限装饰器**：
```python
def require_role(*allowed_roles):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if current_user.role not in allowed_roles:
                raise PermissionError()
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# 使用示例
@router.post("/rules")
@require_role("admin", "architect")
async def create_rule(rule_data: RuleCreate, current_user: User):
    ...
```

### 2. 数据加密

**敏感字段加密**：
```python
from cryptography.fernet import Fernet

class EncryptionService:
    def __init__(self):
        self.cipher = Fernet(settings.ENCRYPTION_KEY)
    
    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext.encode()).decode()

# 使用示例
encryption_service = EncryptionService()

# 存储时加密
webhook.secret_key = encryption_service.encrypt(secret_key)

# 使用时解密
decrypted_secret = encryption_service.decrypt(webhook.secret_key)
```

### 3. HMAC签名验证

```python
import hmac
import hashlib

def generate_signature(body: str, secret: str) -> str:
    """生成HMAC-SHA256签名"""
    return hmac.new(
        secret.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()

def verify_signature(body: str, signature: str, secret: str) -> bool:
    """验证签名"""
    expected_signature = generate_signature(body, secret)
    return hmac.compare_digest(expected_signature, signature)

# 推送时添加签名
async def push_to_webhook(task: Task, webhook: Webhook):
    body = render_template(webhook.request_template, task)
    signature = generate_signature(body, webhook.secret_key)
    
    headers = {
        "X-IDP-Signature": signature,
        "Content-Type": "application/json"
    }
    
    response = await http_client.post(
        webhook.endpoint_url,
        data=body,
        headers=headers
    )
```

### 4. SQL注入防护

使用SQLAlchemy ORM和参数化查询：
```python
# 安全的查询方式
tasks = db.query(Task).filter(
    Task.status == status,
    Task.created_at >= start_date
).all()

# 避免字符串拼接
# 错误示例：f"SELECT * FROM tasks WHERE status = '{status}'"
```

### 5. XSS防护

前端使用Vue的自动转义：
```vue
<!-- 安全：自动转义 -->
<div>{{ userInput }}</div>

<!-- 危险：不要使用v-html显示用户输入 -->
<!-- <div v-html="userInput"></div> -->
```

### 6. CSRF防护

```python
# 使用SameSite Cookie
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```


## Performance Optimization

### 1. 数据库优化

**索引策略**：
- 为高频查询字段添加索引（status, created_at, file_hash等）
- 使用复合索引优化多条件查询
- 定期分析慢查询日志并优化

**连接池配置**：
```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)
```

**查询优化**：
```python
# 使用select_related减少查询次数
tasks = db.query(Task).options(
    selectinload(Task.rule),
    selectinload(Task.push_logs)
).filter(Task.status == status).all()

# 分页查询
def paginate(query, page: int, page_size: int):
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {"items": items, "total": total}
```

### 2. 缓存策略

**规则配置缓存**：
```python
async def get_rule_config(rule_id: str, version: str) -> dict:
    cache_key = f"rule:config:{rule_id}:{version}"
    
    # 尝试从缓存获取
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 从数据库加载
    rule_version = db.query(RuleVersion).filter(
        RuleVersion.rule_id == rule_id,
        RuleVersion.version == version
    ).first()
    
    if not rule_version:
        raise NotFoundError("Rule version")
    
    # 写入缓存
    await redis.setex(cache_key, 3600, json.dumps(rule_version.config))
    
    return rule_version.config
```

**仪表盘数据缓存**：
```python
async def get_dashboard_metrics(date_range: str) -> dict:
    cache_key = f"metrics:dashboard:{date_range}"
    
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 计算指标
    metrics = await calculate_metrics(date_range)
    
    # 缓存5分钟
    await redis.setex(cache_key, 300, json.dumps(metrics))
    
    return metrics
```

### 3. 异步处理

**并发OCR处理**：
```python
async def process_multi_page_ocr(file_path: str, pages: List[int]) -> List[PageResult]:
    tasks = [
        asyncio.create_task(ocr_single_page(file_path, page))
        for page in pages
    ]
    return await asyncio.gather(*tasks)
```

**并发推送**：
```python
async def push_to_multiple_webhooks(task: Task, webhooks: List[Webhook]):
    tasks = [
        asyncio.create_task(push_to_webhook(task, webhook))
        for webhook in webhooks
    ]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

### 4. 文件处理优化

**流式上传**：
```python
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 流式读取，避免一次性加载到内存
    file_path = f"/tmp/{uuid.uuid4()}.pdf"
    
    async with aiofiles.open(file_path, 'wb') as f:
        while chunk := await file.read(8192):  # 8KB chunks
            await f.write(chunk)
    
    return {"file_path": file_path}
```

**懒加载PDF预览**：
```python
@router.get("/tasks/{task_id}/preview/{page}")
async def get_page_preview(task_id: str, page: int):
    """按需生成单页预览图"""
    task = await get_task(task_id)
    
    # 检查缓存
    cache_key = f"preview:{task_id}:{page}"
    cached_image = await redis.get(cache_key)
    if cached_image:
        return Response(content=cached_image, media_type="image/png")
    
    # 生成预览图
    image = await generate_page_image(task.file_path, page)
    
    # 缓存1小时
    await redis.setex(cache_key, 3600, image)
    
    return Response(content=image, media_type="image/png")
```

### 5. 前端性能优化

**代码分割**：
```javascript
// router/index.js
const routes = [
  {
    path: '/dashboard',
    component: () => import('@/views/Dashboard.vue')  // 懒加载
  },
  {
    path: '/rules',
    component: () => import('@/views/RuleList.vue')
  }
]
```

**虚拟滚动**：
```vue
<!-- 使用ant-design-vue的虚拟列表 -->
<a-list
  :data-source="tasks"
  :virtual="true"
  :height="600"
>
  <template #renderItem="{ item }">
    <TaskListItem :task="item" />
  </template>
</a-list>
```

**图片懒加载**：
```vue
<img 
  v-lazy="pageImageUrl" 
  :key="currentPage"
  class="pdf-preview"
/>
```

## Deployment Architecture

### Docker Compose配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # MySQL数据库
  mysql:
    image: mysql:8.0
    container_name: idp-mysql
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: idp_platform
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
      - ./backend/scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "3306:3306"
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis缓存
  redis:
    image: redis:7-alpine
    container_name: idp-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # RabbitMQ消息队列
  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: idp-rabbitmq
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    ports:
      - "5672:5672"
      - "15672:15672"
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # MinIO对象存储
  minio:
    image: minio/minio:latest
    container_name: idp-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 5

  # 后端API服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: idp-backend
    environment:
      DATABASE_URL: mysql+aiomysql://${MYSQL_USER}:${MYSQL_PASSWORD}@mysql:3306/idp_platform
      REDIS_URL: redis://redis:6379/0
      RABBITMQ_URL: amqp://${RABBITMQ_USER}:${RABBITMQ_PASSWORD}@rabbitmq:5672/
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ROOT_USER}
      MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD}
    volumes:
      - ./backend:/app
      - backend_temp:/tmp
    ports:
      - "8000:8000"
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
      minio:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # OCR Worker
  worker-ocr:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: idp-worker-ocr
    environment:
      DATABASE_URL: mysql+aiomysql://${MYSQL_USER}:${MYSQL_PASSWORD}@mysql:3306/idp_platform
      REDIS_URL: redis://redis:6379/0
      RABBITMQ_URL: amqp://${RABBITMQ_USER}:${RABBITMQ_PASSWORD}@rabbitmq:5672/
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ROOT_USER}
      MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD}
    volumes:
      - ./backend:/app
      - worker_temp:/tmp
    depends_on:
      - backend
    command: python -m app.tasks.ocr_worker
    deploy:
      replicas: 2

  # Push Worker
  worker-push:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: idp-worker-push
    environment:
      DATABASE_URL: mysql+aiomysql://${MYSQL_USER}:${MYSQL_PASSWORD}@mysql:3306/idp_platform
      REDIS_URL: redis://redis:6379/0
      RABBITMQ_URL: amqp://${RABBITMQ_USER}:${RABBITMQ_PASSWORD}@rabbitmq:5672/
    volumes:
      - ./backend:/app
    depends_on:
      - backend
    command: python -m app.tasks.push_worker

  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: idp-frontend
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    volumes:
      - ./frontend/nginx.conf:/etc/nginx/nginx.conf:ro

volumes:
  mysql_data:
  redis_data:
  rabbitmq_data:
  minio_data:
  backend_temp:
  worker_temp:
```

### 环境变量配置

```bash
# .env.example
# MySQL
MYSQL_ROOT_PASSWORD=root_password_here
MYSQL_USER=idp_user
MYSQL_PASSWORD=idp_password_here

# RabbitMQ
RABBITMQ_USER=idp_user
RABBITMQ_PASSWORD=rabbitmq_password_here

# MinIO
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=minio_password_here

# Backend
SECRET_KEY=your_secret_key_here_min_32_chars
ENCRYPTION_KEY=your_encryption_key_here_32_bytes
ALGORITHM=HS256

# LLM
AGENTLY_API_KEY=your_agently_api_key_here
LLM_TOKEN_PRICE=0.002

# OCR
OCR_TIMEOUT=300
OCR_MAX_PARALLEL=4
```

### Nginx配置

```nginx
# frontend/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 20M;
    
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss;
    
    # 前端静态资源
    server {
        listen 80;
        server_name _;
        root /usr/share/nginx/html;
        index index.html;
        
        # SPA路由支持
        location / {
            try_files $uri $uri/ /index.html;
        }
        
        # 静态资源缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # API代理
        location /api/ {
            proxy_pass http://backend:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
        
        # 健康检查
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

### Dockerfile配置

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建临时目录
RUN mkdir -p /tmp/uploads /tmp/processing

# 暴露端口
EXPOSE 8000

# 启动命令（由docker-compose覆盖）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine as build

WORKDIR /app

# 安装依赖
COPY package*.json ./
RUN npm ci

# 构建应用
COPY . .
RUN npm run build

# 生产镜像
FROM nginx:alpine

# 复制构建产物
COPY --from=build /app/dist /usr/share/nginx/html

# 复制Nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

## Monitoring and Logging

### 日志配置

```python
# app/core/logger.py
import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def setup_logging():
    logger = logging.getLogger("idp")
    logger.setLevel(logging.INFO)
    
    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # 文件输出（轮转）
    file_handler = RotatingFileHandler(
        "logs/idp.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()
```

### 指标监控

```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# 请求计数器
request_count = Counter(
    'idp_requests_total',
    'Total request count',
    ['method', 'endpoint', 'status']
)

# 请求延迟
request_duration = Histogram(
    'idp_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

# 任务处理时间
task_processing_duration = Histogram(
    'idp_task_processing_seconds',
    'Task processing duration in seconds',
    ['rule_id', 'status']
)

# 当前队列长度
queue_length = Gauge(
    'idp_queue_length',
    'Current queue length',
    ['queue_name']
)

# OCR Token消耗
llm_tokens_consumed = Counter(
    'idp_llm_tokens_total',
    'Total LLM tokens consumed',
    ['rule_id']
)
```

## Summary

本设计文档详细描述了智能文档处理中台的技术架构，包括：

1. **系统架构**：前后端分离，微服务化设计，支持水平扩展
2. **核心组件**：API层、Services层、Models层、Tasks层的详细设计
3. **数据模型**：完整的数据库表结构和Redis缓存设计
4. **错误处理**：统一的异常处理机制和熔断降级策略
5. **测试策略**：单元测试、集成测试、性能测试的完整方案
6. **安全设计**：认证授权、数据加密、签名验证等安全机制
7. **性能优化**：数据库优化、缓存策略、异步处理等优化方案
8. **部署架构**：Docker Compose编排、Nginx配置、监控日志方案

该设计方案完全满足PRD中定义的所有功能需求和非功能需求，为后续的实现提供了清晰的技术指导。
