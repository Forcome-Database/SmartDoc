/**
 * 推送到远程仓库 API
 * POST /api/publish/push
 * 
 * Requirements: 5.5
 * - 5.5: 同步状态管理
 */
import { useGitService } from '~/server/utils/git'

export default defineEventHandler(async (event) => {
  // 获取当前用户
  const session = await getUserSession(event)
  if (!session?.user?.id) {
    throw createError({
      statusCode: 401,
      statusMessage: 'Unauthorized',
      message: '请先登录',
    })
  }

  // 检查用户权限（只有 admin 可以推送）
  if (session.user.role !== 'admin') {
    throw createError({
      statusCode: 403,
      statusMessage: 'Forbidden',
      message: '只有管理员可以推送到远程仓库',
    })
  }

  // 获取 Git 服务
  const gitService = useGitService()

  // 推送到远程
  const success = await gitService.push()

  if (!success) {
    throw createError({
      statusCode: 500,
      statusMessage: 'Internal Server Error',
      message: '推送失败，请检查远程仓库配置',
    })
  }

  return {
    success: true,
    message: '推送成功',
  }
})
