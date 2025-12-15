/**
 * 统一的消息提示工具
 * 封装Ant Design Vue的Message和Notification组件
 */

import { message, notification } from 'ant-design-vue'

// 默认配置
const defaultConfig = {
  duration: 3, // 默认3秒后自动关闭
  maxCount: 3, // 最多同时显示3个消息
}

// 配置全局默认值
message.config({
  ...defaultConfig,
  top: '80px', // 距离顶部的距离
})

notification.config({
  placement: 'topRight', // 通知位置
  duration: 4.5, // 通知默认4.5秒后关闭
  maxCount: 3,
})

/**
 * 成功提示（轻量级）
 * @param {string} content - 提示内容
 * @param {number} duration - 持续时间（秒）
 * @param {Function} onClose - 关闭回调
 */
export const success = (content, duration = 3, onClose) => {
  return message.success({
    content,
    duration,
    onClose,
  })
}

/**
 * 错误提示（轻量级）
 * @param {string} content - 提示内容
 * @param {number} duration - 持续时间（秒）
 * @param {Function} onClose - 关闭回调
 */
export const error = (content, duration = 3, onClose) => {
  return message.error({
    content,
    duration,
    onClose,
  })
}

/**
 * 警告提示（轻量级）
 * @param {string} content - 提示内容
 * @param {number} duration - 持续时间（秒）
 * @param {Function} onClose - 关闭回调
 */
export const warning = (content, duration = 3, onClose) => {
  return message.warning({
    content,
    duration,
    onClose,
  })
}

/**
 * 信息提示（轻量级）
 * @param {string} content - 提示内容
 * @param {number} duration - 持续时间（秒）
 * @param {Function} onClose - 关闭回调
 */
export const info = (content, duration = 3, onClose) => {
  return message.info({
    content,
    duration,
    onClose,
  })
}

/**
 * 加载中提示（轻量级）
 * @param {string} content - 提示内容
 * @param {number} duration - 持续时间（秒，0表示不自动关闭）
 * @param {Function} onClose - 关闭回调
 */
export const loading = (content, duration = 0, onClose) => {
  return message.loading({
    content,
    duration,
    onClose,
  })
}

/**
 * 成功通知（详细信息）
 * @param {Object} options - 配置选项
 * @param {string} options.message - 通知标题
 * @param {string} options.description - 通知描述
 * @param {number} options.duration - 持续时间（秒）
 * @param {Function} options.onClose - 关闭回调
 * @param {Function} options.onClick - 点击回调
 */
export const notifySuccess = (options) => {
  const { message: msg, description, duration = 4.5, onClose, onClick } = options
  
  return notification.success({
    message: msg,
    description,
    duration,
    onClose,
    onClick,
  })
}

/**
 * 错误通知（详细信息）
 * @param {Object} options - 配置选项
 * @param {string} options.message - 通知标题
 * @param {string} options.description - 通知描述
 * @param {number} options.duration - 持续时间（秒）
 * @param {Function} options.onClose - 关闭回调
 * @param {Function} options.onClick - 点击回调
 */
export const notifyError = (options) => {
  const { message: msg, description, duration = 4.5, onClose, onClick } = options
  
  return notification.error({
    message: msg,
    description,
    duration,
    onClose,
    onClick,
  })
}

/**
 * 警告通知（详细信息）
 * @param {Object} options - 配置选项
 * @param {string} options.message - 通知标题
 * @param {string} options.description - 通知描述
 * @param {number} options.duration - 持续时间（秒）
 * @param {Function} options.onClose - 关闭回调
 * @param {Function} options.onClick - 点击回调
 */
export const notifyWarning = (options) => {
  const { message: msg, description, duration = 4.5, onClose, onClick } = options
  
  return notification.warning({
    message: msg,
    description,
    duration,
    onClose,
    onClick,
  })
}

/**
 * 信息通知（详细信息）
 * @param {Object} options - 配置选项
 * @param {string} options.message - 通知标题
 * @param {string} options.description - 通知描述
 * @param {number} options.duration - 持续时间（秒）
 * @param {Function} options.onClose - 关闭回调
 * @param {Function} options.onClick - 点击回调
 */
export const notifyInfo = (options) => {
  const { message: msg, description, duration = 4.5, onClose, onClick } = options
  
  return notification.info({
    message: msg,
    description,
    duration,
    onClose,
    onClick,
  })
}

/**
 * 处理API错误响应
 * @param {Error|Object} error - 错误对象
 * @param {string} defaultMessage - 默认错误消息
 */
