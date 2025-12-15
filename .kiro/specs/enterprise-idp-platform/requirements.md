# Requirements Document - Enterprise IDP Platform

## Introduction

本文档定义了企业级智能文档处理中台（Enterprise IDP Platform）的功能需求。该系统旨在构建一个高可用、可溯源、智能化的文档处理平台，支持单页及多页长文档的自动化解析，实现从规则定义、合并提取、人机协同审核到下游安全推送的全链路闭环。

系统基于"规则引擎 + OCR + LLM 增强"的技术架构，提供文档接入、去重秒传、多页合并提取、自动质检和下游安全推送等核心能力。

## Glossary

- **IDP_System**: 智能文档处理系统，本需求文档中的核心系统
- **OCR_Engine**: 光学字符识别引擎，用于从图像或PDF中提取文本
- **LLM_Service**: 大语言模型服务，用于智能提取和增强
- **Rule_Engine**: 规则引擎，管理文档处理规则的配置和执行
- **Task**: 文档处理任务，代表一次文档处理请求
- **Webhook_Target**: 下游业务系统的回调接口
- **Hash_Key**: 文件指纹，用于去重判断的唯一标识
- **STP_Rate**: 直通率（Straight Through Processing），无需人工干预的任务比例
- **Audit_Workbench**: 审核工作台，人工审核和修正的界面
- **DLQ**: 死信队列（Dead Letter Queue），存储推送失败的任务
- **RBAC**: 基于角色的访问控制（Role-Based Access Control）
- **Page_Strategy**: 页面处理策略，定义如何处理单页或多页文档
- **Global_Context_String**: 全局上下文字符串，合并所有页面OCR结果的文本

## Requirements

### Requirement 1: Dashboard Metrics Display

**User Story:** 作为系统管理员，我希望在仪表盘上查看关键业务指标，以便实时监控系统运行状态和业务健康度

#### Acceptance Criteria

1. WHEN 用户访问仪表盘页面, THE IDP_System SHALL 展示总接单量、累计处理页数、处理中任务数、待人工审核数、推送异常数、平均直通率、算力节省和LLM消耗估算等8个核心指标
2. WHEN 用户选择时间范围筛选器（今日、近7天、近30天）, THE IDP_System SHALL 在200毫秒内更新所有指标数据
3. WHERE 推送异常数大于0, THE IDP_System SHALL 以红色预警样式显示该指标
4. THE IDP_System SHALL 计算平均直通率为无需人工干预且成功推送的任务数除以总任务数的百分比
5. THE IDP_System SHALL 统计累计处理页数为所有任务实际消耗的OCR页数总和

### Requirement 2: Dashboard Visualization Charts

**User Story:** 作为系统管理员，我希望通过可视化图表了解系统趋势和异常分布，以便快速识别问题和优化方向

#### Acceptance Criteria

1. THE IDP_System SHALL 在仪表盘展示任务吞吐趋势的堆叠柱状图，包含成功、待审核、失败、驳回四种状态的每日数量
2. THE IDP_System SHALL 展示规则效能Top10列表，按任务量降序排列，包含规则名称、平均耗时和人工干预率
3. THE IDP_System SHALL 展示异常分布饼图，显示各类异常原因的占比（OCR识别空、必填校验失败、LLM不一致、下游接口500等）
4. WHEN 用户点击图表中的数据点, THE IDP_System SHALL 跳转到对应的任务列表筛选视图


### Requirement 3: Webhook Target Configuration

**User Story:** 作为系统管理员，我希望配置下游业务系统的回调接口，以便安全地推送处理结果

#### Acceptance Criteria

1. THE IDP_System SHALL 提供Webhook目标系统配置界面，包含系统名称、Endpoint URL、鉴权方式、安全签名密钥和请求体模版字段
2. THE IDP_System SHALL 支持四种鉴权方式：No Auth、Basic Auth、Bearer Token、API Key
3. WHEN 配置安全签名密钥, THE IDP_System SHALL 使用HMAC-SHA256算法对请求体生成签名，并在推送时将签名放入X-IDP-Signature请求头
4. THE IDP_System SHALL 在请求体模版中支持变量注入：{{task_id}}、{{result_json}}、{{file_url}}、{{meta_info}}
5. WHEN 用户点击发送测试按钮, THE IDP_System SHALL 使用Mock数据发送测试请求，并在5秒内展示响应状态码、响应头和响应体
6. THE IDP_System SHALL 对Secret Key等敏感字段使用AES-256加密存储

### Requirement 4: Data Retention Policy

**User Story:** 作为系统管理员，我希望配置数据生命周期策略，以便平衡存储成本和合规审计需求

#### Acceptance Criteria

1. THE IDP_System SHALL 提供原始文件留存期配置，默认值为30天
2. THE IDP_System SHALL 提供提取数据留存期配置，默认值为永久保留
3. THE IDP_System SHALL 每日凌晨02:00执行定时清理任务，删除超过留存期的原始文件
4. WHEN 执行清理任务, THE IDP_System SHALL 记录清理日志，包含删除文件数量和释放存储空间大小
5. THE IDP_System SHALL 在删除文件前验证该文件对应的任务状态为已完成或已驳回

### Requirement 5: Role-Based Access Control

**User Story:** 作为系统管理员，我希望实现基于角色的权限管理，以便保障配置和数据安全

#### Acceptance Criteria

1. THE IDP_System SHALL 支持四种角色：超级管理员（Admin）、规则架构师（Architect）、业务审核员（Auditor）、API访客（Visitor）
2. WHERE 用户角色为Admin, THE IDP_System SHALL 授予全部功能权限，包括系统配置、规则管理、审核工作台和账号管理
3. WHERE 用户角色为Architect, THE IDP_System SHALL 仅授予规则管理模块权限，包括创建、编辑、发布、回滚规则和沙箱测试
4. WHERE 用户角色为Auditor, THE IDP_System SHALL 仅授予审核工作台权限，不可修改规则配置
5. WHERE 用户角色为Visitor, THE IDP_System SHALL 仅授予API Key生成和查看权限
6. WHEN 用户尝试访问无权限的功能, THE IDP_System SHALL 返回403 Forbidden错误并记录访问日志


### Requirement 6: Rule Lifecycle Management

**User Story:** 作为规则架构师，我希望管理规则的完整生命周期，以便安全地创建、测试、发布和回滚规则配置

#### Acceptance Criteria

1. THE IDP_System SHALL 为每个规则维护版本历史，包括草稿（Draft）、已发布（Published）和历史版本（Archived）三种状态
2. WHEN 创建新规则, THE IDP_System SHALL 生成唯一的规则编码和初始草稿版本
3. WHEN 发布草稿版本, THE IDP_System SHALL 生成新的版本号（如V1.0、V1.1），并将当前已发布版本归档为历史版本
4. THE IDP_System SHALL 确保同一时刻仅有一个已发布版本用于生产环境
5. WHEN 用户执行回滚操作, THE IDP_System SHALL 将指定的历史版本恢复为已发布状态，并将当前版本归档
6. THE IDP_System SHALL 记录规则的所有变更历史，包含操作人、操作时间和变更内容

### Requirement 7: Rule Editor - Basic Configuration

**User Story:** 作为规则架构师，我希望配置规则的基础参数和OCR引擎，以便适配不同类型的文档处理需求

#### Acceptance Criteria

