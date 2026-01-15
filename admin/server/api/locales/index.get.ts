/**
 * 获取语言列表 API
 * GET /api/locales
 * 
 * Requirements: 6.9
 */
import { asc } from 'drizzle-orm'
import { locales } from '@shared/schema'

export default defineEventHandler(async () => {
  const db = useDb()

  // 按 sortOrder 升序获取所有语言
  const result = await db
    .select()
    .from(locales)
    .orderBy(asc(locales.sortOrder))

  return result
})
