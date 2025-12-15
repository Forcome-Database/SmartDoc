# Implementation Plan - Enterprise IDP Platform

## 项目初始化与基础设施

- [x] 1. 项目结构搭建与环境配置





  - 创建项目根目录结构（backend/、frontend/、.kiro/等）
  - 配置.gitignore文件，排除敏感文件和临时文件
  - 创建.env.example环境变量模板文件
  - 编写README.md项目说明文档
  - _Requirements: 67_

- [x] 1.1 后端项目初始化


  - 创建backend目录结构（app/api、app/core、app/models、app/services、app/tasks等）
  - 创建requirements.txt，添加FastAPI、SQLAlchemy、Redis、RabbitMQ等依赖
  - 创建main.py应用入口文件，配置FastAPI应用
  - 配置CORS中间件，允许前端跨域访问
  - _Requirements: 67_



- [x] 1.2 前端项目初始化





  - 使用Vite创建Vue 3项目
  - 安装Ant Design Vue 4.2、Pinia、Tailwind CSS、Axios等依赖
  - 配置vite.config.js，设置代理和构建选项
  - 配置tailwind.config.js，自定义主题颜色
  - 创建src目录结构（api/、components/、views/、router/、stores/等）


  - _Requirements: 63_

- [x] 1.3 Docker环境配置






  - 编写docker-compose.yml，定义MySQL、Redis、RabbitMQ、MinIO、backend、frontend服务
  - 编写docker-compose.dev.yml开发环境覆盖配置
  - 创建backend/Dockerfile，配置Python运行环境
  - 创建frontend/Dockerfile，配置Nginx静态服务器
  - 编写frontend/nginx.conf，配置反向代理和静态资源服务
  - _Requirements: 67_

## 核心配置与数据库

- [x] 2. 核心配置模块实现





- [x] 2.1 配置管理（app/core/config.py）


  - 创建Settings类，使用Pydantic BaseSettings加载环境变量
  - 配置数据库连接URL、Redis URL、RabbitMQ URL、MinIO配置
  - 配置安全相关参数（SECRET_KEY、ALGORITHM、TOKEN过期时间）
  - 配置OCR和LLM相关参数（超时时间、并行数、Token单价）
  - _Requirements: 53_

- [x] 2.2 数据库连接池（app/core/database.py）


  - 使用SQLAlchemy创建异步数据库引擎
  - 配置连接池参数（pool_size=20、max_overflow=10、pool_timeout=30）
  - 创建SessionLocal工厂函数
  - 实现get_db依赖注入函数，提供数据库会话
  - _Requirements: 65_



- [x] 2.3 Redis连接（app/core/cache.py）



  - 创建Redis客户端连接
  - 实现缓存操作封装函数（get、set、delete、exists）
  - 实现限流计数器功能


  - _Requirements: 66_

- [x] 2.4 RabbitMQ连接（app/core/mq.py）
  - 创建RabbitMQ连接和Channel
  - 声明任务队列（ocr_tasks、push_tasks、push_dlq）


  - 实现消息发布函数（publish_task）
  - 配置消息持久化和确认机制
  - _Requirements: 35_

- [x] 2.5 MinIO存储客户端（app/core/storage.py）
  - 创建MinIO客户端连接
  - 实现文件上传函数（upload_file）
  - 实现文件下载函数（download_file）
  - 实现预签名URL生成函数（generate_presigned_url）
  - 实现文件删除函数（delete_file）
  - _Requirements: 23, 36_

- [x] 3. 数据库模型定义





- [x] 3.1 用户模型（app/models/user.py）


  - 创建User模型，定义id、username、email、password_hash、role、is_active等字段
  - 定义RoleEnum枚举（admin、architect、auditor、visitor）
  - 添加索引（username、email）
  - _Requirements: 5, 49_

- [x] 3.2 规则模型（app/models/rule.py）


  - 创建Rule模型，定义id、name、code、document_type、current_version等字段
  - 创建RuleVersion模型，定义rule_id、version、status、config等字段
  - 定义RuleStatus枚举（draft、published、archived）
  - 建立Rule和RuleVersion的一对多关系
  - 添加索引（code、document_type、status）
  - _Requirements: 6, 27_

- [x] 3.3 任务模型（app/models/task.py）


  - 创建Task模型，定义id、file_name、file_path、file_hash、page_count等字段
  - 定义status、is_instant、ocr_text、ocr_result、extracted_data等字段
  - 定义confidence_scores、audit_reasons、llm_token_count等字段
  - 定义TaskStatus枚举（queued、processing、pending_audit、completed等）
  - 建立Task和Rule的多对一关系
  - 添加索引（file_hash、rule_id、status、created_at）
  - _Requirements: 13, 14, 15, 20, 55_

- [x] 3.4 Webhook模型（app/models/webhook.py）


  - 创建Webhook模型，定义id、name、endpoint_url、auth_type、auth_config等字段
  - 创建RuleWebhook关联表，建立Rule和Webhook的多对多关系
  - 定义AuthType枚举（none、basic、bearer、api_key）
  - 添加索引（is_active）
  - _Requirements: 3, 32_

- [x] 3.5 推送日志模型（app/models/push_log.py）


  - 创建PushLog模型，定义task_id、webhook_id、http_status等字段
  - 定义request_headers、request_body、response_headers、response_body等字段
  - 定义duration_ms、retry_count等字段
  - 建立PushLog和Task、Webhook的多对一关系
  - 添加索引（task_id、webhook_id、created_at）
  - _Requirements: 18, 19_

- [x] 3.6 API Key模型（app/models/api_key.py）


  - 创建APIKey模型，定义id、user_id、key_id、secret_hash等字段
  - 定义expires_at、is_active、last_used_at等字段
  - 建立APIKey和User的多对一关系
  - 添加索引（key_id、user_id）
  - _Requirements: 50_

- [x] 3.7 审计日志模型（app/models/audit_log.py）


  - 创建AuditLog模型，定义user_id、action_type、resource_type等字段
  - 定义resource_id、changes、ip_address、user_agent等字段
  - 添加索引（user_id、action_type、resource_type、created_at）
  - _Requirements: 51_

- [x] 3.8 系统配置模型（app/models/system_config.py）


  - 创建SystemConfig模型，定义key、value、description等字段
  - 定义updated_by、updated_at等字段
  - _Requirements: 53_

- [x] 4. 数据库迁移脚本




