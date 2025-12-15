// Task Status Constants
export const TASK_STATUS = {
  QUEUED: 'queued',
  PROCESSING: 'processing',
  PENDING_AUDIT: 'pending_audit',
  COMPLETED: 'completed',
  REJECTED: 'rejected',
  PUSHING: 'pushing',
  PUSH_SUCCESS: 'push_success',
  PUSH_FAILED: 'push_failed',
  FAILED: 'failed'
}

// Task Status Labels (Chinese)
export const TASK_STATUS_LABELS = {
  [TASK_STATUS.QUEUED]: '排队中',
  [TASK_STATUS.PROCESSING]: '处理中',
  [TASK_STATUS.PENDING_AUDIT]: '待审核',
  [TASK_STATUS.COMPLETED]: '已完成',
  [TASK_STATUS.REJECTED]: '已驳回',
  [TASK_STATUS.PUSHING]: '推送中',
  [TASK_STATUS.PUSH_SUCCESS]: '推送成功',
  [TASK_STATUS.PUSH_FAILED]: '推送失败',
  [TASK_STATUS.FAILED]: '失败'
}

// Task Status Colors
export const TASK_STATUS_COLORS = {
  [TASK_STATUS.QUEUED]: 'default',
  [TASK_STATUS.PROCESSING]: 'processing',
  [TASK_STATUS.PENDING_AUDIT]: 'warning',
  [TASK_STATUS.COMPLETED]: 'success',
  [TASK_STATUS.REJECTED]: 'error',
  [TASK_STATUS.PUSHING]: 'processing',
  [TASK_STATUS.PUSH_SUCCESS]: 'success',
  [TASK_STATUS.PUSH_FAILED]: 'error',
  [TASK_STATUS.FAILED]: 'error'
}

// User Roles
export const USER_ROLES = {
  ADMIN: 'admin',
  ARCHITECT: 'architect',
  AUDITOR: 'auditor',
  VISITOR: 'visitor'
}

// User Role Labels (Chinese)
export const USER_ROLE_LABELS = {
  [USER_ROLES.ADMIN]: '超级管理员',
  [USER_ROLES.ARCHITECT]: '规则架构师',
  [USER_ROLES.AUDITOR]: '业务审核员',
  [USER_ROLES.VISITOR]: 'API访客'
}

// Rule Status
export const RULE_STATUS = {
  DRAFT: 'draft',
  PUBLISHED: 'published',
  ARCHIVED: 'archived'
}

// Rule Status Labels (Chinese)
export const RULE_STATUS_LABELS = {
  [RULE_STATUS.DRAFT]: '草稿',
  [RULE_STATUS.PUBLISHED]: '已发布',
  [RULE_STATUS.ARCHIVED]: '已归档'
}

// Confidence Levels
export const CONFIDENCE_LEVELS = {
  HIGH: { min: 80, max: 100, label: '高', color: 'success' },
  MEDIUM: { min: 50, max: 80, label: '中', color: 'warning' },
  LOW: { min: 0, max: 50, label: '低', color: 'error' }
}

// OCR Engines
export const OCR_ENGINES = {
  PADDLEOCR: 'paddleocr',
  TESSERACT: 'tesseract',
  UMIOCR: 'umiocr'
}

// OCR Engine Labels
export const OCR_ENGINE_LABELS = {
  [OCR_ENGINES.PADDLEOCR]: 'PaddleOCR',
  [OCR_ENGINES.TESSERACT]: 'Tesseract',
  [OCR_ENGINES.UMIOCR]: 'UmiOCR'
}

// Data Types
export const DATA_TYPES = {
  STRING: 'string',
  INT: 'int',
  DATE: 'date',
  DECIMAL: 'decimal',
  BOOLEAN: 'boolean'
}

// Extraction Types
export const EXTRACTION_TYPES = {
  REGEX: 'regex',
  ANCHOR: 'anchor',
  TABLE: 'table',
  LLM: 'llm'
}

// Auth Types for Webhooks
export const AUTH_TYPES = {
  NONE: 'none',
  BASIC: 'basic',
  BEARER: 'bearer',
  API_KEY: 'api_key'
}

// Auth Type Labels
export const AUTH_TYPE_LABELS = {
  [AUTH_TYPES.NONE]: '无认证',
  [AUTH_TYPES.BASIC]: 'Basic Auth',
  [AUTH_TYPES.BEARER]: 'Bearer Token',
  [AUTH_TYPES.API_KEY]: 'API Key'
}