1. THE IDP_System SHALL 在规则编辑器中提供OCR引擎选择，支持PaddleOCR、Tesseract和Azure Form Recognizer
2. THE IDP_System SHALL 支持语言配置，包括中文、英文和混排模式
3. THE IDP_System SHALL 提供页面处理策略配置，包括单页模式、多页合并模式和指定页码三种选项
4. WHERE 页面处理策略为单页模式, THE IDP_System SHALL 仅处理PDF的第一页
5. WHERE 页面处理策略为多页合并模式, THE IDP_System SHALL 处理所有页面并按页码顺序合并OCR结果
6. WHERE 页面处理策略为指定页码, THE IDP_System SHALL 支持页码范围表达式（如"1-3"或"Last Page"）

### Requirement 8: Rule Editor - Sandbox Testing

**User Story:** 作为规则架构师，我希望在沙箱环境中测试规则配置，以便在发布前验证规则的正确性

#### Acceptance Criteria

1. THE IDP_System SHALL 在规则编辑器顶部提供常驻的"运行测试"按钮
2. WHEN 用户点击运行测试, THE IDP_System SHALL 允许上传本地样张文件（PDF或图片）
3. WHEN 沙箱测试执行完成, THE IDP_System SHALL 在30秒内展示提取的JSON结果和OCR标注预览
4. WHERE 上传文件为多页PDF, THE IDP_System SHALL 展示合并后的OCR纯文本预览，方便调试跨页正则表达式
5. THE IDP_System SHALL 确保沙箱测试不影响生产环境数据和任务队列
6. THE IDP_System SHALL 在沙箱测试结果中标注每个字段的置信度和数据来源页码


### Requirement 9: Rule Editor - Schema Definition

**User Story:** 作为规则架构师，我希望定义目标JSON结构和字段属性，以便精确控制数据提取的格式和验证规则

#### Acceptance Criteria

1. THE IDP_System SHALL 支持四种节点类型：Object（对象）、Array（数组）、Table（明细表）、Field（原子字段）
2. THE IDP_System SHALL 为每个字段提供Key（字段名）、Label（显示名）、Type（数据类型）配置
3. THE IDP_System SHALL 支持五种数据类型：String、Int、Date、Decimal、Boolean
4. THE IDP_System SHALL 允许为字段配置默认值，当提取结果为空且非必填时自动填充
5. THE IDP_System SHALL 允许为每个字段配置独立的置信度阈值（范围0-100）
6. THE IDP_System SHALL 支持深层嵌套结构，最大嵌套层级为5层

### Requirement 10: Rule Editor - Extraction Strategy

**User Story:** 作为规则架构师，我希望配置多种提取策略，以便从文档中准确提取所需信息

#### Acceptance Criteria

1. THE IDP_System SHALL 默认基于Global_Context_String（合并后的全文）执行所有提取操作
2. WHEN 合并多页文本, THE IDP_System SHALL 在页与页之间插入换行符，防止跨页词汇粘连
3. THE IDP_System SHALL 支持锚点定位提取，基于关键词的相对位置提取目标字段
4. THE IDP_System SHALL 支持正则表达式提取，执行全文正则匹配并支持跨页匹配
5. THE IDP_System SHALL 支持表格提取，并支持跨页表格合并（根据表头逻辑自动拼接行数据）
6. THE IDP_System SHALL 支持LLM智能提取，允许配置自定义Prompt和Context Scope（全文、指定区域或前N页）

### Requirement 11: Rule Editor - Data Cleaning and Validation

**User Story:** 作为规则架构师，我希望配置数据清洗和校验规则，以便确保提取数据的质量和一致性

#### Acceptance Criteria

1. THE IDP_System SHALL 提供清洗管道，支持正则替换（Replace）、去空格（Trim）、日期格式化（Date Format）操作
2. THE IDP_System SHALL 支持必填校验，当必填字段为空时标记任务为待审核状态
3. THE IDP_System SHALL 支持正则格式校验，验证Email、Phone等特定格式
4. THE IDP_System SHALL 支持数值范围校验，验证数值字段是否在指定范围内
5. THE IDP_System SHALL 支持自定义JavaScript表达式校验（如amount * count == total）
6. WHEN 任何校验规则失败, THE IDP_System SHALL 记录失败原因并将任务状态设置为Pending Audit


### Requirement 12: Rule Editor - Enhancement and Risk Control

**User Story:** 作为规则架构师，我希望配置智能增强和风控策略，以便提高提取准确率并控制成本

#### Acceptance Criteria

1. WHERE 自动增强功能启用, WHEN OCR结果为空, THE IDP_System SHALL 自动重试备用引擎或调用LLM补全
2. WHERE 一致性校验启用, THE IDP_System SHALL 同时运行OCR和LLM提取，并对比结果差异
3. WHERE 一致性校验启用, WHEN OCR和LLM结果差异超过配置阈值, THE IDP_System SHALL 强制将任务转为人工审核
4. THE IDP_System SHALL 支持配置单次任务的最大Token数限制
5. WHEN LLM接口响应时间超过60秒, THE IDP_System SHALL 自动降级为纯OCR模式并在日志中标记"Warning: LLM Fallback"
6. WHEN LLM接口返回5xx错误, THE IDP_System SHALL 自动降级为纯OCR模式并在日志中标记"Warning: LLM Fallback"

### Requirement 13: Document Upload and Deduplication

**User Story:** 作为API调用方，我希望上传文档并自动去重，以便节省重复处理的算力成本

#### Acceptance Criteria

1. THE IDP_System SHALL 接收文件上传请求，包含file（二进制文件）、rule_id（必填）和rule_version（可选）参数
2. THE IDP_System SHALL 限制单个文件最大20MB或50页
3. WHEN 接收上传请求, THE IDP_System SHALL 计算Hash_Key为SHA256(File_Binary) + Rule_ID + Rule_Version
4. WHEN Hash_Key在数据库中存在且对应任务状态为Completed, THE IDP_System SHALL 直接复制历史结果，标记任务类型为instant（秒传），并在500毫秒内返回结果
5. WHEN Hash_Key未命中, THE IDP_System SHALL 将文件上传至对象存储，生成新任务并加入消息队列
6. THE IDP_System SHALL 在200毫秒内返回任务ID、是否秒传标识、任务状态和预估等待时间

### Requirement 14: Task Processing - OCR and Text Merging

**User Story:** 作为系统，我希望执行OCR识别并合并多页文本，以便为后续提取提供完整的上下文

#### Acceptance Criteria

1. WHEN Worker从消息队列消费任务, THE IDP_System SHALL 从对象存储下载文件
2. THE IDP_System SHALL 判断文件页数，根据规则的Page_Strategy确定需要处理的页码范围
3. THE IDP_System SHALL 对每一页执行OCR识别，生成文本和坐标信息
4. THE IDP_System SHALL 按页码顺序拼接所有页面的OCR文本，形成Global_Context_String
5. WHERE 文件为单页, THE IDP_System SHALL 在3秒内完成OCR处理
6. WHERE 文件为多页, THE IDP_System SHALL 在(2秒 * 页数 + 1秒)内完成OCR处理，最大超时时间为300秒


### Requirement 15: Task Processing - Data Extraction and Quality Check

**User Story:** 作为系统，我希望根据规则配置提取数据并执行质检，以便自动识别需要人工审核的任务

#### Acceptance Criteria

