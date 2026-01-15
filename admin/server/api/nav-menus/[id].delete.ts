/**
 * 删除导航菜单项 API
 * DELETE /api/nav-menus/:id
 * 
 * Requirements: 5.1
 * 删除菜单项，需要处理子菜单
 */
import { eq } from 'drizzle-orm'
import { navMenus, navMenuTitles } from '@shared/schema'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const id = getRouterParam(event, 'id')

  if (!id) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少菜单 ID',
    })
  }

  // 检查菜单是否存在
  const [existing] = await db
    .select()
    .from(navMenus)
    .where(eq(navMenus.id, id))
    .limit(1)

  if (!existing) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '菜单项不存在',
    })
  }

  // 检查是否有子菜单
  const children = await db
    .select({ id: navMenus.id })
    .from(navMenus)
    .where(eq(navMenus.parentId, id))
    .limit(1)

  if (children.length > 0) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '该菜单下存在子菜单，请先删除或移动子菜单',
    })
  }

  // 删除菜单标题（级联删除会自动处理，但显式删除更清晰）
  await db
    .delete(navMenuTitles)
    .where(eq(navMenuTitles.navMenuId, id))

  // 删除菜单项
  await db
    .delete(navMenus)
    .where(eq(navMenus.id, id))

  return { success: true, message: '菜单项已删除' }
})