export const handleApiError = (error, defaultMessage = '操作失败') => {
  let errorMessage = defaultMessage
  let errorDescription = ''

  if (error.response) {
    // 服务器返回错误响应
    const { status, data } = error.response
    
    switch (status) {
      case 400:
        errorMessage = '请求参数错误'
        errorDescription = data?.message || '请检查输入的数据是否正确'
        break
      case 401:
        errorMessage = '未授权'
        errorDescription = '请重新登录'
        break
      case 403:
        errorMessage = '权限不足'
        errorDescription = '您没有权限执行此操作'
        break
      case 404:
        errorMessage = '资源不存在'
        errorDescription = data?.message || '请求的资源未找到'
        break
      case 429:
        errorMessage = '请求过于频繁'
        errorDescription = '请稍后再试'
        break
      case 500:
        errorMessage = '服务器错误'
        errorDescription = data?.message || '服务器内部错误，请联系管理员'
        break
      default:
        errorMessage = `错误 ${status}`
        errorDescription = data?.message || defaultMessage
    }
  } else if (error.request) {
    // 请求已发送但没有收到响应
    errorMessage = '网络错误'
    errorDescription = '无法连接到服务器，请检查网络连接'
  } else {
    // 其他错误
    errorMessage = defaultMessage
    errorDescription = error.message || '未知错误'
  }

  // 显示错误通知
  notifyError({
    message: errorMessage,
    description: errorDescription,
  })

  return {
    message: errorMessage,
    description: errorDescription,
  }
}

/**
 * 显示操作确认对话框
 * @param {Object} options - 配置选项
 * @param {string} options.title - 对话框标题
 * @param {string} options.content - 对话框内容
 * @param {Function} options.onOk - 确认回调
 * @param {Function} options.onCancel - 取消回调
 * @param {string} options.okText - 确认按钮文字
 * @param {string} options.cancelText - 取消按钮文字
 * @param {string} options.okType - 确认按钮类型
 */
export const confirm = (options) => {
  const {
    title = '确认操作',
    content,
    onOk,
    onCancel,
    okText = '确定',
    cancelText = '取消',
    okType = 'primary',
  } = options

  return new Promise((resolve, reject) => {
    notification.warning({
      message: title,
      description: content,
      duration: 0, // 不自动关闭
      btn: [
        {
          text: cancelText,
          onClick: () => {
            if (onCancel) onCancel()
            reject(new Error('用户取消操作'))
          },
        },
        {
          text: okText,
          type: okType,
          onClick: async () => {
            try {
              if (onOk) await onOk()
              resolve()
            } catch (error) {
              reject(error)
            }
          },
        },
      ],
    })
  })
}

/**
 * 显示文件上传错误
 * @param {string} fileName - 文件名
 * @param {string} reason - 错误原因
 */
export const fileUploadError = (fileName, reason) => {
  notifyError({
    message: '文件上传失败',
    description: `文件 "${fileName}" 上传失败：${reason}`,
  })
}

/**
 * 显示文件上传成功
 * @param {string} fileName - 文件名
 */
export const fileUploadSuccess = (fileName) => {
  success(`文件 "${fileName}" 上传成功`)
}

/**
 * 显示任务处理成功
 * @param {string} taskId - 任务ID
 */
export const taskSuccess = (taskId) => {
  notifySuccess({
    message: '任务处理成功',
    description: `任务 ${taskId} 已成功完成`,
  })
}

/**
 * 显示任务处理失败
 * @param {string} taskId - 任务ID
 * @param {string} reason - 失败原因
 */
export const taskError = (taskId, reason) => {
  notifyError({
    message: '任务处理失败',
    description: `任务 ${taskId} 处理失败：${reason}`,
  })
}

/**
 * 显示保存成功
 */
export const saveSuccess = () => {
  success('保存成功')
}

/**
 * 显示删除成功
 */
export const deleteSuccess = () => {
  success('删除成功')
}

/**
 * 显示更新成功
 */
export const updateSuccess = () => {
  success('更新成功')
}

/**
 * 显示创建成功
 */
export const createSuccess = () => {
  success('创建成功')
}

/**
 * 显示复制成功
 */
export const copySuccess = () => {
  success('复制成功')
}

/**
 * 显示导出成功
 */
export const exportSuccess = () => {
  success('导出成功')
}

/**
 * 显示导入成功
 */
export const importSuccess = () => {
  success('导入成功')
}

// 导出原始的message和notification对象，以便需要时使用
export { message, notification }

// 默认导出
export default {
  success,
  error,
  warning,
  info,
  loading,
  notifySuccess,
  notifyError,
  notifyWarning,
  notifyInfo,
  handleApiError,
  confirm,
  fileUploadError,
  fileUploadSuccess,
  taskSuccess,
  taskError,
  saveSuccess,
  deleteSuccess,
  updateSuccess,
  createSuccess,
  copySuccess,
  exportSuccess,
  importSuccess,
  message,
  notification,
}
