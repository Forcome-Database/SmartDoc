/**
 * Drizzle Schema 定义
 * 数据库表结构定义
 */
import { pgTable, text, timestamp, boolean, integer, pgEnum, unique } from 'drizzle-orm/pg-core'
import { relations } from 'drizzle-orm'

// ============ Enums ============
export const userRoleEnum = pgEnum('user_role', ['admin', 'editor', 'viewer'])
export const documentStatusEnum = pgEnum('document_status', ['draft', 'published', 'archived'])
export const navMenuTypeEnum = pgEnum('nav_menu_type', ['link', 'dropdown', 'divider'])
export const navMenuTargetTypeEnum = pgEnum('nav_menu_target_type', ['category', 'document', 'external', 'none'])
export const translationStatusEnum = pgEnum('translation_status', ['pending', 'processing', 'completed', 'failed'])

// ============ Locales ============
export const locales = pgTable('locales', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  code: text('code').unique().notNull(),
  name: text('name').notNull(),
  nativeName: text('native_name').notNull(),
  isDefault: boolean('is_default').default(false).notNull(),
  isEnabled: boolean('is_enabled').default(true).notNull(),
  sortOrder: integer('sort_order').default(0).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
})

// ============ Users ============
export const users = pgTable('users', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  dingtalkId: text('dingtalk_id').unique().notNull(),
  unionId: text('union_id').unique(),
  name: text('name').notNull(),
  avatar: text('avatar'),
  email: text('email'),
  mobile: text('mobile'),
  department: text('department'),
  departmentId: text('department_id'),
  role: userRoleEnum('role').default('editor').notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
})

// ============ Categories ============
export const categories = pgTable('categories', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  parentId: text('parent_id').references(() => categories.id),
  slug: text('slug').notNull(),
  sortOrder: integer('sort_order').default(0).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
})

export const categoryTitles = pgTable('category_titles', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  categoryId: text('category_id').references(() => categories.id, { onDelete: 'cascade' }).notNull(),
  localeId: text('locale_id').references(() => locales.id).notNull(),
  title: text('title').notNull(),
}, (table) => [
  unique().on(table.categoryId, table.localeId),
])

// ============ Documents ============
export const documents = pgTable('documents', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  categoryId: text('category_id').references(() => categories.id),
  authorId: text('author_id').references(() => users.id).notNull(),
  localeId: text('locale_id').references(() => locales.id).notNull(),
  title: text('title').notNull(),
  slug: text('slug').notNull(),
  content: text('content').default('').notNull(),
  status: documentStatusEnum('status').default('draft').notNull(),
  publishedVersion: integer('published_version'),
  hasUnpublishedChanges: boolean('has_unpublished_changes').default(false).notNull(), // 是否有未发布的更改
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
}, (table) => [
  unique().on(table.categoryId, table.localeId, table.slug),
])

// ============ Versions ============
export const versions = pgTable('versions', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  documentId: text('document_id').references(() => documents.id, { onDelete: 'cascade' }).notNull(),
  versionNum: integer('version_num').notNull(),
  content: text('content').notNull(),
  changeLog: text('change_log'),
  authorId: text('author_id').references(() => users.id).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
})

// ============ Edit Locks ============
export const editLocks = pgTable('edit_locks', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  documentId: text('document_id').references(() => documents.id, { onDelete: 'cascade' }).unique().notNull(),
  userId: text('user_id').references(() => users.id).notNull(),
  acquiredAt: timestamp('acquired_at').defaultNow().notNull(),
  expiresAt: timestamp('expires_at').notNull(),
})

// ============ Nav Menus ============
export const navMenus = pgTable('nav_menus', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  parentId: text('parent_id').references(() => navMenus.id),
  type: navMenuTypeEnum('type').default('link').notNull(),
  targetType: navMenuTargetTypeEnum('target_type').default('none').notNull(),
  targetId: text('target_id'),
  externalUrl: text('external_url'),
  openInNewTab: boolean('open_in_new_tab').default(false).notNull(),
  icon: text('icon'),
  sortOrder: integer('sort_order').default(0).notNull(),
  isVisible: boolean('is_visible').default(true).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
})

