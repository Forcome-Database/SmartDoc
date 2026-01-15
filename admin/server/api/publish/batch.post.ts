/**
 * 批量发布文档 API
 * POST /api/publish/batch
 * 
 * Requirements: 5.1, 5.3, 5.7
 * - 5.1: 发布文档到 docs/ 目录
 * - 5.3: 发布成功后更新状态
 * - 5.7: 支持批量发布
 */
import { z } from 'zod'
import { eq, inArray, desc } from 'drizzle-orm'
import { documents, versions, categories, locales, users } from '@shared/schema'
import { useGitService, type BatchPublishDocumentParams } from '~/server/utils/git'
import { recordDocumentPublished } from '~/server/utils/activities'

// 请求体验证 Schema
const batchPublishSchema = z.object({
  documentIds: z.array(z.string()).min(1, '至少选择一个文档').max(50, '最多同时发布 50 个文档'),
})

export default defineEventHandler(async (event) => {
  const db = useDb()

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

  // 验证请求体
  const body = await readBody(event)
  const parsed = batchPublishSchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: parsed.error.errors.map(e => e.message).join(', '),
    })
  }

  const { documentIds } = parsed.data

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

  // 获取所有文档详情
  const docs = await db
    .select({
      id: documents.id,
      title: documents.title,
      slug: documents.slug,
      content: documents.content,
      status: documents.status,
      categoryId: documents.categoryId,
      localeId: documents.localeId,
    })
    .from(documents)
    .where(inArray(documents.id, documentIds))

  if (docs.length === 0) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '未找到任何文档',
    })
  }

  // 获取所有相关的语言信息
  const localeIds = [...new Set(docs.map(d => d.localeId))]
  const localeList = await db
    .select({
      id: locales.id,
      code: locales.code,
    })
    .from(locales)
    .where(inArray(locales.id, localeIds))

  const localeMap = new Map(localeList.map(l => [l.id, l.code]))

  // 获取所有相关的栏目路径
  const categoryIds = docs.map(d => d.categoryId).filter((id): id is string => id !== null)
  const categoryPathMap = new Map<string, string>()

  for (const categoryId of categoryIds) {
    if (!categoryPathMap.has(categoryId)) {
      const path = await getCategoryPath(db, categoryId)
      categoryPathMap.set(categoryId, path)
    }
  }

  // 准备批量发布参数
  const publishParams: BatchPublishDocumentParams[] = docs.map(doc => ({
    documentId: doc.id,
    slug: doc.slug,
    locale: localeMap.get(doc.localeId) || 'zh',
    content: doc.content,
    title: doc.title,
    categoryPath: doc.categoryId ? categoryPathMap.get(doc.categoryId) : undefined,
  }))

  // 调用 Git 服务批量发布
  const gitService = useGitService()
  const result = await gitService.publishBatch(publishParams, {
    name: currentUser.name,
    email: currentUser.email || `${currentUser.id}@forcome.local`,
  })

  // 更新成功发布的文档状态
  const successfulIds = result.results
    .filter(r => r.success)
    .map(r => r.documentId)

  if (successfulIds.length > 0) {
    // 获取每个文档的当前版本号
    for (const docId of successfulIds) {
      const [latestVersion] = await db
        .select({ versionNum: versions.versionNum })
        .from(versions)
        .where(eq(versions.documentId, docId))
        .orderBy(desc(versions.versionNum))
        .limit(1)

      const currentVersionNum = latestVersion?.versionNum || 1

      // 更新文档状态
      await db
        .update(documents)
        .set({
          status: 'published',
          publishedVersion: currentVersionNum,
          updatedAt: new Date(),
        })
        .where(eq(documents.id, docId))

      // 记录发布活动
      const doc = docs.find(d => d.id === docId)
      if (doc) {
        await recordDocumentPublished(
          currentUserId,
          docId,
          doc.title,
          currentVersionNum
        )
      }
    }
  }

  return {
    success: result.success,
    commitHash: result.commitHash,
    publishedCount: result.publishedCount,
    failedCount: result.failedCount,
    results: result.results.map(r => ({
      documentId: r.documentId,
      success: r.success,
      filePath: r.filePath,
      error: r.error,
    })),
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
