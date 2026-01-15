/**
 * 保存翻译结果 API
 * POST /api/translations
 * 
 * Requirements: 6.5, 6.8, 6.9
 * 将翻译结果保存为新文档，关联源文档，记录翻译任务历史
 */
import { z } from 'zod'
import { documents, versions, translations, locales, users, categories } from '@shared/schema'
import { eq, and } from 'drizzle-orm'

// 请求体验证 Schema
const saveTranslationSchema = z.object({
  sourceDocumentId: z.string().min(1, '源文档 ID 不能为空'),
  targetLocaleId: z.string().min(1, '目标语言不能为空'),
  translatedTitle: z.string().min(1, '翻译标题不能为空').max(200, '标题最多 200 个字符'),
  translatedContent: z.string().min(1, '翻译内容不能为空'),
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

  const userId = session.user.id

  // 验证请求体
  const body = await readBody(event)
  const parsed = saveTranslationSchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: parsed.error.errors.map(e => e.message).join(', '),
    })
  }

  const { sourceDocumentId, targetLocaleId, translatedTitle, translatedContent } = parsed.data

  // 获取源文档
  const [sourceDoc] = await db
    .select()
    .from(documents)
    .where(eq(documents.id, sourceDocumentId))
    .limit(1)

  if (!sourceDoc) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '源文档不存在',
    })
  }

  // 验证目标语言存在
  const [targetLocale] = await db
    .select()
    .from(locales)
    .where(eq(locales.id, targetLocaleId))
    .limit(1)

  if (!targetLocale) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '目标语言不存在',
    })
  }

  // 获取源语言
  const [sourceLocale] = await db
    .select()
    .from(locales)
    .where(eq(locales.id, sourceDoc.localeId))
    .limit(1)

  if (!sourceLocale) {
    throw createError({
      statusCode: 500,
      statusMessage: 'Internal Server Error',
      message: '源文档语言配置错误',
    })
  }

  // 检查目标语言是否与源语言相同
  if (sourceDoc.localeId === targetLocaleId) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '目标语言不能与源语言相同',
    })
  }

  // 检查同栏目同语言下是否已存在相同 slug 的文档
  const existingDoc = await db
    .select({ id: documents.id })
    .from(documents)
    .where(
      and(
        eq(documents.slug, sourceDoc.slug),
        eq(documents.localeId, targetLocaleId),
        sourceDoc.categoryId 
          ? eq(documents.categoryId, sourceDoc.categoryId) 
          : eq(documents.categoryId, '')
      )
    )
    .limit(1)

  let newDocument
  let isUpdate = false

  if (existingDoc.length > 0) {
    // 更新已存在的翻译文档
    isUpdate = true
    const [updated] = await db
      .update(documents)
      .set({
        title: translatedTitle,
        content: translatedContent,
        updatedAt: new Date(),
      })
      .where(eq(documents.id, existingDoc[0].id))
      .returning()
    
    newDocument = updated

    // 获取当前最大版本号
    const [latestVersion] = await db
      .select({ versionNum: versions.versionNum })
      .from(versions)
      .where(eq(versions.documentId, newDocument.id))
      .orderBy(versions.versionNum)
      .limit(1)

    const nextVersionNum = (latestVersion?.versionNum || 0) + 1

    // 创建新版本
    await db.insert(versions).values({
      documentId: newDocument.id,
      versionNum: nextVersionNum,
      content: translatedContent,
      changeLog: `AI 翻译更新 (从 ${sourceLocale.code} 翻译)`,
      authorId: userId,
    })
  } else {
    // 创建新的翻译文档
    const [created] = await db
      .insert(documents)
      .values({
        title: translatedTitle,
        slug: sourceDoc.slug, // 使用相同的 slug
        categoryId: sourceDoc.categoryId,
        localeId: targetLocaleId,
        authorId: userId,
        content: translatedContent,
        status: 'draft',
      })
      .returning()

    newDocument = created

    // 创建初始版本
    await db.insert(versions).values({
      documentId: newDocument.id,
      versionNum: 1,
      content: translatedContent,
      changeLog: `AI 翻译 (从 ${sourceLocale.code} 翻译)`,
      authorId: userId,
    })
  }

  // 记录翻译任务
  const [translationRecord] = await db
    .insert(translations)
    .values({
      documentId: sourceDocumentId,
      sourceLocaleId: sourceDoc.localeId,
      targetLocaleId,
      status: 'completed',
      result: newDocument.id, // 存储翻译后的文档 ID
      createdBy: userId,
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
    .where(eq(users.id, userId))
    .limit(1)

  return {
    document: {
      ...newDocument,
      author,
      locale: {
        id: targetLocale.id,
        code: targetLocale.code,
        name: targetLocale.name,
        nativeName: targetLocale.nativeName,
      },
    },
    translation: translationRecord,
    isUpdate,
    message: isUpdate 
      ? `已更新 ${targetLocale.nativeName} 版本的文档` 
      : `已创建 ${targetLocale.nativeName} 版本的文档`,
  }
})