- [x] 4.1 配置Alembic



  - 初始化Alembic，创建alembic目录和配置文件
  - 配置alembic.ini，设置数据库连接URL
  - 修改env.py，导入所有模型并配置target_metadata
  - _Requirements: 68_


- [x] 4.2 生成初始迁移脚本

  - 运行alembic revision --autogenerate生成初始迁移脚本
  - 检查生成的迁移脚本，确保所有表和索引正确创建
  - 编写初始数据插入脚本（创建默认管理员账号）
  - _Requirements: 68_


## 安全与认证

- [x] 5. 安全模块实现






- [x] 5.1 密码加密（app/core/security.py）


  - 实现密码哈希函数（使用bcrypt）
  - 实现密码验证函数
  - _Requirements: 49_


- [x] 5.2 JWT Token管理
  - 实现JWT Token生成函数（create_access_token）
  - 实现JWT Token验证函数（verify_token）
  - 实现Token解码函数，提取用户信息

  - _Requirements: 21_

- [x] 5.3 API Key管理
  - 实现API Key生成函数（生成key_id和secret）
  - 实现API Key哈希存储函数

  - 实现API Key验证函数
  - _Requirements: 50_

- [x] 5.4 数据加密服务
  - 实现AES-256加密函数（encrypt）

  - 实现AES-256解密函数（decrypt）
  - 用于加密敏感字段（Secret Key、API Key等）
  - _Requirements: 3, 21_

- [x] 5.5 HMAC签名服务
  - 实现HMAC-SHA256签名生成函数（generate_signature）
  - 实现签名验证函数（verify_signature）
  - 用于Webhook推送签名
  - _Requirements: 3, 18_

- [x] 6. 认证授权API





- [x] 6.1 用户认证端点（app/api/v1/endpoints/auth.py）


  - 实现POST /api/v1/auth/login登录接口
  - 实现POST /api/v1/auth/logout登出接口
  - 实现GET /api/v1/auth/me获取当前用户信息接口
  - 实现POST /api/v1/auth/refresh刷新Token接口
  - _Requirements: 21_

- [x] 6.2 权限依赖注入


  - 实现get_current_user依赖函数，从Token中提取用户
  - 实现require_role装饰器，检查用户角色权限
  - 实现get_current_active_user依赖函数，验证用户是否激活
  - _Requirements: 5_



- [x] 6.3 API限流中间件（app/core/middleware.py）
  - 实现限流中间件，使用Redis计数器
  - 配置不同端点的限流策略（上传100次/分钟，查询1000次/分钟）
  - 返回429错误和限流信息头（X-RateLimit-*）

  - _Requirements: 66_

- [x] 6.4 请求日志中间件
  - 实现请求日志中间件，记录所有API请求
  - 记录请求方法、路径、参数、响应状态、耗时
  - 记录用户IP、User-Agent等信息
  - _Requirements: 24_

## 核心业务服务

- [x] 7. 文件处理服务




- [x] 7.1 文件哈希服务（app/services/hash_service.py）


  - 实现文件SHA256哈希计算函数（calculate_file_hash）
  - 实现Task Key生成函数（generate_task_key = hash + rule_id + version）
  - 实现去重判断函数（check_duplicate），查询数据库是否存在相同Task Key
  - _Requirements: 13_

- [x] 7.2 文件上传服务（app/services/file_service.py）


  - 实现文件上传到MinIO函数（upload_to_storage）
  - 生成文件存储路径（{bucket}/{year}/{month}/{day}/{task_id}/{filename}）
  - 实现文件下载函数（download_from_storage）
  - 实现文件删除函数（delete_from_storage）
  - _Requirements: 23, 36_

- [x] 7.3 PDF处理服务


  - 实现PDF页数获取函数（get_page_count）
  - 实现PDF转图片函数（convert_pdf_to_images），使用pdf2image
  - 配置DPI为300，输出格式为PNG
  - 实现临时文件清理函数
  - _Requirements: 54_

- [x] 8. OCR处理服务





- [x] 8.1 OCR引擎封装（app/services/ocr_service.py）


  - 初始化PaddleOCR引擎（use_angle_cls=True, lang='ch'）
  - 初始化Tesseract引擎配置
  - 实现Azure Form Recognizer客户端初始化
  - _Requirements: 7, 39_

- [x] 8.2 单页OCR处理

  - 实现单页OCR函数（_ocr_single_page）
  - 根据engine参数调用不同的OCR引擎
  - 返回PageOCRResult（text、boxes、confidence）
  - _Requirements: 14_

- [x] 8.3 多页并行OCR处理

  - 实现并行OCR函数（_parallel_ocr），使用asyncio.gather
  - 配置最大并行数（默认4）
  - 实现顺序OCR函数（_sequential_ocr）用于少量页面
  - _Requirements: 40_

- [x] 8.4 页面策略解析

  - 实现页面策略解析函数（_parse_page_strategy）
  - 支持单页模式（仅第一页）
  - 支持多页合并模式（所有页面）
  - 支持指定页码模式（解析"1-3"、"Last Page"等表达式）
  - _Requirements: 7_

- [x] 8.5 文本合并

  - 实现OCR文本合并函数（_merge_ocr_text）
  - 在页面之间插入配置的分隔符（默认\n）
  - 返回Global_Context_String
  - _Requirements: 10, 28_

- [x] 8.6 备用引擎降级

  - 实现备用引擎重试逻辑
  - 当主引擎返回空结果时，自动调用备用引擎
  - 记录使用备用引擎的日志
  - _Requirements: 46_

- [x] 9. 数据提取服务



- [x] 9.1 提取引擎核心（app/services/extraction_service.py）



  - 实现字段提取主函数（extract_fields）
  - 遍历schema中的所有字段，根据extraction_rules执行提取
  - 返回提取结果，包含value、confidence、source_page
  - _Requirements: 10_



- [x] 9.2 正则提取
  - 实现正则提取函数（_extract_by_regex）
  - 在Global_Context_String中执行正则匹配
  - 支持提取第一个匹配或所有匹配
  - 支持捕获组功能
  - _Requirements: 10, 56_

- [x] 9.3 锚点定位提取

  - 实现锚点提取函数（_extract_by_anchor）
  - 查找锚点关键词位置
  - 根据相对位置（右侧、下方、右下方）提取目标文本
  - 支持配置提取范围（最大字符数或坐标偏移）
  - _Requirements: 42_

