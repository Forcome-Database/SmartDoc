import request from './request'

/**
 * 系统配置API
 */
export const systemAPI = {
  /**
   * 获取所有系统配置
   * @returns {Promise} 系统配置列表
   */
  getConfigs() {
    return request.get('/v1/system/config')
  },

  /**
   * 更新系统配置
   * @param {string} key - 配置键
   * @param {any} value - 配置值
   * @returns {Promise} 更新结果
   */
  updateConfig(key, value) {
    return request.put(`/v1/system/config/${key}`, { value })
  },

  /**
   * 获取数据生命周期配置
   * @returns {Promise} 留存期配置
   */
  getRetentionConfig() {
    return request.get('/v1/system/retention')
  },

  /**
   * 更新数据生命周期配置
   * @param {object} data - 留存期配置
   * @param {number} data.file_retention_days - 文件留存天数
   * @param {number} data.data_retention_days - 数据留存天数（-1表示永久）
   * @returns {Promise} 更新结果
   */
  updateRetentionConfig(data) {
    return request.put('/v1/system/retention', data)
  },

  /**
   * 获取钉钉配置
   * @returns {Promise} 钉钉配置
   */
  getDingTalkConfig() {
    return request.get('/v1/system/dingtalk')
  },

  /**
   * 更新钉钉配置
   * @param {object} data - 钉钉配置
   * @param {boolean} data.enabled - 是否启用
   * @param {string} data.webhook_url - Webhook URL
   * @returns {Promise} 更新结果
   */
  updateDingTalkConfig(data) {
    return request.put('/v1/system/dingtalk', data)
  },

  /**
   * 测试钉钉Webhook
   * @param {string} webhookUrl - Webhook URL
   * @param {string} secret - 加签密钥（可选）
   * @param {boolean} atAll - 是否@所有人
   * @param {string[]} atMobiles - @指定人员手机号列表
   * @returns {Promise} 测试结果
   */
  testDingTalkWebhook(webhookUrl, secret = '', atAll = true, atMobiles = []) {
    return request.post('/v1/system/dingtalk/test', { 
      webhook_url: webhookUrl, 
      secret,
      at_all: atAll,
      at_mobiles: atMobiles
    })
  },

  /**
   * 获取规则简单列表（用于钉钉通知规则选择）
   * @returns {Promise} 规则列表 [{id, name}]
   */
  getRulesSimple() {
    return request.get('/v1/system/rules/simple')
  }
}
