/**
 * 认证中间件
 * 检查用户是否已登录，未登录则重定向到登录页
 * 
 * Requirements: 1.1, 1.4
 */
export default defineNuxtRouteMiddleware(async (to) => {
  // 使用 nuxt-auth-utils 提供的 composable
  const { loggedIn, fetch: fetchSession } = useUserSession()

  // 确保会话状态是最新的
  if (!loggedIn.value) {
    await fetchSession()
  }

  // 如果未登录且不是登录页，重定向到登录页
  if (!loggedIn.value && to.path !== '/login') {
    return navigateTo({
      path: '/login',
      query: {
        redirect: to.fullPath,
      },
    })
  }

  // 如果已登录且在登录页，重定向到首页或指定页面
  if (loggedIn.value && to.path === '/login') {
    const redirect = to.query.redirect
    return navigateTo(typeof redirect === 'string' ? redirect : '/')
  }
})