- [x] 9.4 表格提取


  - 实现表格检测函数（_detect_tables）
  - 实现跨页表格合并函数（_merge_cross_page_tables）
  - 根据表头逻辑判断表格是否延续
  - 去除重复的表头行
  - _Requirements: 10, 43_



- [x] 9.5 置信度计算

  - 实现置信度计算函数（_calculate_confidence）
  - 根据OCR置信度、匹配度等因素综合计算
  - 返回0-100的置信度分数
  - _Requirements: 9, 41_


- [x] 10. LLM集成服务


- [x] 10.1 LLM客户端初始化（app/services/llm_service.py）


  - 初始化Agently4客户端
  - 配置API Key和超时时间
  - _Requirements: 10_



- [x] 10.2 LLM提取函数
  - 实现LLM提取函数（extract_by_llm）
  - 根据Context Scope提取上下文（全文/指定区域/前N页）
  - 构建Prompt，包含自定义提示词和上下文
  - 调用LLM API，解析返回结果
  - 记录Token消耗
  - _Requirements: 10, 57_

- [x] 10.3 熔断器实现
  - 实现CircuitBreaker类（failure_threshold=5, recovery_timeout=300）
  - 监控LLM服务响应时间和错误率
  - 当超时或5xx错误时触发熔断
  - 熔断期间返回None，降级为纯OCR模式
  - 每5分钟尝试恢复
  - _Requirements: 12, 48_

- [x] 10.4 一致性校验
  - 实现OCR和LLM结果对比函数（compare_results）
  - 使用编辑距离算法计算相似度
  - 当相似度低于阈值时标记为不一致

  - _Requirements: 47_

- [x] 10.5 Token消耗跟踪
  - 实现Token计数函数（count_tokens）
  - 记录每次LLM调用的输入和输出Token数
  - 根据Token单价计算费用
  - 保存到任务记录中
  - _Requirements: 38_

- [x] 11. 数据清洗与校验服务






- [x] 11.1 数据清洗（app/services/validation_service.py）


  - 实现清洗管道函数（clean_data）
  - 实现正则替换操作（regex_replace）
  - 实现去空格操作（trim）
  - 实现日期格式化操作（format_date），支持多种日期格式识别
  - _Requirements: 11, 44_


- [x] 11.2 数据类型转换
  - 实现类型转换函数（convert_type）
  - 支持String、Int、Date、Decimal、Boolean类型转换
  - 处理转换失败情况，记录警告
  - _Requirements: 58_


- [x] 11.3 数据校验
  - 实现校验函数（validate）
  - 实现必填校验（validate_required）
  - 实现正则格式校验（validate_pattern），支持Email、Phone等
  - 实现数值范围校验（validate_range）

  - _Requirements: 11, 34_

- [x] 11.4 自定义脚本校验
  - 实现JavaScript表达式执行函数（execute_js_expression）
  - 提供字段值访问方式（fields.amount等）
  - 限制执行时间不超过100毫秒
  - 返回校验结果和错误信息
  - _Requirements: 45_

- [x] 12. Webhook推送服务







- [x] 12.1 推送核心（app/services/push_service.py）


  - 实现推送函数（push_to_webhook）
  - 渲染请求体模版，替换变量（{{task_id}}、{{result_json}}等）
  - 生成HMAC签名，添加到X-IDP-Signature头
  - 根据auth_type添加认证信息
  - 发送HTTP POST请求
  - _Requirements: 18, 61_


- [x] 12.2 推送日志记录


  - 实现推送日志保存函数（save_push_log）
  - 记录HTTP状态码、请求头、请求体、响应头、响应体、耗时
  - 记录重试次数
  - _Requirements: 18_


- [x] 12.3 指数退避重试


  - 实现重试逻辑（retry_push）
  - 计算延迟时间（10s、30s、90s）
  - 发布延迟消息到队列
  - 最多重试3次

  - _Requirements: 31_

- [x] 12.4 死信队列处理


  - 实现移入死信队列函数（move_to_dlq）
  - 更新任务状态为Push Failed
  - 记录失败原因
  - _Requirements: 19_

## 异步任务Worker

- [x] 13. OCR处理Worker




- [x] 13.1 Worker主程序（app/tasks/ocr_worker.py）



  - 创建OCRWorker类
  - 初始化RabbitMQ连接和Channel
  - 声明ocr_tasks队列
  - 实现start方法，开始消费消息
  - _Requirements: 14_

- [x] 13.2 任务处理流程


  - 实现process_task方法
  - 更新任务状态为Processing
  - 下载文件从MinIO
  - 加载规则配置（从Redis缓存或数据库）
  - 执行OCR处理
  - 执行数据提取
  - 执行LLM增强（如果配置）
  - 执行数据清洗
  - 执行数据校验
  - _Requirements: 14, 15_



- [x] 13.3 质检与状态判断
  - 判断是否需要人工审核（校验失败或置信度低）
  - 更新任务状态为Pending Audit或Completed
  - 保存OCR结果和提取结果到数据库
  - 触发推送任务（如果Completed）
  - 确认消息



  - _Requirements: 15_

- [x] 13.4 错误处理
  - 捕获异常，记录错误日志
  - 更新任务状态为Failed
  - Nack消息，不重新入队
  - _Requirements: 69_

- [x] 14. 推送Worker




- [x] 14.1 Worker主程序（app/tasks/push_worker.py）


  - 创建PushWorker类
  - 初始化RabbitMQ连接
  - 声明push_tasks和push_dlq队列
  - 实现start方法
  - _Requirements: 18_

- [x] 14.2 推送处理流程

  - 实现process_push方法
  - 加载任务和Webhook配置
  - 并行推送到所有关联的Webhook目标
  - 检查推送结果
  - 处理部分失败情况
  - _Requirements: 18, 32_

- [x] 14.3 重试与死信处理


  - 实现重试逻辑，使用指数退避
  - 3次重试后移入死信队列
  - 更新任务状态
  - _Requirements: 31, 19_

- [x] 15. 定时清理任务




- [x] 15.1 清理Worker（app/tasks/cleanup_worker.py）


  - 创建CleanupWorker类
  - 使用APScheduler配置定时任务（每日02:00）
  - _Requirements: 4, 62_

- [x] 15.2 文件清理逻辑



  - 查询超过留存期的文件记录
  - 仅删除Completed或Rejected状态的任务文件
  - 从MinIO删除文件
  - 更新数据库记录
  - 记录清理日志（删除数量、释放空间）
  - _Requirements: 4, 62_

