# 产品概述

## 智能文档处理中台

高可用、可溯源的文档处理平台，支持单页及多页文档自动化解析，实现规则定义→数据提取→人工审核→安全推送的全链路闭环。

## 核心能力

| 功能 | 说明 |
|------|------|
| 文档处理 | PDF/图片，最大20MB/50页 |
| OCR引擎 | PaddleOCR(主) / Tesseract(备) / UmiOCR |
| 智能去重 | SHA256哈希秒传 |
| 数据提取 | 正则 / 锚点定位 / 表格 / LLM智能提取 |
| 人工审核 | 多页PDF预览、OCR高亮、划词回填 |
| 安全推送 | HMAC-SHA256签名、重试机制、死信队列 |
| 规则引擎 | 版本控制、沙箱测试、热更新 |

## 性能指标

- API响应: < 200ms
- 单页OCR: < 3s
- 直通率(STP): > 90%

## 用户角色

| 角色 | 权限 |
|------|------|
| Admin | 全部权限，用户管理 |
| Architect | 规则创建/编辑/发布/沙箱测试 |
| Auditor | 审核工作台，不可修改规则 |
| Visitor | 仅API Key生成和查看 |

## 任务状态流转

```
queued → processing → pending_audit → completed → pushing → push_success
                   ↓                ↓
                 failed          rejected
                                    ↓
                              push_failed
```