1. THE IDP_System SHALL 将Global_Context_String输入提取引擎，根据规则配置执行正则、表格或LLM提取
2. WHERE 规则配置了LLM增强, THE IDP_System SHALL 调用LLM_Service执行智能提取或校验
3. THE IDP_System SHALL 执行配置的数据清洗管道，包括正则替换、去空格和格式化操作
4. THE IDP_System SHALL 执行必填校验、格式校验和数值范围校验
5. THE IDP_System SHALL 检查每个字段的置信度是否低于配置的阈值
6. WHEN 所有校验通过且置信度达标, THE IDP_System SHALL 将任务状态设置为Completed
7. WHEN 任何校验失败或置信度不达标, THE IDP_System SHALL 将任务状态设置为Pending Audit并记录原因

### Requirement 16: Audit Workbench - Multi-page PDF Preview

**User Story:** 作为业务审核员，我希望在审核工作台浏览多页PDF并修正提取结果，以便高效完成人工审核

#### Acceptance Criteria

1. THE IDP_System SHALL 在审核工作台左侧展示PDF预览，右侧展示结构化表单
2. THE IDP_System SHALL 在PDF预览顶部提供分页器，包含上一页、下一页、跳转按钮和页码显示（如1/15）
3. THE IDP_System SHALL 支持PDF缩放和旋转操作
4. WHERE PDF页数超过50页, THE IDP_System SHALL 采用懒加载机制，按需加载图片切片
5. WHEN 用户点击右侧表单中的字段, THE IDP_System SHALL 自动跳转到该字段数据来源的页码并高亮对应的OCR区域
6. WHEN 用户在左侧PDF中框选文本, THE IDP_System SHALL 支持将选中文本填入右侧聚焦的字段

### Requirement 17: Audit Workbench - Data Correction and Submission

**User Story:** 作为业务审核员，我希望修正提取结果并提交审核决策，以便完成任务处理流程

#### Acceptance Criteria

1. THE IDP_System SHALL 在右侧表单中展示所有提取字段，支持直接编辑
2. WHERE 字段类型为Table, THE IDP_System SHALL 提供插入行、删除行、上移、下移操作
3. WHEN 用户点击确认通过按钮, THE IDP_System SHALL 保存修正后的数据，将任务状态变更为Completed，并触发推送流程
4. WHEN 用户点击驳回按钮, THE IDP_System SHALL 将任务状态变更为Rejected，并记录驳回原因
5. THE IDP_System SHALL 在用户修改字段后自动保存草稿，防止数据丢失
6. THE IDP_System SHALL 记录审核操作日志，包含审核人、操作时间和修改内容


### Requirement 18: Result Push and Retry Mechanism

**User Story:** 作为系统，我希望安全地推送处理结果到下游系统并支持失败重试，以便确保数据传输的可靠性

#### Acceptance Criteria

1. WHEN 任务状态变更为Completed, THE IDP_System SHALL 根据规则关联的Webhook_Target配置组装推送请求
2. THE IDP_System SHALL 使用配置的请求体模版，将{{task_id}}、{{result_json}}、{{file_url}}、{{meta_info}}替换为实际值
3. THE IDP_System SHALL 使用HMAC-SHA256算法计算请求体签名，并将签名放入X-IDP-Signature请求头
4. THE IDP_System SHALL 根据配置的鉴权方式添加相应的认证信息到请求头
5. WHEN 推送请求成功（HTTP 2xx）, THE IDP_System SHALL 记录推送日志，包含HTTP状态码、请求头、请求体、响应体和耗时
6. WHEN 推送请求失败, THE IDP_System SHALL 使用指数退避算法自动重试，最多重试3次
7. WHEN 重试3次后仍失败, THE IDP_System SHALL 将任务加入死信队列（DLQ）

### Requirement 19: Dead Letter Queue Management

**User Story:** 作为系统管理员，我希望管理推送失败的任务，以便手动排查问题并重新推送

#### Acceptance Criteria

1. THE IDP_System SHALL 在任务列表中展示推送异常的任务，标记为红色预警
2. THE IDP_System SHALL 提供死信队列管理界面，展示所有推送失败的任务
3. WHEN 用户点击查看报文, THE IDP_System SHALL 展示完整的推送请求和响应详情，包含HTTP状态码、请求头、请求体、响应体和错误信息
4. THE IDP_System SHALL 支持单个任务的手动重推操作
5. THE IDP_System SHALL 支持批量选择任务并执行批量重推操作
6. WHEN 执行重推操作, THE IDP_System SHALL 使用最新的Webhook配置重新发送请求

### Requirement 20: Task List and Status Tracking

**User Story:** 作为系统用户，我希望查看任务列表并跟踪任务状态，以便了解文档处理进度

#### Acceptance Criteria

1. THE IDP_System SHALL 展示任务列表，包含任务ID、文件名、页数、规则版本、置信度、状态、耗时、创建时间字段
2. THE IDP_System SHALL 使用色块区分不同的置信度等级（高：绿色，中：黄色，低：红色）
3. THE IDP_System SHALL 支持按状态、规则、时间范围筛选任务
4. THE IDP_System SHALL 支持按任务ID、文件名搜索任务
5. THE IDP_System SHALL 支持任务状态流转：Queued -> Processing -> Pending Audit -> Completed -> Pushing -> Push Success
6. THE IDP_System SHALL 支持任务状态流转：Queued -> Processing -> Pending Audit -> Rejected
7. THE IDP_System SHALL 支持任务状态流转：Completed -> Pushing -> Push Failed -> DLQ


### Requirement 21: API Authentication and Security

**User Story:** 作为API调用方，我希望使用安全的认证方式访问系统API，以便保护数据传输安全

#### Acceptance Criteria

1. THE IDP_System SHALL 支持Bearer Token认证方式用于API访问
2. THE IDP_System SHALL 为每个API Key生成唯一的标识和密钥
3. THE IDP_System SHALL 使用AES-256算法加密存储API Key和Secret Key
4. WHEN API请求缺少认证信息, THE IDP_System SHALL 返回401 Unauthorized错误
5. WHEN API请求使用无效的认证信息, THE IDP_System SHALL 返回403 Forbidden错误
6. THE IDP_System SHALL 记录所有API访问日志，包含请求IP、请求时间、请求路径和响应状态

### Requirement 22: System Performance and Scalability

**User Story:** 作为系统架构师，我希望系统满足性能指标并支持水平扩展，以便应对业务增长

#### Acceptance Criteria

1. THE IDP_System SHALL 在200毫秒内响应文件上传请求
2. THE IDP_System SHALL 在500毫秒内响应秒传请求
3. THE IDP_System SHALL 在3秒内完成单页文档的OCR处理
4. THE IDP_System SHALL 采用无状态设计，支持Kubernetes水平扩展
5. THE IDP_System SHALL 使用Redis缓存规则配置，减少数据库查询压力
6. THE IDP_System SHALL 使用消息队列（RabbitMQ）实现任务异步处理，确保服务重启不丢失任务

### Requirement 23: File Storage and Management

**User Story:** 作为系统，我希望安全地存储和管理文档文件，以便支持审核和追溯

#### Acceptance Criteria

1. THE IDP_System SHALL 使用MinIO对象存储服务存储上传的PDF和图片文件
2. THE IDP_System SHALL 为每个文件生成唯一的存储路径，格式为：{bucket}/{year}/{month}/{day}/{task_id}/{filename}
3. THE IDP_System SHALL 在文件上传成功后返回文件访问URL
4. THE IDP_System SHALL 支持生成带有效期的预签名URL，用于临时访问文件
5. THE IDP_System SHALL 根据配置的留存期自动清理过期文件
6. THE IDP_System SHALL 确保文件传输使用TLS 1.2+加密