## API端点实现

- [x] 16. 文件上传API



- [x] 16.1 上传端点（app/api/v1/endpoints/upload.py）


  - 实现POST /api/v1/ocr/upload接口
  - 验证文件大小（最大20MB）
  - 验证文件页数（最大50页）
  - 验证rule_id参数
  - _Requirements: 13_

- [x] 16.2 哈希去重逻辑

  - 计算文件哈希
  - 生成Task Key
  - 查询数据库判断是否命中
  - 如果命中，复制历史结果，标记秒传，直接返回
  - 如果未命中，上传文件到MinIO，创建任务记录，发布到队列
  - _Requirements: 13_

- [x] 16.3 响应处理


  - 返回task_id、is_instant、status、estimated_wait_seconds
  - 根据页数计算预估等待时间
  - 考虑当前队列长度
  - _Requirements: 13, 29_

- [x] 17. 任务查询API



- [x] 17.1 任务列表端点（app/api/v1/endpoints/tasks.py）


  - 实现GET /api/v1/tasks接口
  - 支持分页（page、page_size）
  - 支持筛选（status、rule_id、date_range）
  - 支持搜索（task_id、file_name）
  - 支持排序
  - _Requirements: 20_

- [x] 17.2 任务详情端点

  - 实现GET /api/v1/tasks/{task_id}接口
  - 返回完整任务信息
  - 包含OCR结果、提取结果、置信度、审核原因、推送日志等
  - _Requirements: 20_

- [x] 17.3 任务状态更新端点

  - 实现PATCH /api/v1/tasks/{task_id}/status接口
  - 支持审核员修正数据并提交
  - 更新任务状态为Completed或Rejected
  - 触发推送（如果Completed）
  - 记录审核日志
  - _Requirements: 17_

- [x] 17.4 任务导出端点



  - 实现GET /api/v1/tasks/export接口
  - 支持导出为CSV或Excel格式
  - 支持筛选条件
  - 异步导出（数据量>10000时）
  - _Requirements: 26_


- [x] 18. 规则管理API






- [x] 18.1 规则列表端点（app/api/v1/endpoints/rules.py）
  - 实现GET /api/v1/rules接口
  - 返回规则列表，包含name、code、document_type、current_version
  - 支持按document_type分组
  - 支持筛选和搜索
  - _Requirements: 6, 27_


- [x] 18.2 规则创建端点
  - 实现POST /api/v1/rules接口
  - 创建规则记录和初始草稿版本
  - 生成唯一的规则编码
  - 仅Admin和Architect角色可访问

  - _Requirements: 6_

- [x] 18.3 规则详情端点
  - 实现GET /api/v1/rules/{rule_id}接口

  - 返回规则基本信息和当前发布版本配置
  - _Requirements: 6_

- [x] 18.4 规则版本列表端点
  - 实现GET /api/v1/rules/{rule_id}/versions接口

  - 返回所有版本历史（草稿、已发布、归档）
  - 按版本号降序排列
  - _Requirements: 6_

- [x] 18.5 规则配置更新端点

  - 实现PUT /api/v1/rules/{rule_id}/versions/{version}接口
  - 更新草稿版本的配置内容
  - 验证配置JSON格式
  - _Requirements: 7, 8, 9, 10, 11, 12_

- [x] 18.6 规则发布端点
  - 实现POST /api/v1/rules/{rule_id}/publish接口

  - 将草稿版本发布为新版本（V1.0、V1.1等）
  - 将当前发布版本归档
  - 更新规则的current_version
  - 清除Redis缓存
  - _Requirements: 6_


- [x] 18.7 规则回滚端点
  - 实现POST /api/v1/rules/{rule_id}/rollback接口
  - 将指定历史版本恢复为已发布状态
  - 将当前版本归档
  - 清除Redis缓存
  - _Requirements: 6_

- [x] 18.8 沙箱测试端点
  - 实现POST /api/v1/rules/{rule_id}/sandbox接口
  - 接收上传的测试文件
  - 使用当前草稿配置执行完整处理流程
  - 返回提取结果、OCR标注、合并文本预览
  - 不影响生产数据
  - _Requirements: 8_

- [x] 19. Webhook配置API






- [x] 19.1 Webhook列表端点（app/api/v1/endpoints/webhook.py）


  - 实现GET /api/v1/webhooks接口
  - 返回所有Webhook配置
  - 仅Admin角色可访问
  - _Requirements: 3_

- [x] 19.2 Webhook创建端点

  - 实现POST /api/v1/webhooks接口
  - 创建Webhook配置
  - 加密存储secret_key
  - _Requirements: 3_

- [x] 19.3 Webhook更新端点

  - 实现PUT /api/v1/webhooks/{webhook_id}接口
  - 更新Webhook配置
  - 重新加密secret_key（如果修改）
  - _Requirements: 3_

- [x] 19.4 Webhook删除端点

  - 实现DELETE /api/v1/webhooks/{webhook_id}接口
  - 删除Webhook配置
  - 检查是否有规则关联，提示警告
  - _Requirements: 3_

- [x] 19.5 连通性测试端点

  - 实现POST /api/v1/webhooks/{webhook_id}/test接口
  - 使用Mock数据发送测试请求
  - 返回响应状态码、响应头、响应体
  - 5秒超时
  - _Requirements: 3_

- [x] 19.6 规则关联Webhook端点

  - 实现POST /api/v1/rules/{rule_id}/webhooks接口
  - 关联规则和Webhook（多对多）
  - 实现DELETE /api/v1/rules/{rule_id}/webhooks/{webhook_id}解除关联
  - _Requirements: 32_

- [x] 20. 审核工作台API



- [x] 20.1 待审核任务列表端点（app/api/v1/endpoints/audit.py）


  - 实现GET /api/v1/audit/tasks接口
  - 返回状态为Pending Audit的任务列表
  - 支持分页和筛选
  - 仅Auditor和Admin角色可访问
  - _Requirements: 16_

- [x] 20.2 审核任务详情端点


  - 实现GET /api/v1/audit/tasks/{task_id}接口
  - 返回任务完整信息
  - 返回PDF文件预签名URL
  - 返回OCR结果（含坐标信息）
  - 返回提取结果和置信度
  - _Requirements: 16, 33, 41_

