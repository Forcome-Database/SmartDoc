/**
 * 重新排序语言 API
 * POST /api/locales/reorder
 * 
 * Requirements: 6.9
 */
import { z } from 'zod'
import { locales } from '@shared/schema'
import { eq, inArray } from 'drizzle-orm'

// 请求体验证 Schema
const reorderSchema = z.object({
  // 语言 ID 数组，按新顺序排列
  ids: z.array(z.string()).min(1),
})

export default defineEventHandler(async (event) => {
  const db = useDb()

  // 验证请求体
  const body = await readBody(event)
  const parsed = reorderSchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: parsed.error.errors.map(e => e.message).join(', '),
    })
  }

  const { ids } = parsed.data

  // 验证所有 ID 都存在
  const existingLocales = await db
    .select({ id: locales.id })
    .from(locales)
    .where(inArray(locales.id, ids))

  if (existingLocales.length !== ids.length) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '部分语言 ID 不存在',
    })
  }

  // 批量更新 sortOrder
  const updatePromises = ids.map((id, index) =>
    db
      .update(locales)
      .set({ sortOrder: index })
      .where(eq(locales.id, id))
  )

  await Promise.all(updatePromises)

  // 返回更新后的语言列表
  const updatedLocales = await db
    .select()
    .from(locales)
    .orderBy(locales.sortOrder)

  return updatedLocales
})