export const navMenuTitles = pgTable('nav_menu_titles', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  navMenuId: text('nav_menu_id').references(() => navMenus.id, { onDelete: 'cascade' }).notNull(),
  localeId: text('locale_id').references(() => locales.id).notNull(),
  title: text('title').notNull(),
}, (table) => [
  unique().on(table.navMenuId, table.localeId),
])

// ============ Document Watchers ============
export const documentWatchers = pgTable('document_watchers', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  documentId: text('document_id').references(() => documents.id, { onDelete: 'cascade' }).notNull(),
  userId: text('user_id').references(() => users.id, { onDelete: 'cascade' }).notNull(),
  lastSeenAt: timestamp('last_seen_at').defaultNow().notNull(),
  lastVersionSeen: integer('last_version_seen'),
}, (table) => [
  unique().on(table.documentId, table.userId),
])

// ============ Comments ============
export const comments = pgTable('comments', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  documentId: text('document_id').references(() => documents.id, { onDelete: 'cascade' }).notNull(),
  authorId: text('author_id').references(() => users.id).notNull(),
  parentId: text('parent_id').references(() => comments.id, { onDelete: 'cascade' }),
  content: text('content').notNull(),
  // 存储 @提及的用户 ID 列表（JSON 数组）
  mentions: text('mentions'),
  isResolved: boolean('is_resolved').default(false).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
})

// ============ Notifications ============
export const notificationTypeEnum = pgEnum('notification_type', ['mention', 'comment', 'document_update', 'system'])

export const notifications = pgTable('notifications', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  userId: text('user_id').references(() => users.id, { onDelete: 'cascade' }).notNull(),
  type: notificationTypeEnum('type').notNull(),
  title: text('title').notNull(),
  content: text('content'),
  // 关联的资源
  documentId: text('document_id').references(() => documents.id, { onDelete: 'cascade' }),
  commentId: text('comment_id').references(() => comments.id, { onDelete: 'cascade' }),
  // 触发通知的用户
  fromUserId: text('from_user_id').references(() => users.id),
  isRead: boolean('is_read').default(false).notNull(),
  readAt: timestamp('read_at'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
})

// ============ Activities ============
export const activityTypeEnum = pgEnum('activity_type', [
  'document_created',
  'document_updated',
  'document_published',
  'document_deleted',
  'comment_added',
  'version_created',
])

export const activities = pgTable('activities', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  userId: text('user_id').references(() => users.id).notNull(),
  type: activityTypeEnum('type').notNull(),
  documentId: text('document_id').references(() => documents.id, { onDelete: 'cascade' }),
  documentTitle: text('document_title'), // 冗余存储，防止文档删除后丢失
  versionNum: integer('version_num'),
  commentId: text('comment_id').references(() => comments.id, { onDelete: 'set null' }),
  metadata: text('metadata'), // JSON 格式的额外数据
  createdAt: timestamp('created_at').defaultNow().notNull(),
})

// ============ Document Permissions ============
export const permissionLevelEnum = pgEnum('permission_level', ['view', 'edit', 'admin'])
export const permissionTargetTypeEnum = pgEnum('permission_target_type', ['user', 'department'])

export const documentPermissions = pgTable('document_permissions', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  documentId: text('document_id').references(() => documents.id, { onDelete: 'cascade' }).notNull(),
  targetType: permissionTargetTypeEnum('target_type').notNull(),
  targetId: text('target_id').notNull(), // 用户 ID 或部门 ID
  level: permissionLevelEnum('level').notNull(),
  createdBy: text('created_by').references(() => users.id).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
}, (table) => [
  unique().on(table.documentId, table.targetType, table.targetId),
])

// ============ Translations ============
export const translations = pgTable('translations', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  documentId: text('document_id').references(() => documents.id, { onDelete: 'cascade' }).notNull(),
  sourceLocaleId: text('source_locale_id').references(() => locales.id).notNull(),
  targetLocaleId: text('target_locale_id').references(() => locales.id).notNull(),
  status: translationStatusEnum('status').default('pending').notNull(),
  result: text('result'),
  createdBy: text('created_by').references(() => users.id).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
})

