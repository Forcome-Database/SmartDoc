/**
 * 添加语言 API
 * POST /api/locales
 * 
 * Requirements: 6.9
 */
import { z } from 'zod'
import { locales } from '@shared/schema'
import { eq, max } from 'drizzle-orm'

// 请求体验证 Schema
const createLocaleSchema = z.object({
  code: z.string().min(2).max(10),
  name: z.string().min(1).max(50),
  nativeName: z.string().min(1).max(50),
  isDefault: z.boolean().optional().default(false),
  isEnabled: z.boolean().optional().default(true),
})

export default defineEventHandler(async (event) => {
  const db = useDb()

  // 验证请求体
  const body = await readBody(event)
  const parsed = createLocaleSchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: parsed.error.errors.map(e => e.message).join(', '),
    })
  }

  const { code, name, nativeName, isDefault, isEnabled } = parsed.data

  // 检查语言代码是否已存在
  const existing = await db
    .select()
    .from(locales)
    .where(eq(locales.code, code))
    .limit(1)

  if (existing.length > 0) {
    throw createError({
      statusCode: 409,
      statusMessage: 'Conflict',
      message: `语言代码 "${code}" 已存在`,
    })
  }

  // 获取当前最大 sortOrder
  const maxOrderResult = await db
    .select({ maxOrder: max(locales.sortOrder) })
    .from(locales)

  const nextOrder = (maxOrderResult[0]?.maxOrder ?? -1) + 1

  // 如果设置为默认语言，先取消其他默认语言
  if (isDefault) {
    await db
      .update(locales)
      .set({ isDefault: false })
      .where(eq(locales.isDefault, true))
  }

  // 创建新语言
  const [newLocale] = await db
    .insert(locales)
    .values({
      code,
      name,
      nativeName,
      isDefault,
      isEnabled,
      sortOrder: nextOrder,
    })
    .returning()

  return newLocale
})
