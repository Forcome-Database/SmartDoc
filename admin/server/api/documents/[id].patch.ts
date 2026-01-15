/**
 * 更新文档 API
 * PATCH /api/documents/:id
 * 
 * Requirements: 3.7
 * 更新文档内容，自动创建新版本
 */
import { z } from 'zod'
import { documents, versions, categories, locales, users } from '@shared/schema'
import { eq, and, ne, desc } from 'drizzle-orm'

// 请求体验证 Schema
const updateDocumentSchema = z.object({
  title: z.string().min(1, '标题不能为空').max(200, '标题最多 200 个字符').optional(),
  slug: z.string().min(1).max(100).regex(/^[a-z0-9-]+$/, {
    message: 'slug 只能包含小写字母、数字和连字符',
  }).optional(),
  categoryId: z.string().nullable().optional(),
  localeId: z.string().optional(),
  content: z.string().optional(),
  status: z.enum(['draft', 'published', 'archived']).optional(),
  changeLog: z.string().max(500).optional(), // 版本变更说明
  createVersion: z.boolean().default(true), // 是否创建新版本
})

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

  // 验证请求体
  const body = await readBody(event)
  const parsed = updateDocumentSchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: parsed.error.errors.map(e => e.message).join(', '),
    })
  }

  const { title, slug, categoryId, localeId, content, status, changeLog, createVersion } = parsed.data

  // 检查文档是否存在
  const [existing] = await db
    .select()
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

  // 确定目标 localeId 和 categoryId
  const targetLocaleId = localeId !== undefined ? localeId : existing.localeId
  const targetCategoryId = categoryId !== undefined ? categoryId : existing.categoryId

  // 如果更新 localeId，验证语言存在
  if (localeId && localeId !== existing.localeId) {
    const [locale] = await db
      .select({ id: locales.id })
      .from(locales)
      .where(eq(locales.id, localeId))
      .limit(1)

    if (!locale) {
      throw createError({
        statusCode: 400,
        statusMessage: 'Bad Request',
        message: '语言不存在',
      })
    }
  }

  // 如果更新 categoryId，验证栏目存在
  if (categoryId !== undefined && categoryId !== existing.categoryId && categoryId) {
    const [category] = await db
      .select({ id: categories.id })
      .from(categories)
      .where(eq(categories.id, categoryId))
      .limit(1)

    if (!category) {
      throw createError({
        statusCode: 400,
        statusMessage: 'Bad Request',
        message: '栏目不存在',
      })
    }
  }

  // 如果更新 slug，检查同栏目同语言下是否重复
  if (slug && slug !== existing.slug) {
    const conditions = [
      eq(documents.slug, slug),
      eq(documents.localeId, targetLocaleId),
      ne(documents.id, id),
    ]

    if (targetCategoryId) {
      conditions.push(eq(documents.categoryId, targetCategoryId))
    }

    const existingDoc = await db
      .select({ id: documents.id })
      .from(documents)
      .where(and(...conditions))
      .limit(1)

    if (existingDoc.length > 0) {
      throw createError({
        statusCode: 409,
        statusMessage: 'Conflict',
        message: `该栏目下已存在 slug "${slug}" 的文档`,
      })
    }
  }

  // 构建更新数据
  const updateData: Partial<typeof documents.$inferInsert> = {
    updatedAt: new Date(),
  }

  if (title !== undefined) updateData.title = title
  if (slug !== undefined) updateData.slug = slug
  if (categoryId !== undefined) updateData.categoryId = categoryId
  if (localeId !== undefined) updateData.localeId = localeId
  if (content !== undefined) {
    updateData.content = content
    // 内容变化时标记为有未发布的更改
    if (content !== existing.content) {
      updateData.hasUnpublishedChanges = true
    }
  }
  if (status !== undefined) updateData.status = status

  // 更新文档
  const [updatedDocument] = await db
    .update(documents)
    .set(updateData)
    .where(eq(documents.id, id))
    .returning()

  // 如果内容有变化且需要创建版本，创建新版本
  let newVersion = null
  if (content !== undefined && content !== existing.content && createVersion) {
    // 获取当前最大版本号
    const [latestVersion] = await db
      .select({ versionNum: versions.versionNum })
      .from(versions)
      .where(eq(versions.documentId, id))
      .orderBy(desc(versions.versionNum))
      .limit(1)

    const nextVersionNum = (latestVersion?.versionNum || 0) + 1

    // 创建新版本
    const [version] = await db
      .insert(versions)
      .values({
        documentId: id,
        versionNum: nextVersionNum,
        content,
        changeLog: changeLog || null,
        authorId: currentUserId,
      })
      .returning()

    newVersion = version
  }

  // 获取作者信息
  const [author] = await db
    .select({
      id: users.id,
      name: users.name,
      avatar: users.avatar,
    })
    .from(users)
    .where(eq(users.id, updatedDocument.authorId))
    .limit(1)

  // 获取语言信息
  const [locale] = await db
    .select({
      id: locales.id,
      code: locales.code,
      name: locales.name,
    })
    .from(locales)
    .where(eq(locales.id, updatedDocument.localeId))
    .limit(1)

  // 获取当前版本号
  const [currentVersionRecord] = await db
    .select({ versionNum: versions.versionNum })
    .from(versions)
    .where(eq(versions.documentId, id))
    .orderBy(desc(versions.versionNum))
    .limit(1)

  return {
    ...updatedDocument,
    author,
    locale,
    currentVersion: currentVersionRecord?.versionNum || 1,
    newVersion: newVersion ? {
      id: newVersion.id,
      versionNum: newVersion.versionNum,
      changeLog: newVersion.changeLog,
      createdAt: newVersion.createdAt,
    } : null,
  }
})