### Requirement 24: Logging and Monitoring

**User Story:** 作为系统管理员，我希望查看详细的系统日志和监控指标，以便快速定位和解决问题

#### Acceptance Criteria

1. THE IDP_System SHALL 记录所有任务处理日志，包含任务ID、处理阶段、耗时、状态和错误信息
2. THE IDP_System SHALL 记录所有API访问日志，包含请求方法、路径、参数、响应状态和耗时
3. THE IDP_System SHALL 记录所有推送日志，包含目标URL、请求头、请求体、响应状态和耗时
4. THE IDP_System SHALL 记录所有规则变更日志，包含操作人、操作类型、变更前后内容和时间戳
5. THE IDP_System SHALL 记录所有审核操作日志，包含审核人、任务ID、修改字段和审核决策
6. THE IDP_System SHALL 提供日志查询界面，支持按时间范围、任务ID、用户、操作类型筛选日志

### Requirement 25: Error Handling and User Feedback

**User Story:** 作为系统用户，我希望在操作失败时获得清晰的错误提示，以便快速理解问题并采取行动

#### Acceptance Criteria

1. WHEN 文件上传超过大小限制, THE IDP_System SHALL 返回400错误并提示"文件大小超过20MB限制"
2. WHEN 文件上传超过页数限制, THE IDP_System SHALL 返回400错误并提示"文件页数超过50页限制"
3. WHEN 指定的规则不存在, THE IDP_System SHALL 返回404错误并提示"规则不存在"
4. WHEN OCR处理超时, THE IDP_System SHALL 将任务状态设置为Failed并记录错误原因"OCR处理超时"
5. WHEN LLM服务不可用, THE IDP_System SHALL 自动降级为纯OCR模式并在任务详情中标记"LLM服务降级"
6. THE IDP_System SHALL 在前端界面使用统一的错误提示组件，展示错误信息和建议操作

### Requirement 26: Data Export and Reporting

**User Story:** 作为系统管理员，我希望导出任务数据和生成报表，以便进行数据分析和业务汇报

#### Acceptance Criteria

1. THE IDP_System SHALL 支持导出任务列表为CSV或Excel格式
2. THE IDP_System SHALL 支持导出指定任务的完整处理结果为JSON格式
3. THE IDP_System SHALL 支持生成日报、周报、月报，包含任务量、直通率、平均耗时等关键指标
4. THE IDP_System SHALL 支持按规则、状态、时间范围筛选导出数据
5. WHEN 导出数据量超过10000条, THE IDP_System SHALL 采用异步导出方式，完成后通过邮件或系统通知发送下载链接
6. THE IDP_System SHALL 在导出文件中包含导出时间、导出人和筛选条件等元信息


### Requirement 27: Rule Editor - Document Type Configuration

**User Story:** 作为规则架构师，我希望为规则配置文档类型标识，以便对不同类型的文档应用不同的处理规则

#### Acceptance Criteria

1. THE IDP_System SHALL 在规则基本属性中提供文档类型字段配置
2. THE IDP_System SHALL 支持自定义文档类型名称（如"发票"、"合同"、"身份证"等）
3. THE IDP_System SHALL 在规则列表中按文档类型分组展示规则
4. THE IDP_System SHALL 在任务列表中展示任务关联的文档类型
5. THE IDP_System SHALL 在仪表盘中支持按文档类型筛选统计数据

### Requirement 28: Rule Configuration - Custom Page Separator

**User Story:** 作为规则架构师，我希望自定义页面文本合并时的分隔符，以便更好地控制跨页文本的拼接逻辑

#### Acceptance Criteria

1. THE IDP_System SHALL 在页面处理策略配置中提供自定义分隔符选项
2. THE IDP_System SHALL 支持使用换行符（\n）、双换行符（\n\n）或自定义字符串作为分隔符
3. THE IDP_System SHALL 默认使用单换行符（\n）作为页面分隔符
4. WHEN 合并多页OCR文本, THE IDP_System SHALL 在每两页之间插入配置的分隔符
5. THE IDP_System SHALL 在沙箱测试结果中展示使用分隔符后的合并文本预览

### Requirement 29: Task Processing - Estimated Wait Time Calculation

**User Story:** 作为API调用方，我希望在上传文件后获得预估等待时间，以便合理安排后续操作

#### Acceptance Criteria

1. WHEN 文件上传成功, THE IDP_System SHALL 根据文件页数计算预估等待时间
2. WHERE 文件为单页, THE IDP_System SHALL 返回预估等待时间为3秒
3. WHERE 文件为多页, THE IDP_System SHALL 返回预估等待时间为(2秒 * 页数 + 1秒)
4. THE IDP_System SHALL 在预估等待时间计算中考虑当前队列长度
5. WHERE 队列中有N个任务等待处理, THE IDP_System SHALL 在基础等待时间上增加(N * 平均任务耗时)

### Requirement 30: Audit Workbench - Draft Auto-save

**User Story:** 作为业务审核员，我希望系统自动保存我的修改草稿，以便在意外情况下不丢失修改内容

#### Acceptance Criteria

1. WHEN 用户在审核工作台修改字段值, THE IDP_System SHALL 在3秒后自动保存草稿
2. THE IDP_System SHALL 在浏览器本地存储中保存草稿数据
3. WHEN 用户重新打开同一任务, THE IDP_System SHALL 自动加载之前保存的草稿
4. WHEN 用户点击确认通过或驳回, THE IDP_System SHALL 清除对应任务的草稿数据
5. THE IDP_System SHALL 在界面上显示"草稿已保存"的提示信息


### Requirement 31: Push Mechanism - Exponential Backoff Retry

**User Story:** 作为系统，我希望使用指数退避算法进行推送重试，以便在下游系统临时故障时提高推送成功率

#### Acceptance Criteria

1. WHEN 推送请求失败, THE IDP_System SHALL 使用指数退避算法计算下次重试时间
2. THE IDP_System SHALL 在第1次重试前等待10秒
3. THE IDP_System SHALL 在第2次重试前等待30秒
4. THE IDP_System SHALL 在第3次重试前等待90秒
5. WHEN 3次重试全部失败, THE IDP_System SHALL 将任务移入死信队列
6. THE IDP_System SHALL 在推送日志中记录每次重试的时间和结果

### Requirement 32: Webhook Configuration - Multiple Targets

**User Story:** 作为系统管理员，我希望为一个规则配置多个推送目标，以便同时向多个下游系统推送结果

#### Acceptance Criteria

1. THE IDP_System SHALL 支持为单个规则关联多个Webhook目标系统
2. WHEN 任务完成, THE IDP_System SHALL 并行向所有关联的Webhook目标推送结果
3. THE IDP_System SHALL 为每个推送目标独立记录推送状态和日志
4. WHERE 任一推送目标失败, THE IDP_System SHALL 仅对该目标执行重试，不影响其他目标
5. THE IDP_System SHALL 在任务详情中展示所有推送目标的推送状态

### Requirement 33: OCR Result - Coordinate Information Storage

**User Story:** 作为系统，我希望存储OCR识别结果的坐标信息，以便在审核工作台中实现高亮联动功能

#### Acceptance Criteria

