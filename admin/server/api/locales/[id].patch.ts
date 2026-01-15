/**
 * 更新语言 API
 * PATCH /api/locales/:id
 * 
 * Requirements: 6.9
 */
import { z } from 'zod'
import { locales } from '@shared/schema'
import { eq } from 'drizzle-orm'

// 请求体验证 Schema
const updateLocaleSchema = z.object({
  code: z.string().min(2).max(10).optional(),
  name: z.string().min(1).max(50).optional(),
  nativeName: z.string().min(1).max(50).optional(),
  isDefault: z.boolean().optional(),
  isEnabled: z.boolean().optional(),
})

export default defineEventHandler(async (event) => {
  const db = useDb()
  const id = getRouterParam(event, 'id')

  if (!id) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少语言 ID',
    })
  }

  // 验证请求体
  const body = await readBody(event)
  const parsed = updateLocaleSchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: parsed.error.errors.map(e => e.message).join(', '),
    })
  }

  const updateData = parsed.data

  // 检查语言是否存在
  const existing = await db
    .select()
    .from(locales)
    .where(eq(locales.id, id))
    .limit(1)

  if (existing.length === 0) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '语言不存在',
    })
  }

  // 如果更新语言代码，检查是否与其他语言冲突
  if (updateData.code && updateData.code !== existing[0].code) {
    const codeConflict = await db
      .select()
      .from(locales)
      .where(eq(locales.code, updateData.code))
      .limit(1)

    if (codeConflict.length > 0) {
      throw createError({
        statusCode: 409,
        statusMessage: 'Conflict',
        message: `语言代码 "${updateData.code}" 已存在`,
      })
    }
  }

  // 如果设置为默认语言，先取消其他默认语言
  if (updateData.isDefault === true) {
    await db
      .update(locales)
      .set({ isDefault: false })
      .where(eq(locales.isDefault, true))
  }

  // 更新语言
  const [updatedLocale] = await db
    .update(locales)
    .set(updateData)
    .where(eq(locales.id, id))
    .returning()

  return updatedLocale
})
