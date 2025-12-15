/**
 * 草稿管理工具
 * 支持本地存储和API保存
 */

const DRAFT_PREFIX = 'audit_draft_'
const DRAFT_EXPIRY = 24 * 60 * 60 * 1000 // 24小时

/**
 * 保存草稿到localStorage
 * @param {string} taskId - 任务ID
 * @param {Object} data - 草稿数据
 */
export function saveDraftToLocal(taskId, data) {
  try {
    const draft = {
      data,
      timestamp: Date.now(),
      taskId
    }
    localStorage.setItem(`${DRAFT_PREFIX}${taskId}`, JSON.stringify(draft))
    return true
  } catch (error) {
    console.error('Save draft to local failed:', error)
    return false
  }
}

/**
 * 从localStorage加载草稿
 * @param {string} taskId - 任务ID
 * @returns {Object|null} 草稿数据
 */
export function loadDraftFromLocal(taskId) {
  try {
    const draftStr = localStorage.getItem(`${DRAFT_PREFIX}${taskId}`)
    if (!draftStr) return null

    const draft = JSON.parse(draftStr)
    
    // 检查是否过期
    if (Date.now() - draft.timestamp > DRAFT_EXPIRY) {
      removeDraftFromLocal(taskId)
      return null
    }

    return draft.data
  } catch (error) {
    console.error('Load draft from local failed:', error)
    return null
  }
}

/**
 * 删除localStorage中的草稿
 * @param {string} taskId - 任务ID
 */
export function removeDraftFromLocal(taskId) {
  try {
    localStorage.removeItem(`${DRAFT_PREFIX}${taskId}`)
    return true
  } catch (error) {
    console.error('Remove draft from local failed:', error)
    return false
  }
}

/**
 * 清理所有过期草稿
 */
export function cleanExpiredDrafts() {
  try {
    const keys = Object.keys(localStorage)
    const draftKeys = keys.filter(key => key.startsWith(DRAFT_PREFIX))

    draftKeys.forEach(key => {
      const draftStr = localStorage.getItem(key)
      if (draftStr) {
        const draft = JSON.parse(draftStr)
        if (Date.now() - draft.timestamp > DRAFT_EXPIRY) {
          localStorage.removeItem(key)
        }
      }
    })
  } catch (error) {
    console.error('Clean expired drafts failed:', error)
  }
}

/**
 * 创建防抖保存函数
 * @param {Function} saveFn - 保存函数
 * @param {number} delay - 延迟时间（毫秒）
 * @returns {Function} 防抖后的保存函数
 */
export function createDebouncedSave(saveFn, delay = 3000) {
  let timer = null

  return function (...args) {
    if (timer) {
      clearTimeout(timer)
    }

    timer = setTimeout(() => {
      saveFn(...args)
      timer = null
    }, delay)
  }
}

/**
 * 检查是否有未保存的草稿
 * @param {string} taskId - 任务ID
 * @returns {boolean}
 */
export function hasDraft(taskId) {
  return !!loadDraftFromLocal(taskId)
}
