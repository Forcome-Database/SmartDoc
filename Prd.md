---

# 产品需求文档：智能文档处理 (IDP) 平台 V3.1.1

| 文档属性 | 详细信息 |
| :--- | :--- |
| **文档版本** | **V3.1.1 (Multi-page Support)** |
| **项目名称** | 企业级智能文档处理中台 (Enterprise IDP Platform) |
| **文档状态** | **已锁定 (Ready for Dev)** |
| **最后更新** | 2025-12-14 |
| **修订人** | 产品架构组 |
| **核心目标** | 构建高可用、可溯源、智能化的文档处理中台，支持**单页及多页长文档**的自动化解析，实现从规则定义、合并提取、人机协同审核到下游安全推送的全链路闭环。 |

---

## 1. 全局仪表盘 (Dashboard)

### 1.1 核心指标卡 (Key Metrics)
需支持按时间范围（今日、近7天、近30天）筛选：
*   **总接单量**：系统累计接收的文档请求总数。
*   **累计处理文件/页数 (Total Pages)**：**[新增]** 统计实际消耗的 OCR 页数（用于精确计算算力成本）。
*   **处理中 (Processing)**：当前队列中排队 + 正在计算（OCR/LLM）的任务数。
*   **待人工审核 (Pending Audit)**：因置信度低、逻辑校验失败或 LLM 不一致，阻塞在工作台等待人工介入的任务数。
*   **推送异常 (Push Error)**：**[红色预警]** 进入“死信队列”或多次重试仍失败的任务数。
*   **平均直通率 (STP)**：无需人工介入，直接处理成功并推送的比例（目标 > 90%）。
*   **算力节省**：通过“哈希秒传”机制命中缓存，跳过计算所节省的预估总耗时。
*   **LLM 消耗估算**：本周期内累计消耗的 Token 数及预估费用（用于成本监控）。

### 1.2 可视化图表
*   **任务吞吐趋势**：堆叠柱状图，展示每日的 [成功]、[待审核]、[失败]、[驳回] 数量。
*   **规则效能 Top10**：按任务量排名的规则列表，包含“平均耗时”和“人工干预率”。
*   **异常分布**：饼图，展示异常原因占比（如：OCR识别空、必填校验失败、LLM不一致、下游接口500）。

---

## 2. 基础配置与安全 (System Foundation)

### 2.1 目标系统配置 (Webhook & Security)
**功能目标**：统一管理下游业务系统的回调接口，确保数据传输的安全性与标准化。
*   **配置字段**：
    *   `系统名称`：标识（如“SAP 财务系统”）。
    *   `Endpoint URL`：完整的接收地址。
    *   `鉴权方式`：No Auth / Basic Auth / Bearer Token / API Key。
    *   **`安全签名 (HMAC Signature)`**：配置一个 `Secret Key`。系统在推送时，将使用 `HMAC-SHA256(RequestBody, SecretKey)` 生成签名，放入 Header `X-IDP-Signature` 中，供下游校验请求来源合法性。
    *   `请求体模版`：JSON 编辑器，支持变量注入：`{{task_id}}`, `{{result_json}}`, `{{file_url}}`, `{{meta_info}}`。
*   **连通性测试**：点击 [发送测试]，系统使用 Mock 数据发送一次请求，并展示响应结果。

### 2.2 数据生命周期 (Retention Policy)
**功能目标**：平衡存储成本与合规审计需求。
*   **策略配置**：
    *   `原始文件留存期`：设置 PDF/图片在对象存储中的保留天数（默认 30 天）。过期自动清理。
    *   `提取数据留存期`：设置解析后的 JSON 结果保留天数（默认永久）。
*   **执行机制**：每日凌晨 02:00 触发定时任务执行清理。