- [x] 20.3 PDF页面预览端点


  - 实现GET /api/v1/audit/tasks/{task_id}/preview/{page}接口
  - 按需生成单页预览图
  - 使用Redis缓存（1小时）
  - 支持懒加载
  - _Requirements: 16_

- [x] 20.4 草稿保存端点


  - 实现POST /api/v1/audit/tasks/{task_id}/draft接口
  - 保存用户修改的草稿数据
  - 使用Redis存储（TTL 24小时）
  - _Requirements: 30_

- [x] 20.5 审核提交端点




  - 实现POST /api/v1/audit/tasks/{task_id}/submit接口
  - 接收修正后的数据和审核决策（通过/驳回）
  - 更新任务状态和extracted_data
  - 记录审核人和审核时间
  - 触发推送（如果通过）
  - 清除草稿
  - _Requirements: 17_

- [x] 21. 仪表盘API




- [x] 21.1 核心指标端点（app/api/v1/endpoints/dashboard.py）


  - 实现GET /api/v1/dashboard/metrics接口
  - 支持时间范围筛选（today、7days、30days）
  - 返回8个核心指标（总接单量、累计页数、处理中、待审核、推送异常、直通率、算力节省、LLM消耗）
  - 使用Redis缓存（5分钟）
  - _Requirements: 1, 37, 38_

- [x] 21.2 任务吞吐趋势端点


  - 实现GET /api/v1/dashboard/throughput接口
  - 返回每日任务数量统计（成功、待审核、失败、驳回）
  - 按日期分组聚合
  - _Requirements: 2_

- [x] 21.3 规则效能Top10端点


  - 实现GET /api/v1/dashboard/rule-performance接口
  - 返回任务量Top10规则
  - 包含规则名称、任务量、平均耗时、人工干预率
  - _Requirements: 2, 59_

- [x] 21.4 异常分布端点


  - 实现GET /api/v1/dashboard/exceptions接口
  - 统计各类异常的数量和占比
  - 返回饼图数据（OCR识别空、必填校验失败、LLM不一致、下游接口错误等）
  - _Requirements: 2, 60_

- [x] 22. 用户管理API








- [x] 22.1 用户列表端点（app/api/v1/endpoints/users.py）
  - 实现GET /api/v1/users接口
  - 返回用户列表
  - 支持按用户名、邮箱、角色筛选
  - 仅Admin角色可访问
  - _Requirements: 49_


- [x] 22.2 用户创建端点
  - 实现POST /api/v1/users接口
  - 创建新用户
  - 验证用户名和邮箱唯一性
  - 哈希存储密码

  - _Requirements: 49_

- [x] 22.3 用户更新端点
  - 实现PUT /api/v1/users/{user_id}接口
  - 更新用户信息（用户名、邮箱、角色）

  - 支持修改密码（需验证旧密码）
  - _Requirements: 49_

- [x] 22.4 用户禁用/启用端点

  - 实现PATCH /api/v1/users/{user_id}/status接口
  - 切换用户is_active状态
  - _Requirements: 49_

- [x] 22.5 用户删除端点
  - 实现DELETE /api/v1/users/{user_id}接口
  - 软删除用户（设置is_active=False）
  - 不允许删除最后一个Admin用户
  - _Requirements: 49_

- [x] 23. API Key管理API





- [x] 23.1 API Key列表端点（app/api/v1/endpoints/api_keys.py）

  - 实现GET /api/v1/api-keys接口
  - 返回当前用户的API Key列表
  - 仅显示部分secret（前8位+***）
  - _Requirements: 50_


- [x] 23.2 API Key生成端点
  - 实现POST /api/v1/api-keys接口
  - 生成新的API Key（key_id和secret）
  - 哈希存储secret
  - 返回完整secret（仅此一次）
  - 支持配置有效期
  - _Requirements: 50_


- [x] 23.3 API Key撤销端点
  - 实现DELETE /api/v1/api-keys/{key_id}接口
  - 设置is_active=False
  - _Requirements: 50_

- [x] 24. 系统配置API







- [x] 24.1 系统配置查询端点（app/api/v1/endpoints/system.py）


  - 实现GET /api/v1/system/config接口
  - 返回所有系统配置
  - 仅Admin角色可访问
  - _Requirements: 53_

- [x] 24.2 系统配置更新端点


  - 实现PUT /api/v1/system/config/{key}接口
  - 更新指定配置项
  - 记录审计日志
  - 立即生效（更新Redis缓存）
  - _Requirements: 53_

- [x] 24.3 数据生命周期配置端点


  - 实现GET /api/v1/system/retention接口
  - 返回文件留存期和数据留存期配置
  - 实现PUT /api/v1/system/retention接口更新配置
  - _Requirements: 4_

- [x] 25. 审计日志API




- [x] 25.1 审计日志查询端点（app/api/v1/endpoints/audit_logs.py）

  - 实现GET /api/v1/audit-logs接口
  - 支持按时间范围、用户、操作类型筛选
  - 支持分页
  - 仅Admin角色可访问
  - _Requirements: 51_


- [x] 25.2 审计日志导出端点
  - 实现GET /api/v1/audit-logs/export接口
  - 导出为CSV格式
  - 支持筛选条件
  - _Requirements: 51_


## 前端实现

- [x] 26. 前端路由与布局





- [x] 26.1 路由配置（src/router/index.js）


  - 配置Vue Router
  - 定义路由：/login、/dashboard、/rules、/tasks、/audit、/webhooks、/users、/settings
  - 配置路由守卫，验证登录状态
  - 配置懒加载
  - _Requirements: 63_

- [x] 26.2 主布局组件（src/components/Layout/MainLayout.vue）


  - 创建主布局，包含顶部导航、侧边菜单、内容区域
  - 使用Ant Design Vue的Layout组件
  - 实现响应式设计（桌面/平板/移动）
  - _Requirements: 63_

- [x] 26.3 顶部导航栏（src/components/Layout/Header.vue）


  - 显示系统Logo和名称
  - 显示当前用户信息
  - 实现用户下拉菜单（个人信息、登出）
  - _Requirements: 63_

- [x] 26.4 侧边菜单（src/components/Layout/Sidebar.vue）


  - 根据用户角色显示菜单项
  - 实现菜单折叠/展开
  - 高亮当前激活菜单
  - _Requirements: 5_

- [x] 27. 认证页面




