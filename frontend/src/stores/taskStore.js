/**
 * 任务Store
 * 管理任务列表、详情和状态
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { taskAPI } from '@/api'

export const useTaskStore = defineStore('task', () => {
  // ==================== State ====================
  
  /**
   * 任务列表
   */
  const tasks = ref([])
  
  /**
   * 当前任务详情
   */
  const currentTask = ref(null)
  
  /**
   * 筛选条件
   */
  const filters = ref({
    status: null,
    rule_id: null,
    date_range: null,
    search: null
  })
  
  /**
   * 分页信息
   */
  const pagination = ref({
    page: 1,
    page_size: 20,
    total: 0
  })
  
  /**
   * 排序信息
   */
  const sorting = ref({
    field: 'created_at',
    order: 'desc'
  })
  
  /**
   * 加载状态
   */
  const loading = ref({
    list: false,
    detail: false,
    uploading: false,
    updating: false,
    exporting: false
  })

  // ==================== Getters ====================
  
  /**
   * 是否有任何加载中的操作
   */
  const isLoading = computed(() => {
    return Object.values(loading.value).some(v => v)
  })
  
  /**
   * 按状态分组的任务统计
   */
  const tasksByStatus = computed(() => {
    const stats = {
      queued: 0,
      processing: 0,
      pending_audit: 0,
      completed: 0,
      rejected: 0,
      push_failed: 0
    }
    
    tasks.value.forEach(task => {
      if (stats.hasOwnProperty(task.status)) {
        stats[task.status]++
      }
    })
    
    return stats
  })
  
  /**
   * 待审核任务数量
   */
  const pendingAuditCount = computed(() => {
    return tasks.value.filter(t => t.status === 'pending_audit').length
  })
  
  /**
   * 推送失败任务数量
   */
  const pushFailedCount = computed(() => {
    return tasks.value.filter(t => t.status === 'push_failed').length
  })

  // ==================== Actions ====================
  
  /**
   * 获取任务列表
   */
  async function fetchTasks() {
    loading.value.list = true
    try {
      const response = await taskAPI.list({
        ...filters.value,
        ...pagination.value,
        sort_by: sorting.value.field,
        sort_order: sorting.value.order
      })
      
      if (response.code === 200) {
        tasks.value = response.data.items || []
        pagination.value.total = response.data.total || 0
      }
      
      return response
    } catch (error) {
      console.error('获取任务列表失败:', error)
      throw error
    } finally {
      loading.value.list = false
    }
  }
  
  /**
   * 获取任务详情
   * @param {string} taskId - 任务ID
   */
  async function fetchTaskDetail(taskId) {
    loading.value.detail = true
    try {
      const response = await taskAPI.get(taskId)
      
      if (response.code === 200) {
        currentTask.value = response.data
      }
      
      return response
    } catch (error) {
      console.error('获取任务详情失败:', error)
      throw error
    } finally {
      loading.value.detail = false
    }
  }
  
  /**
   * 上传文件
   * @param {FormData} formData - 包含文件和rule_id的表单数据
   */
  async function uploadFile(formData) {
    loading.value.uploading = true
    try {
      const response = await taskAPI.upload(formData)
      
      if (response.code === 200) {
        // 如果是秒传，直接添加到任务列表
        if (response.data.is_instant) {
          tasks.value.unshift(response.data)
        }
      }
      
      return response
    } catch (error) {
      console.error('文件上传失败:', error)
      throw error
    } finally {
      loading.value.uploading = false
    }
  }
  
  /**
   * 更新任务状态
   * @param {string} taskId - 任务ID
   * @param {object} data - 状态更新数据
   */
  async function updateTaskStatus(taskId, data) {
    loading.value.updating = true
    try {
      const response = await taskAPI.updateStatus(taskId, data)
      
      if (response.code === 200) {
        // 更新当前任务
        if (currentTask.value?.id === taskId) {
          currentTask.value = { ...currentTask.value, ...response.data }
        }
        
        // 更新列表中的任务
        const index = tasks.value.findIndex(t => t.id === taskId)
        if (index !== -1) {
          tasks.value[index] = { ...tasks.value[index], ...response.data }
        }
      }
      
      return response
    } catch (error) {
      console.error('更新任务状态失败:', error)
      throw error
    } finally {
      loading.value.updating = false
    }
  }
  
  /**
   * 导出任务
   * @param {object} exportParams - 导出参数
   */
  async function exportTasks(exportParams) {
    loading.value.exporting = true
    try {
      const response = await taskAPI.export({
        ...filters.value,
        ...exportParams
      })
      
      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `tasks_${Date.now()}.${exportParams.format || 'csv'}`)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      return { code: 200, message: '导出成功' }
    } catch (error) {
      console.error('导出任务失败:', error)
      throw error
    } finally {
      loading.value.exporting = false
    }
  }
  
  /**
   * 设置筛选条件
   * @param {object} newFilters - 新的筛选条件
   */
  function setFilters(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
    pagination.value.page = 1 // 重置页码
  }
  
  /**
   * 设置分页
   * @param {object} newPagination - 新的分页信息
   */
  function setPagination(newPagination) {
    pagination.value = { ...pagination.value, ...newPagination }
  }
  
  /**
   * 设置排序
   * @param {string} field - 排序字段
   * @param {string} order - 排序方向（asc/desc）
   */
  function setSorting(field, order) {
    sorting.value = { field, order }
  }
  
  /**
   * 设置当前任务
   * @param {object} task - 任务对象
   */
  function setCurrentTask(task) {
    currentTask.value = task
  }
  
  /**
   * 清除当前任务
   */
  function clearCurrentTask() {
    currentTask.value = null
  }
  
  /**
   * 刷新任务列表
   */
  async function refresh() {
    await fetchTasks()
  }
  
  /**
   * 重置状态
   */
  function reset() {
    tasks.value = []
    currentTask.value = null
    filters.value = {
      status: null,
      rule_id: null,
      date_range: null,
      search: null
    }
    pagination.value = {
      page: 1,
      page_size: 20,
      total: 0
    }
    sorting.value = {
      field: 'created_at',
      order: 'desc'
    }
  }

  // ==================== Return ====================
  
  return {
    // State
    tasks,
    currentTask,
    filters,
    pagination,
    sorting,
    loading,
    
    // Getters
    isLoading,
    tasksByStatus,
    pendingAuditCount,
    pushFailedCount,
    
    // Actions
    fetchTasks,
    fetchTaskDetail,
    uploadFile,
    updateTaskStatus,
    exportTasks,
    setFilters,
    setPagination,
    setSorting,
    setCurrentTask,
    clearCurrentTask,
    refresh,
    reset
  }
})
