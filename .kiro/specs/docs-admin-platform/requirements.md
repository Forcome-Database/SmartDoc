# Requirements Document

## Introduction

本文档定义了 FORCOME 知识库后台管理系统的需求规格。该系统是一个类 Mintlify 风格的文档管理平台，支持多用户协作创建栏目和文档，并集成 AI 大模型实现文档多语言翻译功能。系统采用混合版本管理方案（数据库草稿 + Git 发布），UI 风格追求简约大气。

## Glossary

- **Admin_System**: 文档管理后台系统，提供文档编辑、版本管理、AI 翻译等功能
- **Document**: 单个 Markdown 文档，包含内容、元数据和版本历史
- **Category**: 文档栏目/目录，支持多级嵌套的树形结构
- **Version**: 文档的历史版本快照，存储在数据库中
- **Translation_Task**: AI 翻译任务，将文档从源语言翻译到目标语言
- **File_Tree**: 左侧文件树组件，展示文档目录结构
- **Editor**: Notion 风格的富文本编辑器（基于 Novel/Tiptap）
- **User**: 系统用户，具有不同的角色和权限
- **Git_Service**: Git 版本控制服务，用于发布文档到文件系统
- **AI_Service**: AI 翻译服务，基于 Vercel AI SDK 实现流式翻译
- **DingTalk_OAuth**: 钉钉 OAuth 2.0 认证服务，用于企业用户身份验证
- **Edit_Lock**: 文档编辑锁，防止多用户同时编辑产生冲突
- **Collaborator**: 协作者，当前正在查看或编辑同一文档的其他用户
- **Presence**: 在线状态，实时显示用户在系统中的活动状态

## Requirements

### Requirement 1: 用户认证与授权

**User Story:** As a 系统管理员, I want to 管理用户账户和权限, so that 不同角色的用户可以安全地访问系统功能。

#### Acceptance Criteria

1. WHEN a user visits the admin system without authentication THEN THE Admin_System SHALL redirect to the login page
2. WHEN a user provides valid credentials THEN THE Admin_System SHALL authenticate the user and create a session
3. WHEN a user provides invalid credentials THEN THE Admin_System SHALL display an error message and prevent access
4. WHILE a user is authenticated THEN THE Admin_System SHALL maintain the session until logout or timeout
5. WHEN a user logs out THEN THE Admin_System SHALL invalidate the session and redirect to login page
6. THE Admin_System SHALL support role-based access control with at least admin and editor roles

### Requirement 2: 文档栏目管理

**User Story:** As a 内容管理员, I want to 创建和管理文档栏目结构, so that 文档可以按照逻辑层次组织。

#### Acceptance Criteria

1. WHEN a user creates a new category THEN THE Admin_System SHALL add it to the category tree and persist to database
2. WHEN a user renames a category THEN THE Admin_System SHALL update the category name and reflect in file tree
3. WHEN a user deletes a category THEN THE Admin_System SHALL remove the category and prompt for handling child items
4. WHEN a user drags a category to a new position THEN THE Admin_System SHALL update the sort order and parent relationship
5. THE Admin_System SHALL support unlimited nesting levels for categories
6. WHEN a category is created THEN THE Admin_System SHALL require titles for all configured languages (zh, en, vi)
7. THE File_Tree SHALL display categories with expand/collapse functionality

### Requirement 3: 文档创建与编辑

**User Story:** As a 文档编辑者, I want to 使用 Notion 风格的编辑器创建和编辑文档, so that 我可以高效地编写格式丰富的内容。

#### Acceptance Criteria

1. WHEN a user creates a new document THEN THE Admin_System SHALL create a document record and open the editor
2. WHEN a user types in the editor THEN THE Editor SHALL render content in real-time with Markdown formatting
3. WHEN a user presses "/" in the editor THEN THE Editor SHALL display a slash command menu with formatting options
4. THE Editor SHALL support headings, lists, code blocks, images, tables, and blockquotes
5. WHEN a user pastes Markdown content THEN THE Editor SHALL parse and render it correctly
6. WHEN a user exports content THEN THE Editor SHALL serialize to valid Markdown format
7. WHEN a user presses Ctrl+S / Cmd+S THEN THE Admin_System SHALL save the document as a new version
8. THE Editor SHALL provide a toolbar for common formatting actions
9. WHEN the editor content changes THEN THE Admin_System SHALL indicate unsaved changes in the UI

