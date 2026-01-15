/**
 * 更新用户角色 API
 * PATCH /api/users/:id
 * 
 * Requirements: 1.6, 13.12
 * 只有管理员可以修改用户角色
 */
import { z } from 'zod'
import { users } from '@shared/schema'
import { eq } from 'drizzle-orm'

// 请求体验证 Schema
const updateUserSchema = z.object({
  role: z.enum(['admin', 'editor', 'viewer']),
})

export default defineEventHandler(async (event) => {
  const db = useDb()
  const id = getRouterParam(event, 'id')

  if (!id) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少用户 ID',
    })
  }

  // 检查当前用户是否为管理员
  const currentUser = event.context.user
  if (currentUser?.role !== 'admin') {
    throw createError({
      statusCode: 403,
      statusMessage: 'Forbidden',
      message: '只有管理员可以修改用户角色',
    })
  }

  // 不能修改自己的角色
  if (currentUser.id === id) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '不能修改自己的角色',
    })
  }

  // 验证请求体
  const body = await readBody(event)
  const parsed = updateUserSchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: parsed.error.errors.map(e => e.message).join(', '),
    })
  }

  const { role } = parsed.data

  // 检查用户是否存在
  const existing = await db
    .select()
    .from(users)
    .where(eq(users.id, id))
    .limit(1)

  if (existing.length === 0) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: '用户不存在',
    })
  }

  // 更新用户角色
  const [updatedUser] = await db
    .update(users)
    .set({
      role,
      updatedAt: new Date(),
    })
    .where(eq(users.id, id))
    .returning({
      id: users.id,
      name: users.name,
      avatar: users.avatar,
      email: users.email,
      department: users.department,
      role: users.role,
      updatedAt: users.updatedAt,
    })

  return updatedUser
})
