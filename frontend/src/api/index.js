/**
 * API模块统一导出
 * 提供所有API接口的统一入口
 */

// 导出request实例
export { default as request } from './request'

// 导出所有API模块
export { authAPI } from './auth'
export { taskAPI } from './task'
export { ruleAPI, ruleAPI as ruleApi } from './rule'
export { dashboardAPI } from './dashboard'
export { auditAPI } from './audit'
export { webhookAPI } from './webhook'
export { userAPI } from './user'
export { systemAPI } from './system'
export { auditLogAPI } from './auditLog'
export { default as pipelineApi } from './pipeline'