### Requirement 4: 版本管理（数据库层）

**User Story:** As a 文档编辑者, I want to 保存文档的多个版本, so that 我可以追踪变更历史并在需要时回滚。

#### Acceptance Criteria

1. WHEN a user saves a document THEN THE Admin_System SHALL create a new version record in the database
2. WHEN a user views version history THEN THE Admin_System SHALL display a list of versions with timestamps and authors
3. WHEN a user selects a historical version THEN THE Admin_System SHALL display the content of that version
4. WHEN a user compares two versions THEN THE Admin_System SHALL display a diff view highlighting changes
5. WHEN a user reverts to a previous version THEN THE Admin_System SHALL create a new version with the old content
6. THE Admin_System SHALL store version metadata including version number, change log, author, and timestamp
7. WHEN a document is saved THEN THE Admin_System SHALL auto-increment the version number

### Requirement 5: 发布流程（Git 集成）

**User Story:** As a 内容管理员, I want to 将文档发布到 VitePress 站点, so that 用户可以在前端访问最新内容。

#### Acceptance Criteria

1. WHEN a user clicks publish THEN THE Admin_System SHALL write the document content to the docs/ directory
2. WHEN a document is published THEN THE Git_Service SHALL create a commit with the changes
3. WHEN publishing succeeds THEN THE Admin_System SHALL update the document status to "published"
4. WHEN publishing fails THEN THE Admin_System SHALL display an error message and maintain draft status
5. THE Admin_System SHALL display sync status (synced, pending changes, conflict) in the header
6. WHEN a user views a document THEN THE Admin_System SHALL indicate if the current version differs from published version
7. THE Admin_System SHALL support batch publishing of multiple documents

### Requirement 6: AI 翻译功能

**User Story:** As a 文档编辑者, I want to 使用 AI 将文档翻译成其他语言, so that 我可以快速创建多语言版本。

#### Acceptance Criteria

1. WHEN a user initiates translation THEN THE Admin_System SHALL display a translation dialog with language selection
2. WHEN translation starts THEN THE AI_Service SHALL stream the translated content in real-time
3. WHILE translation is in progress THEN THE Admin_System SHALL display a loading indicator and partial results
4. WHEN translation completes THEN THE Admin_System SHALL display the full translated content for review
5. WHEN a user approves the translation THEN THE Admin_System SHALL save it as a new document in the target language
6. THE AI_Service SHALL preserve Markdown formatting during translation
7. THE AI_Service SHALL preserve code blocks without translating code content
8. IF translation fails THEN THE Admin_System SHALL display an error message and allow retry
9. THE Admin_System SHALL support translation between zh, en, and vi languages

### Requirement 7: 文件树导航

**User Story:** As a 文档编辑者, I want to 通过文件树浏览和管理文档, so that 我可以快速定位和操作文档。

#### Acceptance Criteria

1. WHEN the admin system loads THEN THE File_Tree SHALL display the complete document structure
2. WHEN a user clicks a document in the file tree THEN THE Admin_System SHALL open it in the editor
3. WHEN a user right-clicks an item THEN THE File_Tree SHALL display a context menu with actions
4. THE File_Tree SHALL support creating new files and folders via toolbar buttons
5. WHEN a user drags a file THEN THE File_Tree SHALL allow moving it to a different folder
6. THE File_Tree SHALL visually distinguish between folders, documents, and different file states
7. WHEN a document has unsaved changes THEN THE File_Tree SHALL display an indicator

### Requirement 8: 用户界面布局

**User Story:** As a 用户, I want to 使用简约大气的界面, so that 我可以专注于内容编辑而不被复杂的 UI 分散注意力。

#### Acceptance Criteria

1. THE Admin_System SHALL use a three-column layout: sidebar (navigation), file tree, and main content area
2. THE Admin_System SHALL support light and dark themes with system preference detection
3. THE Admin_System SHALL use consistent spacing, typography, and color scheme throughout
4. WHEN the window is resized THEN THE Admin_System SHALL adapt the layout responsively
5. THE Admin_System SHALL provide keyboard shortcuts for common actions (save, publish, search)
6. THE Admin_System SHALL display breadcrumb navigation showing current document path
7. THE Admin_System SHALL use smooth transitions (0.15-0.2s) for UI state changes

### Requirement 9: 搜索功能

**User Story:** As a 文档编辑者, I want to 快速搜索文档, so that 我可以找到需要编辑的内容。