// ============ Relations ============
export const usersRelations = relations(users, ({ many }) => ({
  documents: many(documents),
  versions: many(versions),
  editLocks: many(editLocks),
}))

export const documentsRelations = relations(documents, ({ one, many }) => ({
  author: one(users, { fields: [documents.authorId], references: [users.id] }),
  category: one(categories, { fields: [documents.categoryId], references: [categories.id] }),
  locale: one(locales, { fields: [documents.localeId], references: [locales.id] }),
  versions: many(versions),
}))

export const categoriesRelations = relations(categories, ({ one, many }) => ({
  parent: one(categories, { fields: [categories.parentId], references: [categories.id], relationName: 'parentChild' }),
  children: many(categories, { relationName: 'parentChild' }),
  titles: many(categoryTitles),
  documents: many(documents),
}))

export const categoryTitlesRelations = relations(categoryTitles, ({ one }) => ({
  category: one(categories, { fields: [categoryTitles.categoryId], references: [categories.id] }),
  locale: one(locales, { fields: [categoryTitles.localeId], references: [locales.id] }),
}))

export const versionsRelations = relations(versions, ({ one }) => ({
  document: one(documents, { fields: [versions.documentId], references: [documents.id] }),
  author: one(users, { fields: [versions.authorId], references: [users.id] }),
}))

export const editLocksRelations = relations(editLocks, ({ one }) => ({
  document: one(documents, { fields: [editLocks.documentId], references: [documents.id] }),
  user: one(users, { fields: [editLocks.userId], references: [users.id] }),
}))

export const documentWatchersRelations = relations(documentWatchers, ({ one }) => ({
  document: one(documents, { fields: [documentWatchers.documentId], references: [documents.id] }),
  user: one(users, { fields: [documentWatchers.userId], references: [users.id] }),
}))

export const commentsRelations = relations(comments, ({ one, many }) => ({
  document: one(documents, { fields: [comments.documentId], references: [documents.id] }),
  author: one(users, { fields: [comments.authorId], references: [users.id] }),
  parent: one(comments, { fields: [comments.parentId], references: [comments.id], relationName: 'parentChild' }),
  replies: many(comments, { relationName: 'parentChild' }),
}))

export const notificationsRelations = relations(notifications, ({ one }) => ({
  user: one(users, { fields: [notifications.userId], references: [users.id] }),
  document: one(documents, { fields: [notifications.documentId], references: [documents.id] }),
  comment: one(comments, { fields: [notifications.commentId], references: [comments.id] }),
  fromUser: one(users, { fields: [notifications.fromUserId], references: [users.id] }),
}))

export const activitiesRelations = relations(activities, ({ one }) => ({
  user: one(users, { fields: [activities.userId], references: [users.id] }),
  document: one(documents, { fields: [activities.documentId], references: [documents.id] }),
  comment: one(comments, { fields: [activities.commentId], references: [comments.id] }),
}))

export const documentPermissionsRelations = relations(documentPermissions, ({ one }) => ({
  document: one(documents, { fields: [documentPermissions.documentId], references: [documents.id] }),
  createdByUser: one(users, { fields: [documentPermissions.createdBy], references: [users.id] }),
}))

export const navMenusRelations = relations(navMenus, ({ one, many }) => ({
  parent: one(navMenus, { fields: [navMenus.parentId], references: [navMenus.id], relationName: 'parentChild' }),
  children: many(navMenus, { relationName: 'parentChild' }),
  titles: many(navMenuTitles),
}))

export const navMenuTitlesRelations = relations(navMenuTitles, ({ one }) => ({
  navMenu: one(navMenus, { fields: [navMenuTitles.navMenuId], references: [navMenus.id] }),
  locale: one(locales, { fields: [navMenuTitles.localeId], references: [locales.id] }),
}))

export const translationsRelations = relations(translations, ({ one }) => ({
  document: one(documents, { fields: [translations.documentId], references: [documents.id] }),
  sourceLocale: one(locales, { fields: [translations.sourceLocaleId], references: [locales.id] }),
  targetLocale: one(locales, { fields: [translations.targetLocaleId], references: [locales.id] }),
  createdByUser: one(users, { fields: [translations.createdBy], references: [users.id] }),
}))
