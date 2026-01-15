/**
 * nuxt-auth-utils 类型扩展
 * 定义会话中存储的用户信息类型
 */
import type { UserRole } from './index'

declare module '#auth-utils' {
  interface User {
    id: string
    name: string
    avatar?: string | null
    role: UserRole
    dingtalkId: string
  }

  interface UserSession {
    user: User
  }
}

export {}
