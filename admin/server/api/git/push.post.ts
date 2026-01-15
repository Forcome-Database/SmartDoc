/**
 * 推送到远程仓库
 * 
 * Requirements: 5.5
 */

export default defineEventHandler(async () => {
  try {
    const git = useGit()
    await git.push()
    
    return { success: true }
  } catch (error: any) {
    console.error('Git 推送失败:', error)
    throw createError({
      statusCode: 500,
      message: error.message || '推送失败',
    })
  }
})
