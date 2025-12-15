/**
 * Webhook API模块
 * 提供Webhook配置相关的API接口
 */
import request from './request'

/**
 * Webhook API
 */
export const webhookAPI = {
  /**
   * 获取Webhook列表
   * @returns {Promise} Webhook列表数据
   */
  list() {
    return request.get('/v1/webhooks')
  },

  /**
   * 获取Webhook详情
   * @param {string} webhookId - Webhook ID
   * @returns {Promise} Webhook详情数据
   */
  get(webhookId) {
    return request.get(`/v1/webhooks/${webhookId}`)
  },

  /**
   * 创建Webhook
   * @param {object} data - Webhook配置数据
   * @param {string} data.name - 系统名称
   * @param {string} data.endpoint_url - 回调URL
   * @param {string} data.auth_type - 鉴权方式
   * @param {object} data.auth_config - 鉴权配置
   * @param {string} data.secret_key - 签名密钥
   * @param {object} data.request_template - 请求体模版
   * @returns {Promise} 创建结果
   */
  create(data) {
    return request.post('/v1/webhooks', data)
  },

  /**
   * 更新Webhook
   * @param {string} webhookId - Webhook ID
   * @param {object} data - 更新的Webhook配置数据
   * @returns {Promise} 更新结果
   */
  update(webhookId, data) {
    return request.put(`/v1/webhooks/${webhookId}`, data)
  },

  /**
   * 删除Webhook
   * @param {string} webhookId - Webhook ID
   * @returns {Promise} 删除结果
   */
  delete(webhookId) {
    return request.delete(`/v1/webhooks/${webhookId}`)
  },

  /**
   * 测试Webhook连通性
   * @param {string} webhookId - Webhook ID
   * @returns {Promise} 测试结果（包含状态码、响应头、响应体）
   */
  test(webhookId) {
    return request.post(`/v1/webhooks/${webhookId}/test`, {}, {
      timeout: 10000 // 10秒超时
    })
  },

  /**
   * 获取规则关联的Webhook列表
   * @param {string} ruleId - 规则ID
   * @returns {Promise} Webhook列表
   */
  getRuleWebhooks(ruleId) {
    return request.get(`/v1/rules/${ruleId}/webhooks`)
  },

  /**
   * 关联规则和Webhook
   * @param {string} ruleId - 规则ID
   * @param {string} webhookId - Webhook ID
   * @returns {Promise} 关联结果
   */
  associateRule(ruleId, webhookId) {
    return request.post(`/v1/rules/${ruleId}/webhooks`, { webhook_id: webhookId })
  },

  /**
   * 解除规则和Webhook关联
   * @param {string} ruleId - 规则ID
   * @param {string} webhookId - Webhook ID
   * @returns {Promise} 解除关联结果
   */
  disassociateRule(ruleId, webhookId) {
    return request.delete(`/v1/rules/${ruleId}/webhooks/${webhookId}`)
  }
}


/**
 * 导出独立函数（兼容 WebhookConfig.vue 的导入方式）
 */
export function getWebhookList() {
  return webhookAPI.list()
}

export function getWebhook(webhookId) {
  return webhookAPI.get(webhookId)
}

export function getWebhookDetail(webhookId) {
  return webhookAPI.get(webhookId)
}

export function createWebhook(data) {
  return webhookAPI.create(data)
}

export function updateWebhook(webhookId, data) {
  return webhookAPI.update(webhookId, data)
}

export function deleteWebhook(webhookId) {
  return webhookAPI.delete(webhookId)
}

export function testWebhook(webhookId) {
  return webhookAPI.test(webhookId)
}