1. THE IDP_System SHALL 在执行OCR识别时记录每个文本块的坐标信息（x, y, width, height）
2. THE IDP_System SHALL 在数据库中存储OCR结果的完整坐标信息
3. THE IDP_System SHALL 记录每个提取字段对应的OCR文本块坐标和页码
4. THE IDP_System SHALL 在审核工作台API中返回字段的坐标和页码信息
5. THE IDP_System SHALL 支持多个坐标区域对应同一个字段（如跨行文本）

### Requirement 34: Rule Editor - Field Required Configuration

**User Story:** 作为规则架构师，我希望配置字段的必填属性，以便在提取结果为空时触发人工审核

#### Acceptance Criteria

1. THE IDP_System SHALL 在字段属性配置中提供"必填"选项
2. WHERE 字段配置为必填, WHEN 提取结果为空或null, THE IDP_System SHALL 将任务状态设置为Pending Audit
3. WHERE 字段配置为非必填, WHEN 提取结果为空, THE IDP_System SHALL 使用配置的默认值填充
4. THE IDP_System SHALL 在审核原因中明确标注"必填字段为空：{字段名}"
5. THE IDP_System SHALL 在沙箱测试结果中标注必填字段的校验状态


### Requirement 35: Task Queue - Persistent Message Queue

**User Story:** 作为系统架构师，我希望使用持久化消息队列，以便在服务重启时不丢失待处理任务

#### Acceptance Criteria

1. THE IDP_System SHALL 使用RabbitMQ持久化模式存储任务消息
2. THE IDP_System SHALL 在任务消息中包含task_id、file_path、rule_id、rule_version等完整信息
3. WHEN 服务重启, THE IDP_System SHALL 自动从消息队列中恢复未处理的任务
4. THE IDP_System SHALL 确保消息在Worker确认处理完成前不会从队列中删除
5. THE IDP_System SHALL 支持配置消息队列的最大长度和过期时间

### Requirement 36: File Storage - Presigned URL Generation

**User Story:** 作为系统，我希望生成带有效期的预签名URL，以便安全地提供文件临时访问权限

#### Acceptance Criteria

1. THE IDP_System SHALL 支持生成MinIO对象存储的预签名URL
2. THE IDP_System SHALL 设置预签名URL的默认有效期为1小时
3. THE IDP_System SHALL 在审核工作台API中返回PDF文件的预签名URL
4. THE IDP_System SHALL 在推送请求中包含原始文件的预签名URL（如配置了{{file_url}}变量）
5. WHEN 预签名URL过期, THE IDP_System SHALL 支持重新生成新的预签名URL

### Requirement 37: Dashboard - Cost Savings Calculation

**User Story:** 作为系统管理员，我希望查看通过哈希秒传节省的算力成本，以便评估去重机制的价值

#### Acceptance Criteria

1. THE IDP_System SHALL 统计秒传任务的总数量
2. THE IDP_System SHALL 计算秒传任务节省的总页数（秒传任务的页数总和）
3. THE IDP_System SHALL 根据单页处理耗时（3秒）计算节省的总耗时
4. THE IDP_System SHALL 在仪表盘展示"算力节省"指标，格式为"节省X小时（Y个任务，Z页）"
5. THE IDP_System SHALL 支持按时间范围筛选算力节省统计数据

### Requirement 38: LLM Integration - Token Consumption Tracking

**User Story:** 作为系统管理员，我希望跟踪LLM的Token消耗和费用，以便控制AI成本

#### Acceptance Criteria

1. THE IDP_System SHALL 在每次调用LLM后记录消耗的Token数（包含输入和输出Token）
2. THE IDP_System SHALL 在数据库中存储每个任务的LLM Token消耗记录
3. THE IDP_System SHALL 根据配置的Token单价计算预估费用
4. THE IDP_System SHALL 在仪表盘展示"LLM消耗估算"，包含总Token数和预估费用
5. THE IDP_System SHALL 支持按时间范围和规则筛选LLM消耗统计
6. THE IDP_System SHALL 在任务详情中展示该任务的LLM Token消耗


### Requirement 39: Rule Editor - Azure Form Recognizer Support

**User Story:** 作为规则架构师，我希望使用Azure Form Recognizer作为OCR引擎，以便处理复杂的表单文档

#### Acceptance Criteria

1. THE IDP_System SHALL 在OCR引擎选项中支持Azure Form Recognizer
2. THE IDP_System SHALL 支持配置Azure Form Recognizer的API Key和Endpoint
3. WHERE OCR引擎为Azure Form Recognizer, THE IDP_System SHALL 调用Azure API执行文档分析
4. THE IDP_System SHALL 将Azure Form Recognizer返回的结果转换为统一的OCR结果格式
5. THE IDP_System SHALL 在Azure API调用失败时记录详细错误信息

### Requirement 40: Task Processing - Parallel OCR Processing

**User Story:** 作为系统，我希望并行处理多页文档的OCR识别，以便提高处理速度

#### Acceptance Criteria

1. WHERE 文档页数大于5页, THE IDP_System SHALL 使用并行处理方式执行OCR识别
2. THE IDP_System SHALL 支持配置最大并行OCR任务数（默认为4）
3. THE IDP_System SHALL 在所有页面OCR完成后按页码顺序合并文本
4. THE IDP_System SHALL 确保并行处理不影响OCR结果的准确性
5. THE IDP_System SHALL 在任务日志中记录并行处理的耗时统计

### Requirement 41: Audit Workbench - Confidence Score Display

**User Story:** 作为业务审核员，我希望在审核工作台中查看每个字段的置信度分数，以便判断提取结果的可靠性

#### Acceptance Criteria

1. THE IDP_System SHALL 在审核工作台的每个字段旁边展示置信度分数（0-100）
2. THE IDP_System SHALL 使用颜色标识置信度等级：高（绿色，>80）、中（黄色，50-80）、低（红色，<50）
3. WHERE 字段置信度低于配置阈值, THE IDP_System SHALL 在字段旁边显示警告图标
4. THE IDP_System SHALL 支持点击置信度分数查看详细的置信度计算依据
5. THE IDP_System SHALL 在用户手动修改字段后将置信度标记为100（人工确认）

### Requirement 42: Rule Configuration - Anchor Positioning Strategy

**User Story:** 作为规则架构师，我希望配置基于锚点的相对位置提取策略，以便准确提取固定格式文档中的字段

#### Acceptance Criteria

1. THE IDP_System SHALL 支持配置锚点关键词（如"发票号："、"金额："）
2. THE IDP_System SHALL 支持配置相对位置：右侧、下方、右下方
3. THE IDP_System SHALL 支持配置提取范围：距离锚点的最大字符数或坐标偏移
4. WHERE 页面处理策略为多页模式, THE IDP_System SHALL 仅在包含锚点关键词的页面应用锚点提取逻辑
5. THE IDP_System SHALL 在沙箱测试中高亮显示锚点位置和提取区域
6. WHEN 锚点关键词未找到, THE IDP_System SHALL 记录警告并将字段值设置为空


### Requirement 43: Rule Configuration - Cross-page Table Merging

**User Story:** 作为规则架构师，我希望系统自动合并跨页表格，以便完整提取延伸到多页的表格数据

#### Acceptance Criteria

1. THE IDP_System SHALL 识别跨页表格的表头结构
2. WHEN 表格从第N页延伸到第N+1页, THE IDP_System SHALL 根据表头逻辑自动拼接行数据
3. THE IDP_System SHALL 支持配置表头识别规则（如首行为表头、包含特定关键词）
4. THE IDP_System SHALL 在合并表格时去除重复的表头行
5. THE IDP_System SHALL 在提取结果中保留表格的原始页码信息
6. THE IDP_System SHALL 在沙箱测试中展示合并后的完整表格数据

