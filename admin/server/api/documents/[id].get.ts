/**
 * 获取文档详情 API
 * GET /api/documents/:id
 * 
 * Requirements: 3.1
 * 返回单个文档的详细信息，包含作者、栏目、语言等关联数据
 */
import { eq, desc } from 'drizzle-orm'
import { documents, users, categories, locales, versions, categoryTitles, editLocks } from '@shared/schema'

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

  // 获取文档
  const [document] = await db
    .select()
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

  // 获取作者信息
  const [author] = await db
    .select({
      id: users.id,
      name: users.name,
      avatar: users.avatar,
    })
    .from(users)
    .where(eq(users.id, document.authorId))
    .limit(1)

  // 获取语言信息
  const [locale] = await db
    .select({
      id: locales.id,
      code: locales.code,
      name: locales.name,
      nativeName: locales.nativeName,
    })
    .from(locales)
    .where(eq(locales.id, document.localeId))
    .limit(1)

  // 获取栏目信息（如果有）- 包含完整路径
  let category = null
  let categoryPath: Array<{ id: string; slug: string; titles: Record<string, string> }> = []
  
  if (document.categoryId) {
    // 递归获取栏目路径
    let currentCatId: string | null = document.categoryId
    
    while (currentCatId) {
      const [cat] = await db
        .select({
          id: categories.id,
          slug: categories.slug,
          parentId: categories.parentId,
        })
        .from(categories)
        .where(eq(categories.id, currentCatId))
        .limit(1)

      if (!cat) break

      // 获取栏目标题
      const catTitles = await db
        .select({
          localeCode: locales.code,
          title: categoryTitles.title,
        })
        .from(categoryTitles)
        .innerJoin(locales, eq(categoryTitles.localeId, locales.id))
        .where(eq(categoryTitles.categoryId, cat.id))

      const titlesMap: Record<string, string> = {}
      for (const t of catTitles) {
        titlesMap[t.localeCode] = t.title
      }

      // 添加到路径开头（因为是从子到父遍历）
      categoryPath.unshift({
        id: cat.id,
        slug: cat.slug,
        titles: titlesMap,
      })

      currentCatId = cat.parentId
    }

    // 当前栏目是路径中的最后一个
    if (categoryPath.length > 0) {
      category = categoryPath[categoryPath.length - 1]
    }
  }

  // 获取最新版本号
  const [latestVersion] = await db
    .select({
      versionNum: versions.versionNum,
    })
    .from(versions)
    .where(eq(versions.documentId, id))
    .orderBy(desc(versions.versionNum))
    .limit(1)

  // 获取编辑锁信息
  const [lock] = await db
    .select({
      id: editLocks.id,
      userId: editLocks.userId,
      acquiredAt: editLocks.acquiredAt,
      expiresAt: editLocks.expiresAt,
      userName: users.name,
      userAvatar: users.avatar,
    })
    .from(editLocks)
    .leftJoin(users, eq(editLocks.userId, users.id))
    .where(eq(editLocks.documentId, id))
    .limit(1)

  // 检查锁是否过期
  let editLock = null
  if (lock && new Date(lock.expiresAt) > new Date()) {
    editLock = {
      id: lock.id,
      userId: lock.userId,
      acquiredAt: lock.acquiredAt,
      expiresAt: lock.expiresAt,
      user: {
        id: lock.userId,
        name: lock.userName,
        avatar: lock.userAvatar,
      },
    }
  }

  return {
    ...document,
    author,
    locale,
    category,
    categoryPath, // 完整栏目路径
    currentVersion: latestVersion?.versionNum || 1,
    editLock,
  }
})