#### Acceptance Criteria

1. WHEN a user presses Ctrl+K / Cmd+K THEN THE Admin_System SHALL open a search modal
2. WHEN a user types in the search box THEN THE Admin_System SHALL display matching documents in real-time
3. THE Admin_System SHALL search document titles, content, and metadata
4. WHEN a user selects a search result THEN THE Admin_System SHALL navigate to that document
5. THE Admin_System SHALL support keyboard navigation in search results (arrow keys, enter)
6. WHEN no results are found THEN THE Admin_System SHALL display an appropriate message

### Requirement 10: 数据持久化

**User Story:** As a 系统管理员, I want to 可靠地存储所有数据, so that 文档和版本历史不会丢失。

#### Acceptance Criteria

1. THE Admin_System SHALL use PostgreSQL as the primary database
2. THE Admin_System SHALL store documents, versions, categories, users, and translation tasks in the database
3. WHEN a database operation fails THEN THE Admin_System SHALL handle the error gracefully and notify the user
4. THE Admin_System SHALL use database transactions for operations that modify multiple records
5. THE Admin_System SHALL implement proper indexing for frequently queried fields

### Requirement 11: 错误处理与反馈

**User Story:** As a 用户, I want to 收到清晰的操作反馈, so that 我知道操作是否成功以及如何处理错误。

#### Acceptance Criteria

1. WHEN an operation succeeds THEN THE Admin_System SHALL display a success toast notification
2. WHEN an operation fails THEN THE Admin_System SHALL display an error message with actionable guidance
3. WHILE a long-running operation is in progress THEN THE Admin_System SHALL display a loading indicator
4. THE Admin_System SHALL validate user input and display inline validation errors
5. IF a network error occurs THEN THE Admin_System SHALL allow retry and preserve user input

### Requirement 12: 钉钉用户集成

**User Story:** As a 企业用户, I want to 使用钉钉账号登录系统, so that 我可以利用企业现有的身份认证体系，无需单独注册账号。

#### Acceptance Criteria

1. WHEN a user clicks "钉钉登录" button THEN THE Admin_System SHALL redirect to DingTalk OAuth authorization page
2. WHEN DingTalk authorization succeeds THEN THE Admin_System SHALL receive authorization code and exchange for access token
3. WHEN access token is obtained THEN THE Admin_System SHALL fetch user info (userId, name, avatar, department) from DingTalk API
4. IF the DingTalk user is new THEN THE Admin_System SHALL auto-create a user record with DingTalk profile
5. IF the DingTalk user exists THEN THE Admin_System SHALL update user profile and create session
6. WHEN DingTalk authorization fails THEN THE Admin_System SHALL display error message and allow retry
7. THE Admin_System SHALL store DingTalk unionId/openId for user identification
8. THE Admin_System SHALL support syncing user department info from DingTalk organization structure
9. WHEN a user logs out THEN THE Admin_System SHALL invalidate both local session and DingTalk token
10. THE Admin_System SHALL support configuring DingTalk AppKey, AppSecret via environment variables

### Requirement 13: 多用户协作

**User Story:** As a 团队成员, I want to 与其他用户协作编辑文档, so that 团队可以高效地共同维护知识库内容。

#### Acceptance Criteria

1. WHEN multiple users open the same document THEN THE Admin_System SHALL display all active collaborators' avatars
2. WHEN a user starts editing a document THEN THE Admin_System SHALL acquire an edit lock for that user
3. WHILE a document is locked by another user THEN THE Admin_System SHALL display the lock holder's info and prevent editing
4. WHEN the lock holder saves or leaves THEN THE Admin_System SHALL release the lock automatically
5. IF a user is inactive for 5 minutes THEN THE Admin_System SHALL auto-release the edit lock
6. WHEN a document is updated by another user THEN THE Admin_System SHALL notify current viewers to refresh
7. THE Admin_System SHALL display real-time presence indicators showing who is viewing each document
8. WHEN a user makes changes THEN THE Admin_System SHALL record the author in version history
9. THE Admin_System SHALL support @mentioning other users in document comments
10. WHEN a user is @mentioned THEN THE Admin_System SHALL send notification (in-app and optionally DingTalk message)
11. THE Admin_System SHALL provide activity feed showing recent document changes by team members
12. THE Admin_System SHALL support document-level permission control (view/edit/admin per user or department)
