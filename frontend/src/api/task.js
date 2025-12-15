import request from './request'

/**
 * Task API
 */
export const taskAPI = {
  /**
   * Get task list
   * @param {object} params - Query parameters
   * @returns {Promise} Task list with pagination
   */
  list(params) {
    return request.get('/v1/tasks', { params })
  },

  /**
   * Get task detail
   * @param {string} taskId - Task ID
   * @returns {Promise} Task detail
   */
  get(taskId) {
    return request.get(`/v1/tasks/${taskId}`)
  },

  /**
   * Upload file(s) for OCR processing
   * 支持单文件和多文件上传
   * @param {FormData} formData - Form data with files and rule_id
   * @param {Function} onProgress - 上传进度回调
   * @returns {Promise} Upload response (UploadResponse or BatchUploadResponse)
   */
  upload(formData, onProgress) {
    return request.post('/v1/ocr/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress
    })
  },

  /**
   * Update task status
   * @param {string} taskId - Task ID
   * @param {object} data - Status update data
   * @returns {Promise} Update response
   */
  updateStatus(taskId, data) {
    return request.patch(`/v1/tasks/${taskId}/status`, data)
  },

  /**
   * Export tasks
   * @param {object} params - Export parameters
   * @returns {Promise} File blob
   */
  export(params) {
    return request.get('/v1/tasks/export', {
      params,
      responseType: 'blob'
    })
  },

  /**
   * Retry failed task
   * @param {string} taskId - Task ID
   * @returns {Promise} Retry response
   */
  retry(taskId) {
    return request.post(`/v1/tasks/${taskId}/retry`)
  },

  /**
   * Repush failed push task
   * @param {string} taskId - Task ID
   * @returns {Promise} Repush response
   */
  repush(taskId) {
    return request.post(`/v1/tasks/${taskId}/repush`)
  },

  /**
   * Cancel queued task
   * @param {string} taskId - Task ID
   * @returns {Promise} Cancel response
   */
  cancel(taskId) {
    return request.post(`/v1/tasks/${taskId}/cancel`)
  },

  /**
   * Delete task
   * @param {string} taskId - Task ID
   * @returns {Promise} Delete response
   */
  delete(taskId) {
    return request.delete(`/v1/tasks/${taskId}`)
  }
}
