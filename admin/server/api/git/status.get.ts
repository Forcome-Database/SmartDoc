/**
 * 获取 Git 同步状态
 * 
 * Requirements: 5.5
 */

export default defineEventHandler(async () => {
  try {
    const git = useGit()
    
    // 获取状态
    const status = await git.status()
    
    // 简化返回
    return {
      syncStatus: status.ahead > 0 && status.behind > 0 
        ? 'diverged' 
        : status.ahead > 0 
          ? 'ahead' 
          : status.behind > 0 
            ? 'behind' 
            : 'synced',
      ahead: status.ahead || 0,
      behind: status.behind || 0,
      hasLocalChanges: !status.isClean(),
      lastSync: new Date().toISOString(),
    }
  } catch (error: any) {
    console.error('获取 Git 状态失败:', error)
    return {
      syncStatus: 'error',
      ahead: 0,
      behind: 0,
      hasLocalChanges: false,
      error: error.message || '获取状态失败',
    }
  }
})
