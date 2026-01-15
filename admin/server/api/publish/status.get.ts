/**
 * 获取 Git 同步状态 API
 * GET /api/publish/status
 * 
 * Requirements: 5.5
 * - 5.5: 显示同步状态（synced, pending changes, conflict）
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

  // 获取 Git 服务
  const gitService = useGitService()

  // 获取详细状态
  const status = await gitService.getDetailedStatus()

  return {
    syncStatus: status.syncStatus,
    ahead: status.ahead,
    behind: status.behind,
    hasLocalChanges: status.modified.length > 0 || status.staged.length > 0,
    modifiedFiles: status.modified,
    stagedFiles: status.staged,
    untrackedFiles: status.untracked,
  }
})