### 2.3 角色权限管理 (RBAC)
**功能目标**：实现职责分离，保障配置与数据安全。
*   **超级管理员 (Admin)**：全权限，负责 2.1、2.2 配置及账号管理。
*   **规则架构师 (Architect)**：负责“规则管理”模块，能够创建、编辑、发布、回滚规则，使用沙箱测试。
*   **业务审核员 (Auditor)**：**仅拥有“审核工作台”权限**，负责处理 Pending 状态的任务，不可修改规则。
*   **API 访客 (Visitor)**：仅能生成和查看 API Key，用于系统对接。

---

## 3. 规则全生命周期管理 (Rule Lifecycle)
**核心模块**：引入版本控制与沙箱机制，避免生产环境配置事故。

### 3.1 规则列表与版本控制
*   **基本属性**：规则名称、编码、文档类型、OCR 引擎。
*   **版本管理 (Versioning)**：
    *   **草稿 (Draft)**：正在编辑中的版本，不影响线上业务。
    *   **已发布 (Published/Active)**：线上生产环境正在使用的版本。
    *   **历史版本 (Archived)**：历史发布的快照。
*   **操作流**：新建规则 -> 编辑草稿 -> **沙箱测试通过** -> 发布上线 (生成 V1.0) -> 再次编辑 (生成 V1.1 草稿)。
*   **回滚**：支持将“当前发布版”回退至任一“历史版本”。

### 3.2 规则配置编辑器 (Rule Editor)

#### 3.2.1 基础与引擎
*   `OCR 引擎`：PaddleOCR / Tesseract / UmiOCR。
*   `语言`：中/英/混排。
*   **`页面处理策略 (Page Strategy)`**：**[新增]**
    *   **单页模式**：仅处理 PDF 第一页（适用于封面或单据）。
    *   **多页合并模式**：处理所有页面，并将 OCR 结果按页码顺序合并为一个长文本流，供后续提取使用。
    *   **指定页码**：仅处理指定页（如 "Page 1-3" 或 "Last Page"）。
*   **沙箱测试 (Dry Run)**：
    *   **入口**：编辑器顶部常驻 [运行测试] 按钮。
    *   **交互**：上传本地样张 -> 实时运行当前配置 -> 展示 JSON 结果与 OCR 标注。
    *   **多页支持**：若上传多页 PDF，沙箱需展示**合并后的 OCR 纯文本预览**，方便调试跨页正则。

#### 3.2.2 字段模型 (Schema Definition)
定义目标 JSON 结构，支持深层嵌套。
*   **节点类型**：Object (对象), Array (数组), Table (明细表), Field (原子字段)。
*   **字段属性**：
    *   `Key` (字段名), `Label` (显示名), `Type` (String/Int/Date/Decimal)。
    *   `默认值 (Default Value)`：若提取结果为空且非必填，自动填充该值。
    *   `置信度阈值 (Confidence Threshold)`：字段级独立阈值（如发票号 90%，备注 40%）。

#### 3.2.3 提取策略 (Extraction Strategy)
*   **上下文定义 (Context Definition)**：**[核心逻辑]**
    *   所有的提取操作（正则/LLM）默认基于 **"Merged OCR Text"**（合并后的全文）进行。
    *   系统在合并页面文本时，会在页与页之间插入换行符 `\n` 或自定义分隔符，防止跨页词汇粘连。
*   **锚点定位 (Anchor)**：基于相对位置提取。在多页模式下，锚点逻辑仅在包含该锚点关键词的页面生效。
*   **正则提取 (Regex)**：全文正则匹配（Global Search）。支持跨页匹配。
*   **表格提取 (Table)**：支持**跨页表格合并**（当表格从第1页延伸到第2页时，根据表头逻辑自动拼接行数据）。
*   **LLM 智能提取**：
    *   `Prompt`：自定义提示词（如“提取甲方名称，去除有限公司后缀”）。
    *   `Context Scope`：全文 (All Pages) / 指定坐标区域 / 前 N 页。

#### 3.2.4 清洗与校验 (Validation)
*   **清洗管道**：正则替换 (Replace), 去空 (Trim), 格式化 (Date Format)。
*   **校验规则**：必填校验、正则格式校验 (Email/Phone)、数值范围校验。
*   **自定义脚本**：支持简单的 JavaScript 表达式（如 `amount * count == total`）。

