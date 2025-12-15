/**
 * 数据处理管道 API
 */
import request from './request'

const pipelineApi = {
  /**
   * 获取管道列表
   */
  list(params) {
    return request.get('/v1/pipelines', { params })
  },

  /**
   * 获取管道详情
   */
  get(id) {
    return request.get(`/v1/pipelines/${id}`)
  },

  /**
   * 根据规则ID获取管道
   */
  getByRule(ruleId) {
    return request.get(`/v1/pipelines/by-rule/${ruleId}`)
  },

  /**
   * 创建管道
   */
  create(data) {
    return request.post('/v1/pipelines', data)
  },

  /**
   * 更新管道
   */
  update(id, data) {
    return request.put(`/v1/pipelines/${id}`, data)
  },

  /**
   * 删除管道
   */
  delete(id) {
    return request.delete(`/v1/pipelines/${id}`)
  },

  /**
   * 激活管道
   */
  activate(id) {
    return request.post(`/v1/pipelines/${id}/activate`)
  },

  /**
   * 停用管道
   */
  deactivate(id) {
    return request.post(`/v1/pipelines/${id}/deactivate`)
  },

  /**
   * 测试管道
   */
  test(id, data) {
    return request.post(`/v1/pipelines/${id}/test`, data)
  },

  /**
   * 获取执行记录列表
   */
  listExecutions(pipelineId, params) {
    return request.get(`/v1/pipelines/${pipelineId}/executions`, { params })
  },

  /**
   * 获取执行记录详情
   */
  getExecution(executionId) {
    return request.get(`/v1/pipelines/executions/${executionId}`)
  }
}

export default pipelineApi
