/**
 * API 响应工具函数
 * 提供统一的响应格式和错误处理
 */
import type { ApiResponse, ApiErrorResponse, SessionUser } from '@shared/types'
import type { H3Event } from 'h3'

/**
 * 创建成功响应
 */
export function successResponse<T>(data: T, message?: string): ApiResponse<T> {
  return {
    success: true,
    data,
    message
  }
}

/**
 * 创建错误响应
 */
export function errorResponse(error: string, statusCode = 400): ApiErrorResponse {
  return {
    success: false,
    error,
    statusCode
  }
}

/**
 * API 错误类
 */
export class ApiError extends Error {
  statusCode: number

  constructor(message: string, statusCode = 400) {
    super(message)
    this.name = 'ApiError'
    this.statusCode = statusCode
  }
}

/**
 * 常见错误工厂函数
 */
export const Errors = {
  /** 未授权 */
  unauthorized: (message = '请先登录') => new ApiError(message, 401),

  /** 禁止访问 */
  forbidden: (message = '没有权限执行此操作') => new ApiError(message, 403),

  /** 资源不存在 */
  notFound: (resource = '资源') => new ApiError(`${resource}不存在`, 404),

  /** 请求参数错误 */
  badRequest: (message: string) => new ApiError(message, 400),

  /** 资源冲突 */
  conflict: (message: string) => new ApiError(message, 409),

  /** 服务器内部错误 */
  internal: (message = '服务器内部错误') => new ApiError(message, 500),

  /** 验证错误 */
  validation: (message: string) => new ApiError(message, 422),
}

/**
 * 验证用户已登录
 * @throws ApiError 如果用户未登录
 */
export async function requireAuth(event: H3Event): Promise<SessionUser> {
  const session = await getUserSession(event)
  if (!session?.user) {
    throw Errors.unauthorized()
  }
  return session.user as SessionUser
}

/**
 * 验证用户角色
 * @throws ApiError 如果用户角色不匹配
 */
export async function requireRole(event: H3Event, roles: string[]): Promise<SessionUser> {
  const user = await requireAuth(event)
  if (!roles.includes(user.role)) {
    throw Errors.forbidden('您的角色没有权限执行此操作')
  }
  return user
}

/**
 * 验证管理员权限
 * @throws ApiError 如果用户不是管理员
 */
export async function requireAdmin(event: H3Event): Promise<SessionUser> {
  return requireRole(event, ['admin'])
}

/**
 * 验证编辑者或管理员权限
 * @throws ApiError 如果用户不是编辑者或管理员
 */
export async function requireEditor(event: H3Event): Promise<SessionUser> {
  return requireRole(event, ['admin', 'editor'])
}

/**
 * 安全地解析 JSON 请求体
 */
export async function parseBody<T>(event: H3Event): Promise<T> {
  try {
    const body = await readBody(event)
    return body as T
  } catch {
    throw Errors.badRequest('无效的请求体')
  }
}

/**
 * 获取必需的路由参数
 * @throws ApiError 如果参数不存在
 */
export function getRequiredParam(event: H3Event, name: string): string {
  const value = getRouterParam(event, name)
  if (!value) {
    throw Errors.badRequest(`缺少必需参数: ${name}`)
  }
  return value
}

/**
 * 获取必需的查询参数
 * @throws ApiError 如果参数不存在
 */
export function getRequiredQuery(event: H3Event, name: string): string {
  const query = getQuery(event)
  const value = query[name]
  if (!value || typeof value !== 'string') {
    throw Errors.badRequest(`缺少必需查询参数: ${name}`)
  }
  return value
}

/**
 * 验证 UUID 格式
 */
export function isValidUUID(str: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
  return uuidRegex.test(str)
}

/**
 * 获取并验证 UUID 参数
 * @throws ApiError 如果参数不存在或格式无效
 */
export function getRequiredUUID(event: H3Event, name: string): string {
  const value = getRequiredParam(event, name)
  if (!isValidUUID(value)) {
    throw Errors.badRequest(`参数 ${name} 必须是有效的 UUID`)
  }
  return value
}
