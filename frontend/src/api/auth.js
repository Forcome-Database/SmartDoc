import request from './request'

/**
 * Auth API
 */
export const authAPI = {
  /**
   * User login
   * @param {object} data - Login credentials
   * @param {string} data.username - Username
   * @param {string} data.password - Password
   * @returns {Promise} Login response with token
   */
  login(data) {
    return request.post('/v1/auth/login', data)
  },

  /**
   * User logout
   * @returns {Promise} Logout response
   */
  logout() {
    return request.post('/v1/auth/logout')
  },

  /**
   * Get current user info
   * @returns {Promise} User info
   */
  getCurrentUser() {
    return request.get('/v1/auth/me')
  },

  /**
   * Refresh access token
   * @returns {Promise} New token
   */
  refreshToken() {
    return request.post('/v1/auth/refresh')
  }
}