### Requirement 44: Data Cleaning - Date Format Normalization

**User Story:** 作为规则架构师，我希望配置日期格式标准化规则，以便将不同格式的日期统一为标准格式

#### Acceptance Criteria

1. THE IDP_System SHALL 支持识别多种日期格式（如"2025-12-14"、"2025/12/14"、"14-12-2025"、"2025年12月14日"）
2. THE IDP_System SHALL 支持配置目标日期格式（如"YYYY-MM-DD"、"YYYY/MM/DD"）
3. THE IDP_System SHALL 在清洗管道中提供日期格式化操作
4. WHEN 日期格式无法识别, THE IDP_System SHALL 保留原始值并记录警告
5. THE IDP_System SHALL 在沙箱测试中展示格式化前后的日期值对比

### Requirement 45: Validation - Custom JavaScript Expression

**User Story:** 作为规则架构师，我希望使用自定义JavaScript表达式进行复杂校验，以便实现业务逻辑验证

#### Acceptance Criteria

1. THE IDP_System SHALL 支持在校验规则中配置JavaScript表达式
2. THE IDP_System SHALL 在表达式中提供字段值的访问方式（如fields.amount、fields.count）
3. THE IDP_System SHALL 支持常用的数学运算和逻辑判断
4. WHEN 表达式执行结果为false, THE IDP_System SHALL 将任务状态设置为Pending Audit并记录校验失败原因
5. THE IDP_System SHALL 限制表达式执行时间不超过100毫秒，防止恶意代码
6. THE IDP_System SHALL 在沙箱测试中展示表达式的执行结果和中间变量值

### Requirement 46: Enhancement - Backup OCR Engine Fallback

**User Story:** 作为系统，我希望在主OCR引擎识别结果为空时自动使用备用引擎，以便提高识别成功率

#### Acceptance Criteria

1. WHERE 自动增强功能启用, WHEN 主OCR引擎识别结果为空, THE IDP_System SHALL 自动调用备用OCR引擎
2. THE IDP_System SHALL 支持配置备用OCR引擎（如主引擎为PaddleOCR，备用为Tesseract）
3. THE IDP_System SHALL 在任务日志中记录使用备用引擎的情况
4. THE IDP_System SHALL 在任务详情中标注"使用备用OCR引擎"
5. WHERE 备用引擎也返回空结果, THE IDP_System SHALL 将任务状态设置为Pending Audit


### Requirement 47: Consistency Check - OCR vs LLM Comparison

**User Story:** 作为规则架构师，我希望启用OCR和LLM结果一致性校验，以便在结果差异过大时触发人工审核

#### Acceptance Criteria

1. WHERE 一致性校验启用, THE IDP_System SHALL 同时执行OCR提取和LLM提取
2. THE IDP_System SHALL 支持配置差异阈值（如字符串相似度<80%视为不一致）
3. THE IDP_System SHALL 使用编辑距离算法计算两个结果的相似度
4. WHEN 相似度低于配置阈值, THE IDP_System SHALL 将任务状态设置为Pending Audit
5. THE IDP_System SHALL 在审核工作台中同时展示OCR结果和LLM结果供人工判断
6. THE IDP_System SHALL 在任务详情中记录一致性校验的相似度分数

### Requirement 48: Circuit Breaker - LLM Service Degradation

**User Story:** 作为系统，我希望在LLM服务异常时自动降级为纯OCR模式，以便保证系统可用性

#### Acceptance Criteria

1. THE IDP_System SHALL 监控LLM服务的响应时间和错误率
2. WHEN LLM接口响应时间超过60秒, THE IDP_System SHALL 自动降级为纯OCR模式
3. WHEN LLM接口返回5xx错误, THE IDP_System SHALL 自动降级为纯OCR模式
4. THE IDP_System SHALL 在日志中标记"Warning: LLM Fallback"
5. THE IDP_System SHALL 在任务详情中标注"LLM服务降级"
6. THE IDP_System SHALL 每5分钟尝试恢复LLM服务调用，直到服务正常

### Requirement 49: Account Management - User CRUD Operations

**User Story:** 作为超级管理员，我希望管理用户账号，以便控制系统访问权限

#### Acceptance Criteria

1. THE IDP_System SHALL 提供用户管理界面，支持创建、编辑、删除、禁用用户
2. THE IDP_System SHALL 在创建用户时要求输入用户名、邮箱、角色和初始密码
3. THE IDP_System SHALL 使用bcrypt算法加密存储用户密码
4. THE IDP_System SHALL 支持为用户分配Admin、Architect、Auditor、Visitor四种角色之一
5. THE IDP_System SHALL 在用户列表中展示用户名、邮箱、角色、状态、创建时间、最后登录时间
6. THE IDP_System SHALL 支持按用户名、邮箱、角色筛选用户列表

### Requirement 50: API Key Management - Generation and Revocation

**User Story:** 作为API访客，我希望生成和管理API Key，以便安全地调用系统API

#### Acceptance Criteria

1. THE IDP_System SHALL 支持用户生成新的API Key
2. THE IDP_System SHALL 为每个API Key生成唯一的Key ID和Secret
3. THE IDP_System SHALL 在生成API Key时仅显示一次完整的Secret，之后仅显示部分字符
4. THE IDP_System SHALL 支持为API Key配置有效期（如30天、90天、永久）
5. THE IDP_System SHALL 支持手动撤销（禁用）API Key
6. THE IDP_System SHALL 在API Key列表中展示Key ID、创建时间、有效期、状态、最后使用时间
7. WHEN API Key过期或被撤销, THE IDP_System SHALL 拒绝使用该Key的API请求


### Requirement 51: Audit Log - Comprehensive Operation Tracking

**User Story:** 作为系统管理员，我希望查看完整的操作审计日志，以便追溯系统变更和用户行为

#### Acceptance Criteria

1. THE IDP_System SHALL 记录所有用户操作，包含登录、登出、配置变更、规则发布、任务审核等
2. THE IDP_System SHALL 在审计日志中记录操作人、操作时间、操作类型、操作对象、变更前后内容、IP地址
3. THE IDP_System SHALL 提供审计日志查询界面，支持按时间范围、用户、操作类型筛选
4. THE IDP_System SHALL 支持导出审计日志为CSV格式
5. THE IDP_System SHALL 确保审计日志不可被修改或删除
6. THE IDP_System SHALL 保留审计日志至少90天

### Requirement 52: Notification System - Task Status Alerts

**User Story:** 作为系统用户，我希望在任务状态变更时收到通知，以便及时处理异常情况

#### Acceptance Criteria

1. THE IDP_System SHALL 支持配置通知规则（如推送失败时通知管理员）
2. THE IDP_System SHALL 支持邮件通知方式
3. THE IDP_System SHALL 在任务进入死信队列时发送通知
4. THE IDP_System SHALL 在任务处理超时时发送通知
5. THE IDP_System SHALL 支持配置通知接收人列表
6. THE IDP_System SHALL 在通知中包含任务ID、文件名、异常原因和处理建议

### Requirement 53: System Configuration - Global Settings

**User Story:** 作为超级管理员，我希望配置系统全局参数，以便调整系统行为

#### Acceptance Criteria

