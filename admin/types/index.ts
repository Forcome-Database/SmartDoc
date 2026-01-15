/**
 * Admin 类型定义
 * 从 shared 导出所有类型，并添加 Admin 特有类型
 */

// 从 shared 导出所有类型
export * from '@shared/types'

// ============ Admin 特有类型 ============

/** 编辑器状态 */
export interface EditorState {
  isDirty: boolean
  isSaving: boolean
  lastSavedAt?: Date
}

/** 面包屑项 */
export interface BreadcrumbItem {
  label: string
  path?: string
}

/** 侧边栏菜单项 */
export interface SidebarMenuItem {
  label: string
  icon?: string
  path?: string
  children?: SidebarMenuItem[]
  badge?: string | number
}

/** 表格列配置 */
export interface TableColumn<T = unknown> {
  key: keyof T | string
  label: string
  sortable?: boolean
  width?: string | number
  align?: 'left' | 'center' | 'right'
  render?: (value: unknown, row: T) => string
}

/** 表单字段配置 */
export interface FormField {
  name: string
  label: string
  type: 'text' | 'textarea' | 'select' | 'checkbox' | 'radio' | 'date' | 'file'
  required?: boolean
  placeholder?: string
  options?: { label: string; value: string | number }[]
  validation?: (value: unknown) => string | null
}

/** 对话框配置 */
export interface DialogConfig {
  title: string
  message?: string
  confirmText?: string
  cancelText?: string
  type?: 'info' | 'warning' | 'error' | 'success'
}

/** 快捷键配置 */
export interface KeyboardShortcut {
  key: string
  modifiers?: ('ctrl' | 'alt' | 'shift' | 'meta')[]
  description: string
  action: () => void
}
