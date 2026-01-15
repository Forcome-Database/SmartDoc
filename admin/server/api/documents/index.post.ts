/**
 * 创建文档 API
 * POST /api/documents
 * 
 * Requirements: 3.1
 * 创建新文档，自动创建初始版本
 */
import { z } from 'zod'
import { documents, versions, categories, locales, users } from '@shared/schema'
import { eq, and } from 'drizzle-orm'

// 请求体验证 Schema
const createDocumentSchema = z.object({
  title: z.string().min(1, '标题不能为空').max(200, '标题最多 200 个字符'),
  slug: z.string().min(1).max(100).regex(/^[a-z0-9-]+$/, {
    message: 'slug 只能包含小写字母、数字和连字符',
  }),
  categoryId: z.string().nullable().optional(),
  localeId: z.string().min(1, '语言不能为空'),
  content: z.string().default(''),
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

  const authorId = session.user.id

  // 验证请求体
  const body = await readBody(event)
  const parsed = createDocumentSchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: parsed.error.errors.map(e => e.message).join(', '),
    })
  }

  const { title, slug, categoryId, localeId, content } = parsed.data

  // 验证语言存在
  const [locale] = await db
    .select()
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

  // 如果有栏目，验证栏目存在
  if (categoryId) {
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

  // 检查同栏目同语言下 slug 是否重复
  const existingDoc = await db
    .select({ id: documents.id })
    .from(documents)
    .where(
      and(
        eq(documents.slug, slug),
        eq(documents.localeId, localeId),
        categoryId ? eq(documents.categoryId, categoryId) : eq(documents.categoryId, '')
      )
    )
    .limit(1)

  if (existingDoc.length > 0) {
    throw createError({
      statusCode: 409,
      statusMessage: 'Conflict',
      message: `该栏目下已存在 slug "${slug}" 的文档`,
    })
  }

  // 创建文档
  const [newDocument] = await db
    .insert(documents)
    .values({
      title,
      slug,
      categoryId: categoryId || null,
      localeId,
      authorId,
      content,
      status: 'draft',
    })
    .returning()

  // 创建初始版本
  const [initialVersion] = await db
    .insert(versions)
    .values({
      documentId: newDocument.id,
      versionNum: 1,
      content,
      changeLog: '初始版本',
      authorId,
    })
    .returning()

  // 获取作者信息
  const [author] = await db
    .select({
      id: users.id,
      name: users.name,
      avatar: users.avatar,
    })
    .from(users)
    .where(eq(users.id, authorId))
    .limit(1)

  return {
    ...newDocument,
    author,
    locale: {
      id: locale.id,
      code: locale.code,
      name: locale.name,
    },
    currentVersion: initialVersion.versionNum,
  }
})
