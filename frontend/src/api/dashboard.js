import request from './request'

/**
 * Dashboard API
 */
export const dashboardAPI = {
  /**
   * Get dashboard metrics
   * @param {object} params - Query parameters (time_range)
   * @returns {Promise} Metrics data
   */
  getMetrics(params) {
    return request.get('/v1/dashboard/metrics', { params })
  },

  /**
   * Get task throughput trend
   * @param {object} params - Query parameters
   * @returns {Promise} Throughput data
   */
  getThroughput(params) {
    return request.get('/v1/dashboard/throughput', { params })
  },

  /**
   * Get rule performance top 10
   * @param {object} params - Query parameters
   * @returns {Promise} Rule performance data
   */
  getRulePerformance(params) {
    return request.get('/v1/dashboard/rule-performance', { params })
  },

  /**
   * Get exception distribution
   * @param {object} params - Query parameters
   * @returns {Promise} Exception data
   */
  getExceptions(params) {
    return request.get('/v1/dashboard/exceptions', { params })
  }
}
