/**
 * 共享类型定义
 * 所有类型定义的单一来源
 */

// ============ 枚举类型 ============
export type UserRole = 'admin' | 'editor' | 'viewer'
export type DocumentStatus = 'draft' | 'published' | 'archived'
export type NavMenuType = 'link' | 'dropdown' | 'divider'
export type NavMenuTargetType = 'category' | 'document' | 'external' | 'none'
export type TranslationStatus = 'pending' | 'processing' | 'completed' | 'failed'
export type PermissionLevel = 'view' | 'edit' | 'admin'
export type PermissionTargetType = 'user' | 'department'
export type NotificationType = 'mention' | 'comment' | 'document_update' | 'system'
export type ActivityType =
  | 'document_created'
  | 'document_updated'
  | 'document_published'
  | 'document_deleted'
  | 'comment_added'
  | 'version_created'

// ============ 通用工具类型 ============

/** 重排序项（用于拖拽排序） */
export interface ReorderItem {
  id: string
  parentId: string | null
  sortOrder: number
}

// ============ 基础实体类型 ============

/** 用户信息（完整） */
export interface User {
  id: string
  dingtalkId: string
  unionId?: string | null
  name: string
  avatar?: string | null
  email?: string | null
  mobile?: string | null
  department?: string | null
  departmentId?: string | null
  role: UserRole
  createdAt: Date
  updatedAt: Date
}

/** 用户会话信息（存储在 session 中的精简信息） */
export interface SessionUser {
  id: string
  name: string
  avatar?: string | null
  role: UserRole
  dingtalkId: string
  departmentId?: string | null
}

/** 语言配置 */
export interface Locale {
  id: string
  code: string
  name: string
  nativeName: string
  isDefault: boolean
  isEnabled: boolean
  sortOrder: number
  createdAt: Date
}

/** 栏目 */
export interface Category {
  id: string
  parentId?: string | null
  slug: string
  sortOrder: number
  titles: CategoryTitle[]
  children?: Category[]
  createdAt: Date
}

/** 栏目标题 */
export interface CategoryTitle {
  id: string
  categoryId: string
  localeId: string
  title: string
}

/** 文档 */
export interface Document {
  id: string
  categoryId?: string | null
  authorId: string
  localeId: string
  title: string
  slug: string
  content: string
  status: DocumentStatus
  publishedVersion?: number | null
  hasUnpublishedChanges: boolean
  createdAt: Date
  updatedAt: Date
}

/** 版本 */
export interface Version {
  id: string
  documentId: string
  versionNum: number
  content: string
  changeLog?: string | null
  authorId: string
  createdAt: Date
}

/** 编辑锁 */
export interface EditLock {
  id: string
  documentId: string
  userId: string
  acquiredAt: Date
  expiresAt: Date
  user?: User
}

/** 导航菜单 */
export interface NavMenu {
  id: string
  parentId?: string | null
  type: NavMenuType
  targetType: NavMenuTargetType
  targetId?: string | null
  externalUrl?: string | null
  openInNewTab: boolean
  icon?: string | null
  sortOrder: number
  isVisible: boolean
  titles: NavMenuTitle[]
  children?: NavMenu[]
  createdAt: Date
  updatedAt: Date
}

/** 导航菜单标题 */
export interface NavMenuTitle {
  id: string
  navMenuId: string
  localeId: string
  title: string
}

/** 评论 */
export interface Comment {
  id: string
  documentId: string
  authorId: string
  parentId?: string | null
  content: string
  mentions?: string | null
  isResolved: boolean
  createdAt: Date
  updatedAt: Date
  author?: User
  replies?: Comment[]
}

/** 通知 */
export interface Notification {
  id: string
  userId: string
  type: NotificationType
  title: string
  content?: string | null
  documentId?: string | null
  commentId?: string | null
  fromUserId?: string | null
  isRead: boolean
  readAt?: Date | null
  createdAt: Date
}

/** 活动日志 */
export interface Activity {
  id: string
  userId: string
  type: ActivityType
  documentId?: string | null
  documentTitle?: string | null
  versionNum?: number | null
  commentId?: string | null
  metadata?: string | null
  createdAt: Date
  user?: User
}

/** 文档权限 */
export interface DocumentPermission {
  id: string
  documentId: string
  targetType: PermissionTargetType
  targetId: string
  level: PermissionLevel
  createdBy: string
  createdAt: Date
  updatedAt: Date
}

/** 翻译任务 */
export interface Translation {
  id: string
  documentId: string
  sourceLocaleId: string
  targetLocaleId: string
  status: TranslationStatus
  result?: string | null
  createdBy: string
  createdAt: Date
}

/** 文档关注者 */
export interface DocumentWatcher {
  id: string
  documentId: string
  userId: string
  lastSeenAt: Date
  lastVersionSeen?: number | null
}

// ============ API 响应类型 ============

/** 通用 API 响应 */
export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

/** API 错误响应 */
export interface ApiErrorResponse {
  success: false
  error: string
  message?: string
  statusCode?: number
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

/** 分页信息 */
export interface Pagination {
  page: number
  limit: number
  total: number
  totalPages: number
}

// ============ API 请求类型 ============

/** 创建文档请求 */
export interface CreateDocumentRequest {
  categoryId?: string
  localeId: string
  title: string
  slug: string
  content?: string
}

/** 更新文档请求 */
export interface UpdateDocumentRequest {
  title?: string
  slug?: string
  content?: string
  status?: DocumentStatus
  changeLog?: string
}

/** 创建栏目请求 */
export interface CreateCategoryRequest {
  parentId?: string
  slug: string
  titles: { localeId: string; title: string }[]
}

/** 创建评论请求 */
export interface CreateCommentRequest {
  content: string
  parentId?: string
  mentions?: string[]
}

/** 设置权限请求 */
export interface SetPermissionRequest {
  targetType: PermissionTargetType
  targetId: string
  level: PermissionLevel
}

// ============ 文件上传类型 ============

/** 文件类型 */
export type FileType = 'image' | 'video' | 'document'

/** 上传响应 */
export interface UploadResponse {
  url: string
  objectName: string
  filename: string
  mimeType: string
  size: number
  fileType: FileType
}

// ============ 权限检查结果 ============

/** 权限检查结果 */
export interface CheckPermissionResult {
  hasPermission: boolean
  level: PermissionLevel | null
  isAuthor: boolean
  isAdmin: boolean
}

// ============ 内容树类型 ============

/** 内容树节点 */
export interface ContentTreeNode {
  id: string
  type: 'category' | 'document'
  title: string
  slug: string
  parentId?: string | null
  sortOrder: number
  children?: ContentTreeNode[]
  // 文档特有属性
  status?: DocumentStatus
  hasUnpublishedChanges?: boolean
  localeId?: string
}

// ============ 发布相关类型 ============

/** 发布状态 */
export interface PublishStatus {
  documentId: string
  status: 'pending' | 'publishing' | 'success' | 'failed'
  message?: string
}

/** 批量发布请求 */
export interface BatchPublishRequest {
  documentIds: string[]
  changeLog?: string
}

/** Git 同步状态 */
export interface GitSyncStatus {
  lastSyncAt?: Date
  status: 'synced' | 'pending' | 'syncing' | 'error'
  message?: string
}