- [x] 27.1 登录页面（src/views/Login.vue）


  - 创建登录表单（用户名、密码）
  - 实现表单验证
  - 调用登录API，保存Token到localStorage
  - 登录成功后跳转到仪表盘
  - _Requirements: 21_

- [x] 27.2 认证Store（src/stores/authStore.js）


  - 管理用户登录状态
  - 保存用户信息和Token
  - 实现登出功能
  - _Requirements: 21_

- [x] 28. 仪表盘页面




- [x] 28.1 仪表盘主页面（src/views/Dashboard.vue）


  - 创建仪表盘布局
  - 显示时间范围筛选器（今日、近7天、近30天）
  - 调用仪表盘API获取数据
  - _Requirements: 1, 2_

- [x] 28.2 指标卡片组件（src/components/Dashboard/MetricCard.vue）


  - 创建指标卡片组件
  - 显示指标名称、数值、趋势图标
  - 支持红色预警样式（推送异常）
  - _Requirements: 1_

- [x] 28.3 任务吞吐趋势图（src/components/Dashboard/ThroughputChart.vue）


  - 使用ECharts或Chart.js创建堆叠柱状图
  - 显示每日成功、待审核、失败、驳回数量
  - 支持点击跳转到任务列表
  - _Requirements: 2_

- [x] 28.4 规则效能列表（src/components/Dashboard/RulePerformance.vue）


  - 创建Top10规则列表
  - 显示规则名称、任务量、平均耗时、人工干预率
  - 使用颜色标识人工干预率等级
  - _Requirements: 2, 59_

- [x] 28.5 异常分布饼图（src/components/Dashboard/ExceptionChart.vue）


  - 使用ECharts创建饼图
  - 显示各类异常的占比
  - 支持点击查看详情
  - _Requirements: 2, 60_

- [x] 29. 规则管理页面




- [x] 29.1 规则列表页面（src/views/RuleList.vue）


  - 创建规则列表表格
  - 显示规则名称、编码、文档类型、当前版本、状态
  - 实现搜索和筛选
  - 实现新建规则按钮
  - _Requirements: 6, 27_

- [x] 29.2 规则编辑器页面（src/views/RuleEditor.vue）


  - 创建规则编辑器主页面
  - 实现多标签页（基础配置、Schema定义、提取策略、清洗校验、增强风控）
  - 显示版本选择器和操作按钮（保存、发布、回滚、沙箱测试）
  - _Requirements: 7, 8, 9, 10, 11, 12_

- [x] 29.3 基础配置标签页（src/components/RuleEditor/BasicConfig.vue）


  - 创建基础配置表单
  - 配置OCR引擎、语言、页面处理策略、页面分隔符
  - _Requirements: 7, 28_

- [x] 29.4 Schema编辑器（src/components/RuleEditor/SchemaEditor.vue）


  - 创建树形Schema编辑器
  - 支持添加Object、Array、Table、Field节点
  - 配置字段属性（Key、Label、Type、默认值、置信度阈值、必填）
  - 支持拖拽排序
  - _Requirements: 9, 34_

- [x] 29.5 提取策略配置（src/components/RuleEditor/ExtractionConfig.vue）


  - 为每个字段配置提取策略
  - 支持正则、锚点、表格、LLM四种提取方式
  - 配置正则表达式、锚点关键词、LLM Prompt等
  - _Requirements: 10, 42, 56, 57_

- [x] 29.6 清洗校验配置（src/components/RuleEditor/ValidationConfig.vue）


  - 配置清洗管道（正则替换、去空格、日期格式化）
  - 配置校验规则（必填、正则格式、数值范围、自定义脚本）
  - _Requirements: 11, 44, 45_

- [x] 29.7 增强风控配置（src/components/RuleEditor/EnhancementConfig.vue）


  - 配置自动增强（备用引擎、LLM补全）
  - 配置一致性校验（OCR vs LLM）
  - 配置成本熔断（Token Limit、服务降级）
  - _Requirements: 12, 46, 47, 48_

- [x] 29.8 沙箱测试面板（src/components/RuleEditor/SandboxPanel.vue）


  - 创建沙箱测试侧边栏
  - 实现文件上传
  - 显示测试结果（JSON、OCR标注、合并文本预览）
  - 支持多页PDF预览
  - _Requirements: 8_

- [x] 29.9 版本管理对话框（src/components/RuleEditor/VersionDialog.vue）


  - 显示版本历史列表
  - 支持查看历史版本配置
  - 支持回滚到历史版本
  - _Requirements: 6_

- [x] 30. 任务管理页面




- [x] 30.1 任务列表页面（src/views/TaskList.vue）


  - 创建任务列表表格
  - 显示任务ID、文件名、页数、规则版本、置信度、状态、耗时、创建时间
  - 使用色块区分置信度等级
  - 实现筛选（状态、规则、时间范围）和搜索
  - _Requirements: 20_

- [x] 30.2 任务详情对话框（src/components/Task/TaskDetailDialog.vue）


  - 显示任务完整信息
  - 显示OCR结果、提取结果、置信度
  - 显示审核原因、推送日志
  - 显示状态流转时间线
  - _Requirements: 20, 55_



- [x] 30.3 状态标签组件（src/components/Task/StatusTag.vue）
  - 创建状态标签组件
  - 根据状态显示不同颜色和图标


  - _Requirements: 20_

- [x] 30.4 置信度徽章组件（src/components/Task/ConfidenceBadge.vue）
  - 创建置信度徽章组件
  - 使用颜色标识等级（高/中/低）
  - _Requirements: 41_

- [x] 31. 审核工作台页面




- [x] 31.1 审核工作台主页面（src/views/AuditWorkbench.vue）


  - 创建左右分栏布局
  - 左侧PDF预览，右侧结构化表单
  - 实现响应式布局（移动端上下布局）
  - _Requirements: 16, 63_

- [x] 31.2 PDF预览器（src/components/Audit/PDFViewer.vue）


  - 使用pdf.js或vue-pdf实现PDF预览
  - 实现分页器（上一页、下一页、跳转、页码显示）
  - 实现缩放和旋转功能
  - 实现懒加载（超过50页）
  - _Requirements: 16_

- [x] 31.3 OCR高亮功能

  - 在PDF上绘制OCR区域框
  - 实现跨页高亮（点击字段跳转到对应页面）
  - 实现划词回填（框选文本填入字段）
  - _Requirements: 16, 33_

