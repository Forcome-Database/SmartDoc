/**
 * 获取用户列表 API
 * GET /api/users
 * 
 * Requirements: 1.6, 13.12
 * 支持分页和搜索
 */
import { desc, ilike, or, eq, and, count } from 'drizzle-orm'
import { users } from '@shared/schema'

export default defineEventHandler(async (event) => {
  const db = useDb()
  const query = getQuery(event)

  // 检查当前用户是否为管理员
  const currentUser = event.context.user
  if (currentUser?.role !== 'admin') {
    throw createError({
      statusCode: 403,
      statusMessage: 'Forbidden',
      message: '只有管理员可以查看用户列表',
    })
  }

  // 分页参数
  const page = Math.max(1, parseInt(query.page as string) || 1)
  const pageSize = Math.min(100, Math.max(1, parseInt(query.pageSize as string) || 20))
  const offset = (page - 1) * pageSize

  // 搜索参数
  const searchTerm = (query.q as string) || ''
  const roleFilter = query.role as string

  // 构建查询条件
  const conditions = []

  if (searchTerm.trim()) {
    const searchPattern = `%${searchTerm}%`
    conditions.push(
      or(
        ilike(users.name, searchPattern),
        ilike(users.email, searchPattern),
        ilike(users.department, searchPattern)
      )
    )
  }

  if (roleFilter && roleFilter !== 'all' && ['admin', 'editor', 'viewer'].includes(roleFilter)) {
    conditions.push(eq(users.role, roleFilter))
  }

  // 构建 where 条件
  const whereCondition = conditions.length > 0 
    ? (conditions.length === 1 ? conditions[0] : and(...conditions))
    : undefined

  // 获取总数
  const [{ total }] = await db
    .select({ total: count() })
    .from(users)
    .where(whereCondition)

  // 获取用户列表
  const userList = await db
    .select({
      id: users.id,
      name: users.name,
      avatar: users.avatar,
      email: users.email,
      mobile: users.mobile,
      department: users.department,
      departmentId: users.departmentId,
      role: users.role,
      createdAt: users.createdAt,
      updatedAt: users.updatedAt,
    })
    .from(users)
    .where(whereCondition)
    .orderBy(desc(users.createdAt))
    .limit(pageSize)
    .offset(offset)

  return {
    users: userList,
    pagination: {
      page,
      pageSize,
      total,
      totalPages: Math.ceil(total / pageSize),
    },
  }
})
