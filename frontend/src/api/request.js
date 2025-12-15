/**
 * Axios请求配置
 * 统一的HTTP请求封装，包含请求/响应拦截器、错误处理和Token自动续期
 */
import axios from 'axios'
import { message } from 'ant-design-vue'

/**
 * 创建Axios实例
 * 配置baseURL、timeout等基础参数
 */
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api'

// 调试：打印实际的baseURL
console.log('[API Config] baseURL:', apiBaseUrl, 'ENV:', import.meta.env.VITE_API_BASE_URL)

const request = axios.create({
  baseURL: apiBaseUrl,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Token刷新状态管理
let isRefreshing = false
let refreshSubscribers = []

/**
 * 添加等待刷新的请求到队列
 */
function subscribeTokenRefresh(callback) {
  refreshSubscribers.push(callback)
}

/**
 * 刷新完成后，执行队列中的请求
 */
function onTokenRefreshed(newToken) {
  refreshSubscribers.forEach(callback => callback(newToken))
  refreshSubscribers = []
}

/**
 * 解析JWT Token获取过期时间
 */
function getTokenExpiration(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.exp * 1000 // 转换为毫秒
  } catch {
    return null
  }
}

/**
 * 检查Token是否已过期
 */
function isTokenExpired(token) {
  const expiration = getTokenExpiration(token)
  if (!expiration) return false
  return Date.now() >= expiration
}

/**
 * 检查Token是否即将过期（5分钟内）或已过期
 */
function isTokenExpiringSoon(token) {
  const expiration = getTokenExpiration(token)
  if (!expiration) return false
  
  const now = Date.now()
  const fiveMinutes = 5 * 60 * 1000
  // 如果已过期或即将过期（5分钟内），都返回true
  return expiration - now < fiveMinutes
}

/**
 * 刷新Token
 */
async function refreshToken() {
  const response = await axios.post(
    `${import.meta.env.VITE_API_BASE_URL || '/api'}/v1/auth/refresh`,
    {},
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  )
  return response.data.access_token
}

/**
 * 请求拦截器
 * 在请求发送前添加认证Token，并检查是否需要刷新
 */
request.interceptors.request.use(
  async config => {
    const token = localStorage.getItem('access_token')
    
    // 记录请求日志（开发环境）
    if (import.meta.env.DEV) {
      console.log(`[Request] ${config.method?.toUpperCase()} ${config.url}`, {
        params: config.params,
        data: config.data,
        hasToken: !!token
      })
    }
    
    if (token) {
      // 先添加Token到请求头（确保请求一定带有Token）
      config.headers.Authorization = `Bearer ${token}`
      
      // 检查Token是否即将过期，且不是刷新Token的请求本身
      const isRefreshRequest = config.url?.includes('/auth/refresh')
      if (!isRefreshRequest && isTokenExpiringSoon(token)) {
        if (!isRefreshing) {
          isRefreshing = true
          try {
            const newToken = await refreshToken()
            localStorage.setItem('access_token', newToken)
            onTokenRefreshed(newToken)
            config.headers.Authorization = `Bearer ${newToken}`
          } catch (error) {
            console.error('Token刷新失败，使用原Token:', error)
            // 刷新失败，继续使用原Token（已经在上面设置了）
          } finally {
            isRefreshing = false
          }
        } else {
          // 正在刷新中，等待刷新完成
          return new Promise(resolve => {
            subscribeTokenRefresh(newToken => {
              config.headers.Authorization = `Bearer ${newToken}`
              resolve(config)
            })
          })
        }
      }
    }
    
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

/**
 * 响应拦截器
 * 统一处理响应数据和错误
 */
request.interceptors.response.use(
  response => {
    // 对于blob类型响应，直接返回data（不打印日志，因为blob无法序列化）
    if (response.config.responseType === 'blob') {
      return response.data
    }
    
    // 记录响应日志（开发环境）
    if (import.meta.env.DEV) {
      console.log(`[Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data)
    }
    
    // 直接返回响应数据
    return response.data
  },
  async error => {
    // 处理错误响应
    if (error.response) {
      const { status, data } = error.response
      const errorMessage = data?.message || data?.detail || '请求失败'
      
      // 根据状态码进行不同处理
      switch (status) {
        case 400:
          // 请求参数错误
          message.error(errorMessage || '请求参数错误')
          break
          
        case 401: {
          // 未认证 - 尝试刷新Token，如果失败则跳转登录页
          const isRefreshRequest = error.config?.url?.includes('/auth/refresh')
          const hasRetried = error.config?._retry
          
          if (!isRefreshRequest && !hasRetried) {
            error.config._retry = true
            try {
              const newToken = await refreshToken()
              localStorage.setItem('access_token', newToken)
              error.config.headers.Authorization = `Bearer ${newToken}`
              return request(error.config)
            } catch (refreshError) {
              // 刷新失败，清除Token并跳转登录页
              console.error('Token刷新失败，跳转登录页:', refreshError)
              message.error('登录已过期，请重新登录')
              localStorage.removeItem('access_token')
              localStorage.removeItem('user_info')
              setTimeout(() => {
                window.location.href = '/login'
              }, 1000)
            }
          } else if (isRefreshRequest) {
            // 刷新Token请求本身失败，直接跳转登录页
            console.error('刷新Token请求失败')
            message.error('登录已过期，请重新登录')
            localStorage.removeItem('access_token')
            localStorage.removeItem('user_info')
            setTimeout(() => {
              window.location.href = '/login'
            }, 1000)
          }
          // 如果已经重试过了，不再处理，让错误继续传播
          break
        }
          
        case 403:
          // 无权限
          message.error(errorMessage || '无权限访问')
          break
          
        case 404:
          // 资源不存在
          message.error(errorMessage || '请求的资源不存在')
          break
          
        case 429:
          // 请求过于频繁
          message.warning('请求过于频繁，请稍后再试')
          break
          
        case 500:
          // 服务器错误
          message.error(errorMessage || '服务器错误，请稍后重试')
          break
          
        case 502:
        case 503:
        case 504:
          // 服务不可用
          message.error('服务暂时不可用，请稍后重试')
          break
          
        default:
          message.error(errorMessage || '请求失败')
      }
      
      // 记录错误日志
      console.error(`[Error] ${error.config?.method?.toUpperCase()} ${error.config?.url}`, {
        status,
        message: errorMessage,
        data: data?.detail
      })
    } else if (error.request) {
      // 请求已发送但没有收到响应
      message.error('网络连接失败，请检查网络')
      console.error('[Network Error]', error.message)
    } else {
      // 请求配置出错
      message.error('请求配置错误')
      console.error('[Request Config Error]', error.message)
    }
    
    return Promise.reject(error)
  }
)

/**
 * 导出请求实例
 */
export default request
