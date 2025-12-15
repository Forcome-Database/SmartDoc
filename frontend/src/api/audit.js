/**
 * 审核工作台API
 */
import request from './request'

export const auditAPI = {
  /**
   * 获取待审核任务列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getPendingTasks(params) {
    return request.get('/v1/audit/tasks', { params })
  },

  /**
   * 获取审核任务详情
   * @param {string} taskId - 任务ID
   * @returns {Promise}
   */
  getTaskDetail(taskId) {
    return request.get(`/v1/audit/tasks/${taskId}`)
  },

  /**
   * 获取PDF页面预览
   * @param {string} taskId - 任务ID
   * @param {number} page - 页码
   * @returns {Promise}
   */
  getPagePreview(taskId, page) {
    return request.get(`/v1/audit/tasks/${taskId}/preview/${page}`, {
      responseType: 'blob'
    })
  },

  /**
   * 保存草稿
   * @param {string} taskId - 任务ID
   * @param {Object} data - 草稿数据
   * @returns {Promise}
   */
  saveDraft(taskId, data) {
    return request.post(`/v1/audit/tasks/${taskId}/draft`, data)
  },

  /**
   * 提交审核
   * @param {string} taskId - 任务ID
   * @param {Object} data - 审核数据
   * @returns {Promise}
   */
  submitAudit(taskId, data) {
    return request.post(`/v1/audit/tasks/${taskId}/submit`, data)
  }
}
