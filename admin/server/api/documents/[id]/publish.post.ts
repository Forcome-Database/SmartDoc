/**
 * 发布单个文档 API
 * POST /api/documents/:id/publish
 * 
 * Requirements: 5.1, 5.3, 5.4
 * - 5.1: 发布文档到 docs/ 目录
 * - 5.3: 发布成功后更新状态
 * - 5.4: 发布失败显示错误信息
 */
import { eq, desc } from 'drizzle-orm'
import { documents, versions, categories, locales, users } from '@shared/schema'
import { useGitService } from '~/server/utils/git'
import { recordDocumentPublished } from '~/server/utils/activities'

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

  const currentUserId = session.user.id

  // 获取用户信息（用于 Git 提交）
  const [currentUser] = await db
    .select({
      id: users.id,
      name: users.name,
      email: users.email,
    })
    .from(users)
    .where(eq(users.id, currentUserId))
    .limit(1)

  if (!currentUser) {
    throw createError({
      statusCode: 401,
      statusMessage: 'Unauthorized',
      message: '用户不存在',
    })
  }

  // 获取文档详情
  const [document] = await db
    .select({
      id: documents.id,
      title: documents.title,
      slug: documents.slug,
      content: documents.content,
      status: documents.status,
      categoryId: documents.categoryId,
      localeId: documents.localeId,
      publishedVersion: documents.publishedVersion,
    })
    .from(documents)
    .where(eq(documents.id, id))
    .limit(1)

  if (!document) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '文档不存在',
    })
  }

  // 获取语言信息
  const [locale] = await db
    .select({
      id: locales.id,
      code: locales.code,
    })
    .from(locales)
    .where(eq(locales.id, document.localeId))
    .limit(1)

  if (!locale) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '语言配置不存在',
    })
  }

  // 获取栏目路径（如果有）
  let categoryPath: string | undefined
  if (document.categoryId) {
    // 递归获取栏目路径
    categoryPath = await getCategoryPath(db, document.categoryId)
  }

  // 获取当前版本号
  const [latestVersion] = await db
    .select({ versionNum: versions.versionNum })
    .from(versions)
    .where(eq(versions.documentId, id))
    .orderBy(desc(versions.versionNum))
    .limit(1)

  const currentVersionNum = latestVersion?.versionNum || 0
  const newVersionNum = currentVersionNum + 1

  // 发布时创建新版本记录
  await db.insert(versions).values({
    documentId: id,
    versionNum: newVersionNum,
    content: document.content,
    changeLog: '发布文档',
    authorId: currentUserId,
  })

  // 调用 Git 服务发布
  const gitService = useGitService()
  const result = await gitService.publishDocument({
    slug: document.slug,
    locale: locale.code,
    content: document.content,
    title: document.title,
    categoryPath,
    authorName: currentUser.name,
    authorEmail: currentUser.email || `${currentUser.id}@forcome.local`,
  })

  if (!result.success) {
    throw createError({
      statusCode: 500,
      statusMessage: 'Internal Server Error',
      message: result.error || '发布失败',
    })
  }

  // 更新文档状态
  const [updatedDocument] = await db
    .update(documents)
    .set({
      status: 'published',
      publishedVersion: newVersionNum, // 使用新版本号
      hasUnpublishedChanges: false, // 发布后重置未发布更改标记
      updatedAt: new Date(),
    })
    .where(eq(documents.id, id))
    .returning()

  // 记录发布活动
  await recordDocumentPublished(
    currentUserId,
    id,
    document.title,
    newVersionNum
  )

  return {
    success: true,
    document: {
      id: updatedDocument.id,
      title: updatedDocument.title,
      status: updatedDocument.status,
      publishedVersion: updatedDocument.publishedVersion,
      currentVersion: newVersionNum, // 返回新版本号
      hasUnpublishedChanges: false,
    },
    publish: {
      commitHash: result.commitHash,
      filePath: result.filePath,
    },
  }
})

/**
 * 递归获取栏目路径
 * 返回格式: parent-slug/child-slug
 */
async function getCategoryPath(db: ReturnType<typeof useDb>, categoryId: string): Promise<string> {
  const pathParts: string[] = []
  let currentId: string | null = categoryId

  while (currentId) {
    const [category] = await db
      .select({
        id: categories.id,
        slug: categories.slug,
        parentId: categories.parentId,
      })
      .from(categories)
      .where(eq(categories.id, currentId))
      .limit(1)

    if (!category) break

    pathParts.unshift(category.slug)
    currentId = category.parentId
  }

  return pathParts.join('/')
}
