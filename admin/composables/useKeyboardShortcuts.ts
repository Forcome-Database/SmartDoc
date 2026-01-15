/**
 * 全局快捷键管理
 * 提供统一的快捷键注册和管理功能
 * 
 * Requirements: 8.5
 */

export interface KeyboardShortcut {
  /** 快捷键标识 */
  key: string
  /** 快捷键描述 */
  description: string
  /** 快捷键显示文本 */
  display: string
  /** 是否需要 Ctrl/Cmd 键 */
  meta?: boolean
  /** 是否需要 Shift 键 */
  shift?: boolean
  /** 是否需要 Alt 键 */
  alt?: boolean
  /** 快捷键处理函数 */
  handler: () => void
  /** 是否在输入框中禁用 */
  disableInInput?: boolean
}

// 检测是否为 Mac 系统
const isMac = typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform)

// 获取修饰键显示文本
export const getModifierKey = () => isMac ? '⌘' : 'Ctrl'

// 格式化快捷键显示
export const formatShortcut = (shortcut: KeyboardShortcut): string => {
  const parts: string[] = []
  if (shortcut.meta) parts.push(getModifierKey())
  if (shortcut.shift) parts.push('Shift')
  if (shortcut.alt) parts.push(isMac ? '⌥' : 'Alt')
  parts.push(shortcut.key.toUpperCase())
  return parts.join(isMac ? '' : '+')
}

// 预定义的快捷键配置
export const SHORTCUTS = {
  SEARCH: {
    key: 'k',
    description: '打开搜索',
    display: 'K',
    meta: true,
    disableInInput: false,
  },
  SAVE: {
    key: 's',
    description: '保存文档',
    display: 'S',
    meta: true,
    disableInInput: false,
  },
  NEW_DOCUMENT: {
    key: 'n',
    description: '新建文档',
    display: 'N',
    meta: true,
    shift: true,
    disableInInput: true,
  },
} as const

/**
 * 全局快捷键 Composable
 */
export function useKeyboardShortcuts() {
  const shortcuts = ref<Map<string, KeyboardShortcut>>(new Map())
  const isEnabled = ref(true)

  // 生成快捷键唯一标识
  const getShortcutId = (shortcut: Omit<KeyboardShortcut, 'handler' | 'description' | 'display'>): string => {
    const parts: string[] = []
    if (shortcut.meta) parts.push('meta')
    if (shortcut.shift) parts.push('shift')
    if (shortcut.alt) parts.push('alt')
    parts.push(shortcut.key.toLowerCase())
    return parts.join('+')
  }

  // 检查是否在输入元素中
  const isInputElement = (target: EventTarget | null): boolean => {
    if (!target || !(target instanceof HTMLElement)) return false
    const tagName = target.tagName.toLowerCase()
    const isEditable = target.isContentEditable
    return tagName === 'input' || tagName === 'textarea' || tagName === 'select' || isEditable
  }

  // 键盘事件处理
  const handleKeydown = (event: KeyboardEvent) => {
    if (!isEnabled.value) return

    const id = getShortcutId({
      key: event.key.toLowerCase(),
      meta: event.metaKey || event.ctrlKey,
      shift: event.shiftKey,
      alt: event.altKey,
    })

    const shortcut = shortcuts.value.get(id)
    if (!shortcut) return

    // 检查是否在输入框中禁用
    if (shortcut.disableInInput && isInputElement(event.target)) {
      return
    }

    event.preventDefault()
    shortcut.handler()
  }

  // 注册快捷键
  const register = (shortcut: KeyboardShortcut): () => void => {
    const id = getShortcutId(shortcut)
    shortcuts.value.set(id, shortcut)
    
    // 返回取消注册函数
    return () => {
      shortcuts.value.delete(id)
    }
  }

  // 批量注册快捷键
  const registerMany = (shortcutList: KeyboardShortcut[]): () => void => {
    const unregisters = shortcutList.map(register)
    return () => {
      unregisters.forEach(unregister => unregister())
    }
  }

  // 启用/禁用快捷键
  const enable = () => { isEnabled.value = true }
  const disable = () => { isEnabled.value = false }

  // 获取所有已注册的快捷键
  const getRegisteredShortcuts = (): KeyboardShortcut[] => {
    return Array.from(shortcuts.value.values())
  }

  // 设置事件监听
  onMounted(() => {
    window.addEventListener('keydown', handleKeydown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown)
  })

  return {
    register,
    registerMany,
    enable,
    disable,
    isEnabled: readonly(isEnabled),
    getRegisteredShortcuts,
    formatShortcut,
    getModifierKey,
    isMac,
  }
}

/**
 * 全局快捷键状态（单例）
 * 用于在应用级别管理快捷键
 */
const globalShortcuts = ref<Map<string, KeyboardShortcut>>(new Map())
const globalEnabled = ref(true)
let isGlobalListenerAttached = false

export function useGlobalShortcuts() {
  // 生成快捷键唯一标识
  const getShortcutId = (shortcut: Omit<KeyboardShortcut, 'handler' | 'description' | 'display'>): string => {
    const parts: string[] = []
    if (shortcut.meta) parts.push('meta')
    if (shortcut.shift) parts.push('shift')
    if (shortcut.alt) parts.push('alt')
    parts.push(shortcut.key.toLowerCase())
    return parts.join('+')
  }

  // 检查是否在输入元素中
  const isInputElement = (target: EventTarget | null): boolean => {
    if (!target || !(target instanceof HTMLElement)) return false
    const tagName = target.tagName.toLowerCase()
    const isEditable = target.isContentEditable
    return tagName === 'input' || tagName === 'textarea' || tagName === 'select' || isEditable
  }

  // 键盘事件处理
  const handleKeydown = (event: KeyboardEvent) => {
    if (!globalEnabled.value) return

    const id = getShortcutId({
      key: event.key.toLowerCase(),
      meta: event.metaKey || event.ctrlKey,
      shift: event.shiftKey,
      alt: event.altKey,
    })

    const shortcut = globalShortcuts.value.get(id)
    if (!shortcut) return

    // 检查是否在输入框中禁用
    if (shortcut.disableInInput && isInputElement(event.target)) {
      return
    }

    event.preventDefault()
    shortcut.handler()
  }

  // 注册快捷键
  const register = (shortcut: KeyboardShortcut): () => void => {
    const id = getShortcutId(shortcut)
    globalShortcuts.value.set(id, shortcut)
    
    // 返回取消注册函数
    return () => {
      globalShortcuts.value.delete(id)
    }
  }

  // 批量注册快捷键
  const registerMany = (shortcutList: KeyboardShortcut[]): () => void => {
    const unregisters = shortcutList.map(register)
    return () => {
      unregisters.forEach(unregister => unregister())
    }
  }

  // 启用/禁用快捷键
  const enable = () => { globalEnabled.value = true }
  const disable = () => { globalEnabled.value = false }

  // 获取所有已注册的快捷键
  const getRegisteredShortcuts = (): KeyboardShortcut[] => {
    return Array.from(globalShortcuts.value.values())
  }

  // 设置全局事件监听（只执行一次）
  onMounted(() => {
    if (!isGlobalListenerAttached && typeof window !== 'undefined') {
      window.addEventListener('keydown', handleKeydown)
      isGlobalListenerAttached = true
    }
  })

  return {
    register,
    registerMany,
    enable,
    disable,
    isEnabled: readonly(globalEnabled),
    getRegisteredShortcuts,
    formatShortcut,
    getModifierKey,
    isMac,
  }
}
