/**
 * 通知工具函数
 * 用于创建各类通知
 * 
 * Requirements: 13.10
 */
import { notifications, documents, users } from '@shared/schema'
import { eq } from 'drizzle-orm'

export type NotificationType = 'mention' | 'comment' | 'document_update' | 'system'

export interface CreateNotificationOptions {
  userId: string
  type: NotificationType
  title: string
  content?: string
  documentId?: string
  commentId?: string
  fromUserId?: string
}

/**
 * 创建通知
 */
export async function createNotification(options: CreateNotificationOptions) {
  const db = useDb()

  const [notification] = await db
    .insert(notifications)
    .values({
      userId: options.userId,
      type: options.type,
      title: options.title,
      content: options.content || null,
      documentId: options.documentId || null,
      commentId: options.commentId || null,
      fromUserId: options.fromUserId || null,
    })
    .returning()

  return notification
}

/**
 * 创建 @提及通知
 */
export async function createMentionNotification(options: {
  mentionedUserIds: string[]
  documentId: string
  commentId: string
  fromUserId: string
}) {
  const db = useDb()

  // 获取文档标题
  const [document] = await db
    .select({ title: documents.title })
    .from(documents)
    .where(eq(documents.id, options.documentId))
    .limit(1)

  // 获取发送者名称
  const [fromUser] = await db
    .select({ name: users.name })
    .from(users)
    .where(eq(users.id, options.fromUserId))
    .limit(1)

  const title = `${fromUser?.name || '有人'} 在评论中提到了你`
  const content = document?.title ? `文档：${document.title}` : undefined

  // 为每个被提及的用户创建通知
  const notificationPromises = options.mentionedUserIds
    .filter(userId => userId !== options.fromUserId) // 不通知自己
    .map(userId =>
      createNotification({
        userId,
        type: 'mention',
        title,
        content,
        documentId: options.documentId,
        commentId: options.commentId,
        fromUserId: options.fromUserId,
      })
    )

  return Promise.all(notificationPromises)
}

/**
 * 创建评论通知
 */
export async function createCommentNotification(options: {
  documentAuthorId: string
  documentId: string
  commentId: string
  fromUserId: string
}) {
  const db = useDb()

  // 不通知自己
  if (options.documentAuthorId === options.fromUserId) {
    return null
  }

  // 获取文档标题
  const [document] = await db
    .select({ title: documents.title })
    .from(documents)
    .where(eq(documents.id, options.documentId))
    .limit(1)

  // 获取发送者名称
  const [fromUser] = await db
    .select({ name: users.name })
    .from(users)
    .where(eq(users.id, options.fromUserId))
    .limit(1)

  return createNotification({
    userId: options.documentAuthorId,
    type: 'comment',
    title: `${fromUser?.name || '有人'} 评论了你的文档`,
    content: document?.title,
    documentId: options.documentId,
    commentId: options.commentId,
    fromUserId: options.fromUserId,
  })
}

/**
 * 创建文档更新通知
 */
export async function createDocumentUpdateNotification(options: {
  watcherUserIds: string[]
  documentId: string
  fromUserId: string
}) {
  const db = useDb()

  // 获取文档标题
  const [document] = await db
    .select({ title: documents.title })
    .from(documents)
    .where(eq(documents.id, options.documentId))
    .limit(1)

  // 获取发送者名称
  const [fromUser] = await db
    .select({ name: users.name })
    .from(users)
    .where(eq(users.id, options.fromUserId))
    .limit(1)

  const title = `${fromUser?.name || '有人'} 更新了文档`
  const content = document?.title

  // 为每个查看者创建通知
  const notificationPromises = options.watcherUserIds
    .filter(userId => userId !== options.fromUserId) // 不通知自己
    .map(userId =>
      createNotification({
        userId,
        type: 'document_update',
        title,
        content,
        documentId: options.documentId,
        fromUserId: options.fromUserId,
      })
    )

  return Promise.all(notificationPromises)
}