#### 3.2.5 智能增强与风控 (Enhancement & Risk Control)
*   **自动增强**：当 OCR 结果为空时，自动重试备用引擎或调用 LLM 补全。
*   **一致性校验**：开启后，同时运行 OCR 和 LLM，对比结果。若差异过大，强制转人工。
*   **成本熔断 (Circuit Breaker)**：
    *   `Token Limit`：单次任务允许的最大 Token 数。
    *   `服务降级`：若 LLM 接口响应 > 60s 或返回 5xx 错误，系统自动**降级为纯 OCR 模式**，并在日志中标记 `Warning: LLM Fallback`。

---

## 4. 文档接入与调度 (Ingestion & Dispatch)

### 4.1 哈希去重机制 V2 (Smart Deduplication)
**逻辑修正**：确保复用结果的准确性，防止跨规则复用。
*   **指纹生成**：`Task_Key = SHA256(File_Binary) + Rule_ID + Rule_Version`。
*   **判定流程**：
    1.  计算当前上传文件的 `Task_Key`。
    2.  查询数据库：是否存在 `Task_Key` 相同且 `Status = Completed` 的历史记录？
    3.  **命中 (Hit)**：
        *   直接复制历史记录的 `result_json`。
        *   标记任务类型为 `instant (秒传)`。
        *   跳过 OCR/LLM 计算，直接进入“结果推送”环节。
    4.  **未命中 (Miss)**：
        *   生成新任务，文件上传至对象存储，进入消息队列。

### 4.2 队列与存储
*   **消息队列**：采用 RabbitMQ / Redis Stream (持久化模式)，确保服务重启不丢单。
*   **文件存储**：对接 S3 协议存储（AWS S3 / MinIO / Aliyun OSS）。

### 4.3 接入接口
*   **API 参数**：除文件外，必须指定 `rule_id`。可选 `rule_version`（默认 latest）。

---

## 5. 任务处理中心 (Processing Center)

### 5.1 任务全景列表
*   **列表字段**：任务ID、文件名、**页数**、规则版本、**置信度 (色块区分)**、状态、耗时、创建时间。
*   **状态流转**：
    *   `Queued` -> `Processing` -> `Pending Audit` (异常/低置信度)
    *   `Pending Audit` -> `Completed` (人工通过) OR `Rejected` (人工驳回)
    *   `Completed` -> `Pushing` -> `Push Success` OR `Push Failed`

### 5.2 审核工作台 (Workbench) - 交互增强
**功能目标**：提供高效的人机协同修正环境，适配多页浏览。
*   **布局**：左侧 PDF 预览（支持缩放/旋转），右侧结构化表单。
*   **左侧 PDF 预览交互**：**[新增]**
    *   **分页器**：顶部增加 [上一页] [下一页] [跳转] 及页码显示 (如 1/15)。
    *   **懒加载**：针对超大 PDF (50页+)，采用按需加载图片切片，保证前端性能。
    *   **跨页高亮**：当右侧字段的数据来源于第 5 页时，点击该字段，左侧自动跳转至第 5 页并滚动到对应位置高亮。
*   **核心交互**：
    *   **高亮联动**：光标聚焦右侧某字段时，左侧自动画框高亮对应的 OCR 区域。
    *   **划词回填 (Click-to-Fill)**：支持在左侧任意页面框选文本填入右侧。
    *   **表格操作**：针对 Table 字段，右侧支持 **[插入行]、[删除行]、[上移]、[下移]** 操作。
*   **决策操作**：
    *   **[确认通过]**：保存修正后的数据，状态变更为 `Completed`，触发推送。
    *   **[驳回/作废]**：针对文件错误、模糊不可读的情况。任务结束，状态为 `Rejected`，推送特定错误码。

