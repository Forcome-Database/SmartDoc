/**
 * Slash 命令 Composable
 * 管理 "/" 指令的状态和逻辑
 */

export interface SlashCommandState {
  visible: boolean
  position: { x: number; y: number }
  searchQuery: string
  cursorPosition: number
  slashPosition: number
}

export const useSlashCommand = () => {
  const state = reactive<SlashCommandState>({
    visible: false,
    position: { x: 0, y: 0 },
    searchQuery: '',
    cursorPosition: 0,
    slashPosition: -1,
  })

  /**
   * 检测是否触发 slash 命令
   * @param content 编辑器内容
   * @param cursorPos 光标位置
   */
  const detectSlashCommand = (content: string, cursorPos: number): boolean => {
    // 光标位置无效
    if (cursorPos <= 0 || cursorPos > content.length) {
      return false
    }
    
    // 检查光标前的字符
    const beforeCursor = content.substring(0, cursorPos)
    
    // 查找最后一个 "/" 的位置
    const lastSlashIndex = beforeCursor.lastIndexOf('/')
    
    // 如果没有找到 "/"
    if (lastSlashIndex === -1) {
      return false
    }
    
    // 检查 "/" 前面是否是行首、空格或文档开头
    const charBeforeSlash = lastSlashIndex > 0 ? beforeCursor[lastSlashIndex - 1] : ''
    const isValidPosition = lastSlashIndex === 0 || charBeforeSlash === '\n' || charBeforeSlash === ' '
    
    if (!isValidPosition) {
      return false
    }
    
    // 获取 "/" 后面的内容（搜索查询）
    const afterSlash = beforeCursor.substring(lastSlashIndex + 1)
    
    // 如果 "/" 后面有换行符，则不触发
    if (afterSlash.includes('\n')) {
      return false
    }
    
    // 更新状态
    state.slashPosition = lastSlashIndex
    state.searchQuery = afterSlash
    state.cursorPosition = cursorPos
    
    return true
  }

  /**
   * 显示命令面板
   * @param x X 坐标
   * @param y Y 坐标
   */
  const show = (x: number, y: number) => {
    state.visible = true
    state.position = { x, y }
  }

  /**
   * 隐藏命令面板
   */
  const hide = () => {
    state.visible = false
    state.searchQuery = ''
    state.slashPosition = -1
  }

  /**
   * 更新搜索查询
   */
  const updateSearchQuery = (query: string) => {
    state.searchQuery = query
  }

  /**
   * 更新 slash 位置和光标位置
   */
  const updatePositions = (slashPos: number, cursorPos: number, query: string) => {
    state.slashPosition = slashPos
    state.cursorPosition = cursorPos
    state.searchQuery = query
  }

  /**
   * 获取光标在屏幕上的位置
   * @param editorElement 编辑器 DOM 元素
   */
  const getCursorScreenPosition = (editorElement: HTMLElement): { x: number; y: number } => {
    try {
      // 尝试从 CodeMirror 获取光标位置
      const cmEditor = editorElement.querySelector('.cm-editor')
      if (cmEditor) {
        const cursor = cmEditor.querySelector('.cm-cursor')
        if (cursor) {
          const rect = cursor.getBoundingClientRect()
          return {
            x: rect.left,
            y: rect.bottom + 4, // 在光标下方 4px
          }
        }
      }
      
      // 回退：使用编辑器左上角
      const rect = editorElement.getBoundingClientRect()
      return {
        x: rect.left + 20,
        y: rect.top + 60,
      }
    } catch (e) {
      console.error('Failed to get cursor position:', e)
      return { x: 100, y: 100 }
    }
  }

  return {
    state: readonly(state),
    detectSlashCommand,
    show,
    hide,
    updateSearchQuery,
    getCursorScreenPosition,
  }
}
