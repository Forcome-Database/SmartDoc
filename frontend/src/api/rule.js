import request from './request'

/**
 * Rule API
 */
export const ruleAPI = {
  /**
   * Get rule list
   * @param {object} params - Query parameters
   * @returns {Promise} Rule list
   */
  list(params) {
    return request.get('/v1/rules', { params })
  },

  /**
   * Get rule detail
   * @param {string} ruleId - Rule ID
   * @returns {Promise} Rule detail
   */
  get(ruleId) {
    return request.get(`/v1/rules/${ruleId}`)
  },

  /**
   * Create new rule
   * @param {object} data - Rule data
   * @returns {Promise} Created rule
   */
  create(data) {
    return request.post('/v1/rules', data)
  },

  /**
   * Update rule
   * @param {string} ruleId - Rule ID
   * @param {object} data - Rule data
   * @returns {Promise} Updated rule
   */
  update(ruleId, data) {
    return request.put(`/v1/rules/${ruleId}`, data)
  },

  /**
   * Delete rule
   * @param {string} ruleId - Rule ID
   * @returns {Promise} Delete response
   */
  delete(ruleId) {
    return request.delete(`/v1/rules/${ruleId}`)
  },

  /**
   * Get rule versions
   * @param {string} ruleId - Rule ID
   * @returns {Promise} Version list
   */
  getVersions(ruleId) {
    return request.get(`/v1/rules/${ruleId}/versions`)
  },

  /**
   * Update rule version config
   * @param {string} ruleId - Rule ID
   * @param {number} versionId - Version ID
   * @param {object} data - Config data
   * @returns {Promise} Update response
   */
  updateVersion(ruleId, versionId, data) {
    return request.put(`/v1/rules/${ruleId}/versions/${versionId}`, data)
  },

  /**
   * Publish rule version
   * @param {string} ruleId - Rule ID
   * @param {object} data - Publish data with version_id
   * @returns {Promise} Publish response
   */
  publish(ruleId, data) {
    return request.post(`/v1/rules/${ruleId}/publish`, data)
  },

  /**
   * Rollback to previous version
   * @param {string} ruleId - Rule ID
   * @param {object} data - Rollback data with version_id
   * @returns {Promise} Rollback response
   */
  rollback(ruleId, data) {
    return request.post(`/v1/rules/${ruleId}/rollback`, data)
  },

  /**
   * Test rule in sandbox
   * @param {string} ruleId - Rule ID
   * @param {FormData} formData - Test file
   * @returns {Promise} Test result
   */
  sandbox(ruleId, formData) {
    return request.post(`/v1/rules/${ruleId}/sandbox`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 600000  // 沙箱测试需要更长的超时时间（60秒）
    })
  }
}
