/**
 * 登出
 * 清除用户会话并使 token 失效
 * 
 * Requirements: 1.5, 12.9
 */
export default defineEventHandler(async (event) => {
  try {
    // 获取当前会话信息（用于日志记录）
    const session = await getUserSession(event)
    
    if (session?.user) {
      console.log(`User ${session.user.name} (${session.user.id}) logged out`)
    }

    // 清除会话
    await clearUserSession(event)

    return {
      success: true,
      message: '已成功登出',
    }
  } catch (error: any) {
    console.error('Logout error:', error)
    
    // 即使出错也尝试清除会话
    try {
      await clearUserSession(event)
    } catch {}

    return {
      success: true,
      message: '已登出',
    }
  }
})