1. THE IDP_System SHALL 提供全局配置界面，包含OCR超时时间、LLM超时时间、最大并行任务数等参数
2. THE IDP_System SHALL 支持配置默认的文件留存期和数据留存期
3. THE IDP_System SHALL 支持配置LLM Token单价用于成本估算
4. THE IDP_System SHALL 支持配置消息队列的最大长度
5. THE IDP_System SHALL 在配置变更后立即生效，无需重启服务
6. THE IDP_System SHALL 记录所有配置变更到审计日志

### Requirement 54: PDF Processing - Image Conversion

**User Story:** 作为系统，我希望将PDF页面转换为图片，以便支持图片格式的OCR引擎

#### Acceptance Criteria

1. THE IDP_System SHALL 使用pdf2image库将PDF页面转换为图片
2. THE IDP_System SHALL 支持配置图片输出格式（PNG、JPEG）和DPI（默认300）
3. THE IDP_System SHALL 在转换图片后临时存储到本地，OCR完成后自动清理
4. WHERE OCR引擎要求图片输入, THE IDP_System SHALL 自动执行PDF到图片的转换
5. THE IDP_System SHALL 在转换失败时记录详细错误信息并将任务状态设置为Failed


### Requirement 55: Task Status - Complete State Machine

**User Story:** 作为系统，我希望实现完整的任务状态流转机制，以便准确跟踪任务生命周期

#### Acceptance Criteria

1. THE IDP_System SHALL 支持以下任务状态：Queued、Processing、Pending Audit、Completed、Rejected、Pushing、Push Success、Push Failed
2. THE IDP_System SHALL 确保任务状态按照定义的流转规则变更
3. THE IDP_System SHALL 在数据库中记录每次状态变更的时间戳
4. THE IDP_System SHALL 支持查询任务的完整状态变更历史
5. THE IDP_System SHALL 在任务详情中展示状态流转时间线
6. THE IDP_System SHALL 计算任务在每个状态的停留时长

### Requirement 56: Regex Extraction - Global Search Support

**User Story:** 作为规则架构师，我希望使用正则表达式进行全文搜索，以便提取文档中的所有匹配项

#### Acceptance Criteria

1. THE IDP_System SHALL 支持配置正则表达式用于字段提取
2. THE IDP_System SHALL 在Global_Context_String中执行正则匹配
3. THE IDP_System SHALL 支持提取第一个匹配项或所有匹配项
4. THE IDP_System SHALL 支持正则表达式的捕获组功能
5. THE IDP_System SHALL 支持跨页正则匹配（匹配跨越页面分隔符的文本）
6. THE IDP_System SHALL 在沙箱测试中高亮显示所有正则匹配结果

### Requirement 57: LLM Extraction - Context Scope Configuration

**User Story:** 作为规则架构师，我希望配置LLM提取的上下文范围，以便控制输入Token数量和提取精度

#### Acceptance Criteria

1. THE IDP_System SHALL 支持三种Context Scope：全文（All Pages）、指定坐标区域、前N页
2. WHERE Context Scope为全文, THE IDP_System SHALL 将完整的Global_Context_String作为LLM输入
3. WHERE Context Scope为指定坐标区域, THE IDP_System SHALL 仅提取指定区域的OCR文本作为LLM输入
4. WHERE Context Scope为前N页, THE IDP_System SHALL 仅提取前N页的合并文本作为LLM输入
5. THE IDP_System SHALL 在LLM请求中包含自定义Prompt和上下文文本
6. THE IDP_System SHALL 在任务详情中记录LLM提取使用的上下文范围和Token数

### Requirement 58: Data Type Support - Decimal and Boolean

**User Story:** 作为规则架构师，我希望支持更多数据类型，以便准确表示不同类型的字段值

#### Acceptance Criteria

1. THE IDP_System SHALL 在字段类型中支持String、Int、Date、Decimal、Boolean五种类型
2. WHERE 字段类型为Decimal, THE IDP_System SHALL 支持配置小数位数（如保留2位小数）
3. WHERE 字段类型为Boolean, THE IDP_System SHALL 支持配置真值表示（如"是"、"Yes"、"1"表示true）
4. THE IDP_System SHALL 在数据清洗阶段执行类型转换
5. WHEN 类型转换失败, THE IDP_System SHALL 记录警告并将任务状态设置为Pending Audit
6. THE IDP_System SHALL 在审核工作台中根据字段类型展示相应的输入控件（如日期选择器、数字输入框、复选框）


### Requirement 59: Dashboard - Human Intervention Rate

**User Story:** 作为系统管理员，我希望在规则效能Top10中查看人工干预率，以便识别需要优化的规则

#### Acceptance Criteria

1. THE IDP_System SHALL 计算每个规则的人工干预率为（Pending Audit任务数 / 总任务数）* 100%
2. THE IDP_System SHALL 在规则效能Top10列表中展示规则名称、任务量、平均耗时和人工干预率
3. THE IDP_System SHALL 按任务量降序排列规则列表
4. THE IDP_System SHALL 使用颜色标识人工干预率等级：低（绿色，<10%）、中（黄色，10-30%）、高（红色，>30%）
5. THE IDP_System SHALL 支持点击规则名称跳转到该规则的任务列表

### Requirement 60: Exception Distribution - Detailed Breakdown

**User Story:** 作为系统管理员，我希望查看详细的异常原因分布，以便针对性地解决问题

#### Acceptance Criteria

1. THE IDP_System SHALL 统计以下异常类型的数量：OCR识别空、必填校验失败、格式校验失败、LLM不一致、下游接口错误、处理超时
2. THE IDP_System SHALL 在异常分布饼图中展示各类异常的占比
3. THE IDP_System SHALL 支持点击饼图扇区查看该类异常的详细任务列表
4. THE IDP_System SHALL 在异常详情中展示异常原因、影响的字段和建议的解决方案
5. THE IDP_System SHALL 支持按时间范围筛选异常分布统计

### Requirement 61: Webhook Template - Variable Injection

**User Story:** 作为系统管理员，我希望在Webhook请求体模版中使用变量注入，以便灵活定制推送数据格式

#### Acceptance Criteria

1. THE IDP_System SHALL 支持在请求体模版中使用{{task_id}}、{{result_json}}、{{file_url}}、{{meta_info}}四种变量
2. THE IDP_System SHALL 在推送前将变量替换为实际值
3. WHERE 变量为{{result_json}}, THE IDP_System SHALL 将提取结果的完整JSON对象注入
4. WHERE 变量为{{file_url}}, THE IDP_System SHALL 注入原始文件的预签名URL
5. WHERE 变量为{{meta_info}}, THE IDP_System SHALL 注入任务元信息（如规则名称、处理耗时、页数）
6. THE IDP_System SHALL 在模版编辑器中提供变量插入辅助功能

### Requirement 62: Retention Policy - Scheduled Cleanup Task

**User Story:** 作为系统，我希望定时执行数据清理任务，以便自动管理存储空间

#### Acceptance Criteria

1. THE IDP_System SHALL 每日凌晨02:00执行定时清理任务
2. THE IDP_System SHALL 查询创建时间超过配置留存期的文件记录
3. THE IDP_System SHALL 仅删除任务状态为Completed或Rejected的文件
4. THE IDP_System SHALL 从MinIO对象存储中删除过期文件
5. THE IDP_System SHALL 在数据库中更新文件记录的删除状态
6. THE IDP_System SHALL 在清理日志中记录删除的文件数量、释放的存储空间和执行耗时
7. WHEN 清理任务执行失败, THE IDP_System SHALL 发送通知给系统管理员


### Requirement 63: Frontend - Responsive Design

