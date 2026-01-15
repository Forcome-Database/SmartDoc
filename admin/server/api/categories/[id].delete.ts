/**
 * 删除栏目 API
 * DELETE /api/categories/:id
 * 
 * Requirements: 2.3
 * 删除栏目，需要处理子栏目和关联文档
 * 同时删除 docs 目录下对应的空目录
 */
import { eq, inArray } from 'drizzle-orm'
import { categories, categoryTitles, documents, locales, users } from '@shared/schema'
import { useGitService } from '~/server/utils/git'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const id = getRouterParam(event, 'id')

  if (!id) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少栏目 ID',
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

  // 检查栏目是否存在
  const [existing] = await db
    .select()
    .from(categories)
    .where(eq(categories.id, id))
    .limit(1)

  if (!existing) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '栏目不存在',
    })
  }

  // 检查是否有子栏目
  const children = await db
    .select({ id: categories.id })
    .from(categories)
    .where(eq(categories.parentId, id))
    .limit(1)

  if (children.length > 0) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '该栏目下存在子栏目，请先删除或移动子栏目',
    })
  }

  // 检查是否有关联文档，并获取各语言的文档数量
  const relatedDocs = await db
    .select({ 
      id: documents.id,
      localeId: documents.localeId,
    })
    .from(documents)
    .where(eq(documents.categoryId, id))

  if (relatedDocs.length > 0) {
    // 统计各语言的文档数量
    const localeIds = [...new Set(relatedDocs.map(d => d.localeId))]
    const localeInfos = await db
      .select({ id: locales.id, name: locales.name })
      .from(locales)
      .where(inArray(locales.id, localeIds))
    
    const localeNames = localeInfos.map(l => l.name).join('、')
    
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: `该栏目下存在 ${relatedDocs.length} 个文档（${localeNames}），请先删除或移动文档`,
    })
  }

  // 获取栏目完整路径（用于删除 docs 目录）
  const categoryPath = await getCategoryPath(db, id)

  // 获取所有语言代码
  const allLocales = await db
    .select({ code: locales.code })
    .from(locales)

  // 删除 docs 目录下对应的空目录
  if (categoryPath && allLocales.length > 0) {
    const gitService = useGitService()
    const author = {
      name: currentUser?.name || 'System',
      email: currentUser?.email || 'system@forcome.local',
    }

    const deleteResult = await gitService.deleteDirectory(
      categoryPath,
      allLocales.map(l => l.code),
      author
    )

    if (!deleteResult.success) {
      console.warn('删除栏目目录失败:', deleteResult.error)
      // 不阻止数据库删除，只记录警告
    }
  }

  // 删除栏目标题（级联删除会自动处理，但显式删除更清晰）
  await db
    .delete(categoryTitles)
    .where(eq(categoryTitles.categoryId, id))

  // 删除栏目
  await db
    .delete(categories)
    .where(eq(categories.id, id))

  return { success: true, message: '栏目已删除' }
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
