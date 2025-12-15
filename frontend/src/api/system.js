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
  }
}
