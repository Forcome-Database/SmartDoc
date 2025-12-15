import request from './request'

/**
 * 审计日志API
 */
export const auditLogAPI = {
  /**
   * 获取审计日志列表
   * @param {object} params - 查询参数
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   * @param {string} params.user_id - 用户ID筛选
   * @param {string} params.action_type - 操作类型筛选
   * @param {string} params.resource_type - 资源类型筛选
   * @param {string} params.start_date - 开始日期
   * @param {string} params.end_date - 结束日期
   * @returns {Promise} 审计日志列表
   */
  list(params) {
    return request.get('/v1/audit-logs', { params })
  },

  /**
   * 导出审计日志
   * @param {object} params - 查询参数
   * @returns {Promise} CSV文件
   */
  export(params) {
    return request.get('/v1/audit-logs/export', {
      params,
      responseType: 'blob'
    })
  }
}