- [x] 31.4 数据表单（src/components/Audit/DataForm.vue）


  - 根据Schema动态生成表单
  - 显示字段置信度
  - 支持字段编辑
  - 支持表格操作（插入行、删除行、上移、下移）
  - _Requirements: 16, 17, 41_

- [x] 31.5 草稿自动保存


  - 实现防抖保存（3秒后保存）
  - 保存到localStorage或调用API
  - 显示"草稿已保存"提示
  - _Requirements: 30_

- [x] 31.6 审核操作按钮


  - 实现确认通过按钮
  - 实现驳回按钮
  - 调用审核提交API
  - 显示成功提示并跳转到下一个任务
  - _Requirements: 17_

- [x] 32. Webhook配置页面





- [x] 32.1 Webhook列表页面（src/views/WebhookConfig.vue）


  - 创建Webhook列表表格
  - 显示系统名称、Endpoint URL、鉴权方式、状态
  - 实现新建、编辑、删除操作
  - _Requirements: 3_

- [x] 32.2 Webhook编辑对话框（src/components/Webhook/WebhookDialog.vue）

  - 创建Webhook配置表单
  - 配置系统名称、Endpoint URL、鉴权方式、Secret Key
  - 实现JSON编辑器配置请求体模版
  - 支持变量插入辅助
  - _Requirements: 3, 61_

- [x] 32.3 连通性测试功能

  - 实现发送测试按钮
  - 调用测试API
  - 显示响应结果（状态码、响应头、响应体）
  - _Requirements: 3_

- [x] 33. 用户管理页面






- [x] 33.1 用户列表页面（src/views/UserManagement.vue）



  - 创建用户列表表格
  - 显示用户名、邮箱、角色、状态、创建时间、最后登录时间
  - 实现新建、编辑、禁用、删除操作
  - 仅Admin角色可访问
  - _Requirements: 49_

- [x] 33.2 用户编辑对话框（src/components/User/UserDialog.vue）




  - 创建用户表单
  - 配置用户名、邮箱、角色、密码
  - 实现表单验证
  - _Requirements: 49_

- [x] 34. 系统设置页面






- [x] 34.1 系统设置主页面（src/views/SystemSettings.vue）

  - 创建设置页面，包含多个标签页
  - 数据生命周期、全局配置、审计日志
  - 仅Admin角色可访问
  - _Requirements: 4, 53_


- [x] 34.2 数据生命周期配置（src/components/Settings/RetentionConfig.vue）

  - 配置原始文件留存期
  - 配置提取数据留存期
  - 显示下次清理时间
  - _Requirements: 4_


- [x] 34.3 全局配置（src/components/Settings/GlobalConfig.vue）


  - 配置OCR超时时间、LLM超时时间、最大并行任务数
  - 配置LLM Token单价
  - 配置消息队列最大长度
  - _Requirements: 53_


- [x] 34.4 审计日志查询（src/components/Settings/AuditLogs.vue）

  - 创建审计日志列表
  - 支持筛选和搜索
  - 支持导出
  - _Requirements: 51_

- [x] 35. 公共组件




- [x] 35.1 文件上传器（src/components/Common/FileUploader.vue）


  - 创建文件上传组件
  - 支持拖拽上传
  - 显示上传进度
  - 验证文件大小和类型
  - _Requirements: 13, 64_

- [x] 35.2 加载状态组件（src/components/Common/LoadingState.vue）


  - 创建加载动画组件（Spinner或骨架屏）
  - 用于数据加载时显示
  - _Requirements: 64_

- [x] 35.3 错误提示组件


  - 使用Ant Design Vue的Message和Notification组件
  - 封装统一的成功/错误提示函数
  - _Requirements: 25, 64_

- [x] 36. API封装与状态管理







- [ ] 36.1 Axios配置（src/utils/request.js）
  - 创建Axios实例
  - 配置baseURL、timeout
  - 添加请求拦截器（添加Token）
  - 添加响应拦截器（统一错误处理）


  - _Requirements: 21, 69_

- [x] 36.2 API模块封装（src/api/）


  - 封装所有API接口（auth、task、rule、webhook、dashboard、user、system）
  - 使用统一的请求格式
  - _Requirements: 所有API相关需求_

- [ ] 36.3 Pinia Store实现（src/stores/）
  - 实现authStore（用户认证状态）
  - 实现ruleStore（规则数据缓存）
  - 实现taskStore（任务列表状态）
  - 实现dashboardStore（仪表盘数据）
  - _Requirements: 状态管理相关需求_


## 测试与优化

- [ ]* 37. 后端单元测试
- [ ]* 37.1 Services层测试（tests/services/）
  - 编写OCR服务测试用例
  - 编写提取服务测试用例
  - 编写校验服务测试用例
  - 编写推送服务测试用例
  - 使用Mock对象模拟外部依赖
  - _Requirements: 70_

- [ ]* 37.2 Utils层测试（tests/utils/）
  - 编写哈希计算测试用例
  - 编写签名生成测试用例
  - 编写加密解密测试用例
  - _Requirements: 70_

- [ ]* 38. 后端集成测试
- [ ]* 38.1 API端点测试（tests/api/）
  - 使用TestClient测试所有API接口
  - 测试正常流程和异常情况
  - 测试权限控制
  - _Requirements: 70_

- [ ]* 38.2 数据库集成测试
  - 使用测试数据库验证CRUD操作
  - 测试事务和并发
  - _Requirements: 70_

- [ ]* 39. 性能优化
- [ ]* 39.1 数据库查询优化
  - 分析慢查询日志
  - 添加必要的索引
  - 优化复杂查询
  - _Requirements: 65_

- [ ]* 39.2 缓存优化
  - 实现规则配置缓存
  - 实现仪表盘数据缓存
  - 实现PDF预览图缓存
  - _Requirements: 22_

- [ ]* 39.3 异步处理优化
  - 优化并发OCR处理
  - 优化并发推送
  - _Requirements: 22_

- [ ]* 40. 前端性能优化
- [ ]* 40.1 代码分割
  - 配置路由懒加载
  - 配置组件懒加载
  - _Requirements: 63_

- [ ]* 40.2 资源优化
  - 配置图片懒加载
  - 配置虚拟滚动（长列表）
  - 压缩打包文件
  - _Requirements: 63_

## 部署与文档

