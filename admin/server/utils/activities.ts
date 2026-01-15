/**
 * 活动记录工具函数
 * 用于记录各类文档操作活动
 * 
 * Requirements: 13.11
 */
import { activities, documents } from '@shared/schema'
import { eq } from 'drizzle-orm'

export type ActivityType = 
  | 'document_created'
  | 'document_updated'
  | 'document_published'
  | 'document_deleted'
  | 'comment_added'
  | 'version_created'

export interface RecordActivityOptions {
  userId: string
  type: ActivityType
  documentId?: string
  documentTitle?: string
  versionNum?: number
  commentId?: string
  metadata?: Record<string, any>
}

/**
 * 记录活动
 */
export async function recordActivity(options: RecordActivityOptions) {
  const db = useDb()

  // 如果有 documentId 但没有 documentTitle，尝试获取
  let documentTitle = options.documentTitle
  if (options.documentId && !documentTitle) {
    const [doc] = await db
      .select({ title: documents.title })
      .from(documents)
      .where(eq(documents.id, options.documentId))
      .limit(1)
    documentTitle = doc?.title
  }

  const [activity] = await db
    .insert(activities)
    .values({
      userId: options.userId,
      type: options.type,
      documentId: options.documentId || null,
      documentTitle: documentTitle || null,
      versionNum: options.versionNum || null,
      commentId: options.commentId || null,
      metadata: options.metadata ? JSON.stringify(options.metadata) : null,
    })
    .returning()

  return activity
}

/**
 * 记录文档创建活动
 */
export async function recordDocumentCreated(userId: string, documentId: string, documentTitle: string) {
  return recordActivity({
    userId,
    type: 'document_created',
    documentId,
    documentTitle,
  })
}

/**
 * 记录文档更新活动
 */
export async function recordDocumentUpdated(
  userId: string,
  documentId: string,
  documentTitle: string,
  versionNum?: number
) {
  return recordActivity({
    userId,
    type: 'document_updated',
    documentId,
    documentTitle,
    versionNum,
  })
}

/**
 * 记录文档发布活动
 */
export async function recordDocumentPublished(
  userId: string,
  documentId: string,
  documentTitle: string,
  versionNum: number
) {
  return recordActivity({
    userId,
    type: 'document_published',
    documentId,
    documentTitle,
    versionNum,
  })
}

/**
 * 记录文档删除活动
 */
export async function recordDocumentDeleted(userId: string, documentTitle: string) {
  return recordActivity({
    userId,
    type: 'document_deleted',
    documentTitle,
  })
}

/**
 * 记录评论添加活动
 */
export async function recordCommentAdded(
  userId: string,
  documentId: string,
  documentTitle: string,
  commentId: string
) {
  return recordActivity({
    userId,
    type: 'comment_added',
    documentId,
    documentTitle,
    commentId,
  })
}

/**
 * 记录版本创建活动
 */
export async function recordVersionCreated(
  userId: string,
  documentId: string,
  documentTitle: string,
  versionNum: number,
  changeLog?: string
) {
  return recordActivity({
    userId,
    type: 'version_created',
    documentId,
    documentTitle,
    versionNum,
    metadata: changeLog ? { changeLog } : undefined,
  })
}
