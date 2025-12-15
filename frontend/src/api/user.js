/**
 * 用户管理 API
 */
import request from './request'

/**
 * 获取用户列表
 * @param {object} params - 查询参数
 * @returns {Promise} 用户列表数据
 */
export function getUserList(params) {
  return request.get('/v1/users', { params })
}

/**
 * 更新用户状态（启用/禁用）
 * @param {string} userId - 用户ID
 * @param {boolean} isActive - 是否激活
 * @returns {Promise} 更新结果
 */
export function updateUserStatus(userId, isActive) {
  return request.patch(`/v1/users/${userId}/status`, { is_active: isActive })
}

/**
 * 删除用户
 * @param {string} userId - 用户ID
 * @returns {Promise} 删除结果
 */
export function deleteUser(userId) {
  return request.delete(`/v1/users/${userId}`)
}

/**
 * 创建用户
 * @param {object} data - 用户数据
 * @returns {Promise} 创建结果
 */
export function createUser(data) {
  return request.post('/v1/users', data)
}

/**
 * 更新用户信息
 * @param {string} userId - 用户ID
 * @param {object} data - 更新数据
 * @returns {Promise} 更新结果
 */
export function updateUser(userId, data) {
  return request.put(`/v1/users/${userId}`, data)
}

/**
 * User API
 */
export const userAPI = {
  /**
   * 获取用户列表
   * @param {object} params - 查询参数
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   * @param {string} params.username - 用户名筛选
   * @param {string} params.email - 邮箱筛选
   * @param {string} params.role - 角色筛选
   * @returns {Promise} 用户列表数据
   */
  list(params) {
    return request.get('/v1/users', { params })
  },

  /**
   * 获取用户详情
   * @param {string} userId - 用户ID
   * @returns {Promise} 用户详情
   */
  get(userId) {
    return request.get(`/v1/users/${userId}`)
  },

  /**
   * 创建用户
   * @param {object} data - 用户数据
   * @param {string} data.username - 用户名
   * @param {string} data.email - 邮箱
   * @param {string} data.password - 密码
   * @param {string} data.role - 角色（admin/architect/auditor/visitor）
   * @returns {Promise} 创建结果
   */
  create(data) {
    return request.post('/v1/users', data)
  },

  /**
   * 更新用户信息
   * @param {string} userId - 用户ID
   * @param {object} data - 更新数据
   * @returns {Promise} 更新结果
   */
  update(userId, data) {
    return request.put(`/v1/users/${userId}`, data)
  },

  /**
   * 更新用户状态（启用/禁用）
   * @param {string} userId - 用户ID
   * @param {boolean} isActive - 是否激活
   * @returns {Promise} 更新结果
   */
  updateStatus(userId, isActive) {
    return request.patch(`/v1/users/${userId}/status`, { is_active: isActive })
  },

  /**
   * 删除用户（软删除）
   * @param {string} userId - 用户ID
   * @returns {Promise} 删除结果
   */
  delete(userId) {
    return request.delete(`/v1/users/${userId}`)
  },

  /**
   * 获取API Key列表
   * @returns {Promise} API Key列表
   */
  getApiKeys() {
    return request.get('/v1/api-keys/')
  },

  /**
   * 生成新的API Key
   * @param {object} data - API Key配置
   * @param {number} data.expires_days - 有效期（天数）
   * @returns {Promise} 生成的API Key（仅此一次返回完整secret）
   */
  createApiKey(data) {
    return request.post('/v1/api-keys/', data)
  },

  /**
   * 撤销API Key
   * @param {string} keyId - API Key ID
   * @returns {Promise} 撤销结果
   */
  revokeApiKey(keyId) {
    return request.delete(`/v1/api-keys/${keyId}/`)
  }
}