### 5.3 推送记录与死信管理
*   **推送日志**：记录 HTTP Status, Header (含签名), Request Body, Response Body, 耗时。
*   **死信队列 (DLQ)**：
    *   定义：自动重试 3 次（指数退避算法）后仍失败的任务。
    *   操作：在界面显示“推送异常”列表，支持 **[查看报文]** 和 **[批量重推]**。

---

## 6. 业务逻辑流程图 (Process Logic)

1.  **接收请求**：API/Web 接收文件 -> 校验参数。
2.  **去重判断**：
    *   计算 `SHA256 + Rule + Version`。
    *   *If Hit* -> 读库取结果 -> 标记“秒传” -> 跳转至步骤 7。
    *   *If Miss* -> 文件存 S3 -> 任务入 MQ。
3.  **计算执行 (Worker) - [核心逻辑]**：
    *   MQ 消费 -> 下载文件。
    *   **预处理**：判断文件是单页还是多页。
    *   **循环/并行 OCR**：对文件包含的每一页（或指定页码范围）执行 OCR。
    *   **文本合并 (Text Merge)**：**[关键]** 将所有页面的 OCR 文本结果按页码顺序拼接（String Concatenation），形成 `Global_Context_String`。
    *   **路由提取**：将 `Global_Context_String` 输入提取引擎（正则/Table/LLM）。
    *   *If Configured* -> 执行 LLM 增强/校验 (含熔断保护)。
    *   执行数据清洗。
4.  **自动质检**：
    *   执行必填校验、格式校验。
    *   检查字段置信度是否低于阈值。
    *   *All Pass* -> 状态 `Completed`。
    *   *Any Fail* -> 状态 `Pending Audit` (附带原因)。
5.  **人工干预 (仅针对 Pending)**：
    *   用户进入工作台 -> **翻页查看/修正** -> 提交 -> 状态 `Completed`。
    *   或者 -> 用户点击驳回 -> 状态 `Rejected`。
6.  **结果推送**：
    *   组装 JSON -> 计算 HMAC 签名。
    *   POST 下游系统。
    *   *Success* -> 记录日志。
    *   *Fail* -> 重试 x3 -> 入死信队列。

---

## 7. 非功能需求 (NFR)

1.  **高可用 (HA)**：
    *   服务无状态设计，支持 K8s 水平扩展。
    *   Redis 缓存规则配置，减少 DB 查询压力。
2.  **性能指标**：
    *   API 响应 (Upload)：< 200ms。
    *   秒传响应：< 500ms。
    *   **单页**处理耗时 (OCR Only)：< 3s。
    *   **多页**处理耗时：< `(2s * 页数) + 1s` (合并与提取开销)。需设置最大超时时间 (如 300s)。
3.  **安全性**：
    *   传输加密：全链路 TLS 1.2+。
    *   数据加密：API Key、Secret Key 等敏感字段使用 AES-256 加密存储。

---

## 8. 附录：接口定义 (API Specs)

### 8.1 上传接口
`POST /api/v1/ocr/upload`
*   **Header**: `Authorization: Bearer <token>`
*   **Body (multipart/form-data)**:
    *   `file`: (Binary, **Max 20MB / 50 Pages**)
    *   `rule_id`: (String, Required)
    *   `rule_version`: (String, Optional, default "latest")
*   **Response**:
    ```json
    {
      "code": 200,
      "data": {
        "task_id": "T_20251214_0001",
        "is_instant": false,
        "status": "processing",
        "estimated_wait_seconds": 15 // 根据页数动态计算
      }
    }
    ```

### 8.2 查询结果
`GET /api/v1/ocr/result/{task_id}`
*   **Response**:
    ```json
    {
      "task_id": "T_20251214_0001",
      "status": "pending_audit", // processing, pending_audit, rejected, completed
      "audit_reasons": ["confidence_low:invoice_no", "validation_fail:email"],
      "created_at": "2025-12-14T10:00:00Z",
      "page_count": 3, // 实际处理页数
      "result": {
          "invoice_no": "NO.123456",
          "amount": 100.50
      },
      "push_log": {
          "status": "pending",
          "retry_count": 0
      }
    }
    ```