**User Story:** 作为系统用户，我希望在不同设备上都能正常使用系统，以便随时随地处理任务

#### Acceptance Criteria

1. THE IDP_System SHALL 使用响应式设计，支持桌面端（1920x1080）、平板端（1024x768）和移动端（375x667）
2. THE IDP_System SHALL 在移动端自动调整布局，将左右分栏改为上下布局
3. THE IDP_System SHALL 确保所有按钮和交互元素在触摸屏上易于操作（最小点击区域44x44px）
4. THE IDP_System SHALL 在小屏幕设备上隐藏次要信息，保留核心功能
5. THE IDP_System SHALL 使用Tailwind CSS的响应式工具类实现自适应布局

### Requirement 64: Frontend - Loading States and Feedback

**User Story:** 作为系统用户，我希望在操作过程中看到清晰的加载状态和反馈，以便了解系统正在处理

#### Acceptance Criteria

1. THE IDP_System SHALL 在数据加载时展示加载动画（Spinner或骨架屏）
2. THE IDP_System SHALL 在文件上传时展示上传进度条
3. THE IDP_System SHALL 在操作成功后展示成功提示（Toast通知，3秒后自动消失）
4. THE IDP_System SHALL 在操作失败后展示错误提示（Toast通知，包含错误信息和建议操作）
5. THE IDP_System SHALL 在长时间操作（如沙箱测试）时展示进度提示
6. THE IDP_System SHALL 在按钮点击后禁用按钮，防止重复提交

### Requirement 65: Backend - Database Connection Pool

**User Story:** 作为系统架构师，我希望使用数据库连接池，以便提高数据库访问性能

#### Acceptance Criteria

1. THE IDP_System SHALL 使用SQLAlchemy的连接池功能
2. THE IDP_System SHALL 配置连接池最小连接数为5，最大连接数为20
3. THE IDP_System SHALL 配置连接超时时间为30秒
4. THE IDP_System SHALL 配置连接回收时间为3600秒，防止连接长时间占用
5. THE IDP_System SHALL 在连接池耗尽时等待可用连接，最长等待10秒
6. THE IDP_System SHALL 监控连接池使用情况，在连接数接近上限时记录警告日志

### Requirement 66: Backend - API Rate Limiting

**User Story:** 作为系统架构师，我希望实现API限流，以便防止恶意请求和保护系统资源

#### Acceptance Criteria

1. THE IDP_System SHALL 对每个API Key实施限流策略
2. THE IDP_System SHALL 限制单个API Key每分钟最多调用100次上传接口
3. THE IDP_System SHALL 限制单个API Key每分钟最多调用1000次查询接口
4. WHEN 超过限流阈值, THE IDP_System SHALL 返回429 Too Many Requests错误
5. THE IDP_System SHALL 在响应头中包含限流信息（X-RateLimit-Limit、X-RateLimit-Remaining、X-RateLimit-Reset）
6. THE IDP_System SHALL 使用Redis实现分布式限流计数器


### Requirement 67: Docker Deployment - Multi-service Orchestration

**User Story:** 作为运维工程师，我希望使用Docker Compose编排所有服务，以便快速部署和管理系统

#### Acceptance Criteria

1. THE IDP_System SHALL 提供docker-compose.yml文件，包含backend、frontend、mysql、redis、rabbitmq、minio六个服务
2. THE IDP_System SHALL 提供docker-compose.dev.yml文件用于开发环境覆盖配置
3. THE IDP_System SHALL 配置服务间的依赖关系，确保启动顺序正确
4. THE IDP_System SHALL 配置健康检查，确保服务就绪后才接受流量
5. THE IDP_System SHALL 配置数据卷持久化，确保数据不因容器重启而丢失
6. THE IDP_System SHALL 提供.env.example文件，包含所有必需的环境变量示例

### Requirement 68: Database Migration - Alembic Integration

**User Story:** 作为开发工程师，我希望使用Alembic管理数据库版本，以便安全地执行数据库变更

#### Acceptance Criteria

1. THE IDP_System SHALL 使用Alembic作为数据库迁移工具
2. THE IDP_System SHALL 在backend/alembic目录下维护迁移脚本
3. THE IDP_System SHALL 为每次数据库结构变更生成独立的迁移脚本
4. THE IDP_System SHALL 支持向前迁移（upgrade）和回滚（downgrade）操作
5. THE IDP_System SHALL 在迁移脚本中包含详细的变更说明
6. THE IDP_System SHALL 在应用启动时自动执行待执行的迁移脚本

### Requirement 69: Error Handling - Unified Exception Handler

**User Story:** 作为开发工程师，我希望实现统一的异常处理机制，以便标准化错误响应格式

#### Acceptance Criteria

1. THE IDP_System SHALL 实现全局异常处理器，捕获所有未处理的异常
2. THE IDP_System SHALL 返回统一的错误响应格式：{"code": 错误码, "message": 错误信息, "detail": 详细信息}
3. THE IDP_System SHALL 为不同类型的异常定义标准错误码（如400、401、403、404、500）
4. THE IDP_System SHALL 在生产环境隐藏敏感的错误堆栈信息
5. THE IDP_System SHALL 在开发环境返回完整的错误堆栈信息用于调试
6. THE IDP_System SHALL 记录所有异常到日志系统，包含请求上下文信息

### Requirement 70: Testing - Unit Test Coverage

**User Story:** 作为开发工程师，我希望编写单元测试，以便确保代码质量和功能正确性

#### Acceptance Criteria

1. THE IDP_System SHALL 为核心业务逻辑编写单元测试
2. THE IDP_System SHALL 使用pytest作为测试框架
3. THE IDP_System SHALL 为OCR处理、数据提取、数据清洗、校验等模块编写测试用例
4. THE IDP_System SHALL 使用Mock对象模拟外部依赖（如OCR引擎、LLM服务）
5. THE IDP_System SHALL 确保单元测试覆盖率达到70%以上
6. THE IDP_System SHALL 在CI/CD流程中自动执行单元测试

---

## Summary

本需求文档共包含70个功能需求，全面覆盖了企业级智能文档处理平台的所有核心功能和非功能需求：

- **仪表盘与监控**（需求1-2, 37-38, 59-60）：核心指标、可视化图表、成本统计
- **系统配置与安全**（需求3-5, 49-50, 53）：Webhook配置、数据生命周期、RBAC、账号管理、全局配置
- **规则生命周期管理**（需求6-12, 27-28, 34, 39-48, 56-58, 61）：版本控制、编辑器、沙箱测试、提取策略、校验规则、增强功能
- **文档接入与处理**（需求13-15, 29, 35-36, 40, 54-55）：上传接口、去重机制、OCR处理、文本合并、质检
- **审核工作台**（需求16-17, 30, 41）：多页预览、数据修正、草稿保存、置信度展示
- **结果推送与重试**（需求18-19, 31-32）：推送机制、死信队列、指数退避、多目标推送
- **任务管理**（需求20, 33）：任务列表、状态跟踪、坐标信息
- **安全与性能**（需求21-23, 65-66）：认证授权、文件存储、性能指标、连接池、限流
- **日志监控与报表**（需求24-26, 51-52, 62）：操作日志、审计日志、通知系统、数据导出
- **基础设施**（需求63-70）：响应式设计、加载反馈、Docker部署、数据库迁移、异常处理、单元测试

所有需求均遵循EARS格式，包含明确的用户故事和验收标准，为后续的设计和实现提供了清晰的指导。