- [ ] 41. 部署配置
- [ ] 41.1 Docker镜像构建
  - 编写backend/Dockerfile
  - 编写frontend/Dockerfile
  - 优化镜像大小（多阶段构建）
  - _Requirements: 67_

- [ ] 41.2 Docker Compose编排
  - 完善docker-compose.yml
  - 配置服务依赖和健康检查
  - 配置数据卷持久化
  - _Requirements: 67_

- [ ] 41.3 Nginx配置
  - 编写frontend/nginx.conf
  - 配置反向代理
  - 配置静态资源缓存
  - 配置Gzip压缩
  - _Requirements: 67_

- [ ] 41.4 环境变量配置
  - 完善.env.example
  - 编写环境变量说明文档
  - _Requirements: 67_

- [ ] 42. 初始化脚本
- [ ] 42.1 数据库初始化脚本（backend/scripts/init.sql）
  - 创建默认管理员账号
  - 创建默认系统配置
  - _Requirements: 68_

- [ ] 42.2 MinIO初始化脚本
  - 创建idp-files bucket
  - 配置访问策略
  - _Requirements: 23_

- [ ] 43. 文档编写
- [ ] 43.1 README.md
  - 编写项目介绍
  - 编写快速开始指南
  - 编写部署说明
  - 编写开发指南
  - _Requirements: 67_

- [ ] 43.2 API文档
  - 使用FastAPI自动生成Swagger文档
  - 添加API描述和示例
  - _Requirements: 所有API相关需求_

- [ ] 43.3 用户手册
  - 编写功能使用说明
  - 编写规则配置指南
  - 编写常见问题解答
  - _Requirements: 所有功能需求_

## 集成与验收

- [ ] 44. 端到端测试
- [ ] 44.1 完整流程测试
  - 测试文件上传 → OCR → 提取 → 审核 → 推送完整流程
  - 测试秒传机制
  - 测试人工审核流程
  - 测试死信队列处理
  - _Requirements: 所有核心流程需求_

- [ ] 44.2 多用户角色测试
  - 测试Admin角色权限
  - 测试Architect角色权限
  - 测试Auditor角色权限
  - 测试Visitor角色权限
  - _Requirements: 5_

- [ ] 44.3 异常场景测试
  - 测试OCR超时处理
  - 测试LLM服务降级
  - 测试推送失败重试
  - 测试文件过大/页数过多
  - _Requirements: 12, 25, 31, 48_

- [ ] 45. 系统验收
- [ ] 45.1 功能验收
  - 验证所有70个需求是否实现
  - 验证所有API接口是否正常
  - 验证所有页面功能是否完整
  - _Requirements: 所有需求_

- [ ] 45.2 性能验收
  - 验证API响应时间<200ms
  - 验证秒传响应<500ms
  - 验证单页OCR<3s
  - 验证系统并发处理能力
  - _Requirements: 22_

- [ ] 45.3 安全验收
  - 验证认证授权机制
  - 验证数据加密
  - 验证HMAC签名
  - 验证SQL注入防护
  - 验证XSS防护
  - _Requirements: 21, 安全相关需求_

- [ ] 46. 上线准备
- [ ] 46.1 生产环境配置
  - 配置生产环境变量
  - 配置数据库连接池
  - 配置日志级别
  - 配置监控告警
  - _Requirements: 67_

- [ ] 46.2 数据备份方案
  - 配置MySQL自动备份
  - 配置MinIO数据备份
  - 编写备份恢复文档
  - _Requirements: 非功能需求_

- [ ] 46.3 运维文档
  - 编写部署运维手册
  - 编写故障排查指南
  - 编写监控告警配置
  - _Requirements: 非功能需求_

---

## 任务执行说明

### 任务优先级
1. **P0（核心基础）**：任务1-15（项目初始化、数据库、核心服务、Worker）
2. **P1（API实现）**：任务16-25（所有API端点）
3. **P2（前端实现）**：任务26-36（所有前端页面和组件）
4. **P3（测试优化）**：任务37-40（测试和性能优化，标记为可选*）
5. **P4（部署上线）**：任务41-46（部署配置、文档、验收）

### 任务依赖关系
- 任务1-4必须最先完成（项目初始化和数据库）
- 任务5-6依赖任务2-4（安全模块依赖数据库和配置）
- 任务7-12依赖任务2-4（业务服务依赖数据库和配置）
- 任务13-15依赖任务7-12（Worker依赖业务服务）
- 任务16-25依赖任务5-12（API依赖安全和业务服务）
- 任务26-36依赖任务16-25（前端依赖后端API）
- 任务44-46依赖所有前置任务（集成测试和上线依赖完整系统）

### 可选任务说明
标记为*的任务为可选任务，主要包括：
- 单元测试（任务37）
- 集成测试（任务38）
- 性能优化（任务39-40）

这些任务虽然重要，但不影响核心功能实现。建议在核心功能完成后，根据时间和资源情况选择性实施。

### 预估工作量
- **后端开发**：约30-40个工作日
- **前端开发**：约25-35个工作日
- **测试与优化**：约10-15个工作日
- **部署与文档**：约5-10个工作日
- **总计**：约70-100个工作日（约3-4个月，2-3人团队）

### 技术难点
1. **多页PDF处理与OCR合并**：需要处理大文件、并行OCR、文本合并逻辑
2. **跨页表格识别与合并**：需要智能识别表格延续关系
3. **审核工作台交互**：PDF预览、OCR高亮、跨页跳转、划词回填等复杂交互
4. **LLM集成与熔断**：需要处理超时、降级、Token计费等
5. **分布式任务处理**：消息队列、Worker扩展、死信队列处理
6. **性能优化**：大文件处理、高并发、缓存策略

### 开发建议
1. **迭代开发**：按照P0→P1→P2→P3→P4的顺序逐步实现
2. **持续集成**：每完成一个模块立即进行集成测试
3. **代码审查**：关键模块（OCR、提取、推送）需要代码审查
4. **文档同步**：开发过程中同步更新API文档和用户手册
5. **性能监控**：从开发阶段就关注性能指标，及时优化

---

## 总结

本实现计划包含46个主要任务，涵盖了从项目初始化到上线部署的完整流程。所有任务都基于需求文档和设计文档，确保实现的功能完全满足PRD要求。

每个任务都包含：
- 清晰的任务描述
- 具体的实现内容
- 关联的需求编号
- 可执行的开发指导

通过按照本计划执行，可以系统化地完成企业级智能文档处理平台的开发工作。
