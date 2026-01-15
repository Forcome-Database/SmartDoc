/**
 * 删除文档 API
 * DELETE /api/documents/:id
 * 
 * Requirements: 3.1
 * 删除文档及其所有版本，同时删除 docs 目录下已发布的文件
 */
import { eq } from 'drizzle-orm'
import { documents, versions, editLocks, translations, locales, categories, users } from '@shared/schema'
import { useGitService } from '~/server/utils/git'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const id = getRouterParam(event, 'id')

  if (!id) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少文档 ID',
    })
  }

  // 获取当前用户
  const session = await getUserSession(event)
  if (!session?.user?.id) {
    throw createError({
      statusCode: 401,
      statusMessage: 'Unauthorized',
      message: '请先登录',
    })
  }

  // 获取用户信息（用于 Git 提交）
  const [currentUser] = await db
    .select({ id: users.id, name: users.name, email: users.email })
    .from(users)
    .where(eq(users.id, session.user.id))
    .limit(1)

  // 检查文档是否存在，并获取相关信息
  const [existing] = await db
    .select({
      id: documents.id,
      slug: documents.slug,
      categoryId: documents.categoryId,
      localeId: documents.localeId,
      status: documents.status,
    })
    .from(documents)
    .where(eq(documents.id, id))
    .limit(1)

  if (!existing) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '文档不存在',
    })
  }

  // 检查是否有编辑锁（被其他用户锁定）
  const [lock] = await db
    .select()
    .from(editLocks)
    .where(eq(editLocks.documentId, id))
    .limit(1)

  if (lock && lock.userId !== session.user.id && new Date(lock.expiresAt) > new Date()) {
    throw createError({
      statusCode: 423,
      statusMessage: 'Locked',
      message: '文档正在被其他用户编辑，无法删除',
    })
  }

  // 获取语言信息
  const [locale] = await db
    .select({ code: locales.code })
    .from(locales)
    .where(eq(locales.id, existing.localeId))
    .limit(1)

  // 获取栏目路径
  let categoryPath: string | undefined
  if (existing.categoryId) {
    categoryPath = await getCategoryPath(db, existing.categoryId)
  }

  // 如果文档已发布，删除 docs 目录下的文件
  if (existing.status === 'published' && locale) {
    const gitService = useGitService()
    const author = {
      name: currentUser?.name || 'System',
      email: currentUser?.email || 'system@forcome.local',
    }
    
    const deleteResult = await gitService.deleteDocument(
      locale.code,
      existing.slug,
      categoryPath,
      author
    )
    
    if (!deleteResult.success) {
      console.warn('删除已发布文件失败:', deleteResult.error)
      // 不阻止数据库删除，只记录警告
    }
  }

  // 删除编辑锁
  await db
    .delete(editLocks)
    .where(eq(editLocks.documentId, id))

  // 删除翻译任务
  await db
    .delete(translations)
    .where(eq(translations.documentId, id))

  // 删除版本历史
  await db
    .delete(versions)
    .where(eq(versions.documentId, id))

  // 删除文档
  await db
    .delete(documents)
    .where(eq(documents.id, id))

  return {
    success: true,
    message: '文档已删除',
  }
})

/**
 * 递归获取栏目路径
 */
async function getCategoryPath(db: ReturnType<typeof useDb>, categoryId: string): Promise<string> {
  const pathParts: string[] = []
  let currentId: string | null = categoryId

  while (currentId) {
    const [category] = await db
      .select({ id: categories.id, slug: categories.slug, parentId: categories.parentId })
      .from(categories)
      .where(eq(categories.id, currentId))
      .limit(1)

    if (!category) break

    pathParts.unshift(category.slug)
    currentId = category.parentId
  }

  return pathParts.join('/')
}
