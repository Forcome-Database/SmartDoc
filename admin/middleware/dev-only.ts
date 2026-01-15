/**
 * 开发环境专用中间件
 * 保护测试页面在生产环境中不可访问
 */
export default defineNuxtRouteMiddleware((to) => {
  // 测试页面路径列表
  const testPages = ['/test-video-upload', '/test-slash-command']

  // 生产环境禁止访问测试页面
  const isProduction = process.env.NODE_ENV === 'production'

  if (isProduction && testPages.includes(to.path)) {
    throw createError({
      statusCode: 404,
      message: 'Page not found'
    })
  }
})
