/**
 * 规则Store
 * 管理规则数据、版本和缓存
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ruleAPI } from '@/api'

export const useRuleStore = defineStore('rule', () => {
  // ==================== State ====================
  
  /**
   * 规则列表
   */
  const rules = ref([])
  
  /**
   * 当前选中的规则
   */
  const currentRule = ref(null)
  
  /**
   * 当前规则的版本列表
   */
  const versions = ref([])
  
  /**
   * 当前选中的版本
   */
  const currentVersion = ref(null)
  
  /**
   * 筛选条件
   */
  const filters = ref({
    document_type: null,
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
   * 加载状态
   */
  const loading = ref({
    list: false,
    detail: false,
    versions: false,
    saving: false,
    publishing: false,
    testing: false
  })
  
  /**
   * 沙箱测试结果
   */
  const sandboxResult = ref(null)

  // ==================== Getters ====================
  
  /**
   * 是否有任何加载中的操作
   */
  const isLoading = computed(() => {
    return Object.values(loading.value).some(v => v)
  })
  
  /**
   * 按文档类型分组的规则
   */
  const rulesByDocType = computed(() => {
    const grouped = {}
    rules.value.forEach(rule => {
      const docType = rule.document_type || '未分类'
      if (!grouped[docType]) {
        grouped[docType] = []
      }
      grouped[docType].push(rule)
    })
    return grouped
  })
  
  /**
   * 当前规则的已发布版本
   */
  const publishedVersion = computed(() => {
    return versions.value.find(v => v.status === 'published')
  })
  
  /**
   * 当前规则的草稿版本
   */
  const draftVersion = computed(() => {
    return versions.value.find(v => v.status === 'draft')
  })

  // ==================== Actions ====================
  
  /**
   * 获取规则列表
   */
  async function fetchRules() {
    loading.value.list = true
    try {
      const response = await ruleAPI.list({
        ...filters.value,
        ...pagination.value
      })
      
      if (response.code === 200) {
        rules.value = response.data.items || []
        pagination.value.total = response.data.total || 0
      }
      
      return response
    } catch (error) {
      console.error('获取规则列表失败:', error)
      throw error
    } finally {
      loading.value.list = false
    }
  }
  
  /**
   * 获取规则详情
   * @param {string} ruleId - 规则ID
   */
  async function fetchRuleDetail(ruleId) {
    loading.value.detail = true
    try {
      const response = await ruleAPI.get(ruleId)
      
      if (response.code === 200) {
        currentRule.value = response.data
      }
      
      return response
    } catch (error) {
      console.error('获取规则详情失败:', error)
      throw error
    } finally {
      loading.value.detail = false
    }
  }
  
  /**
   * 获取规则版本列表
   * @param {string} ruleId - 规则ID
   */
  async function fetchVersions(ruleId) {
    loading.value.versions = true
    try {
      const response = await ruleAPI.getVersions(ruleId)
      
      if (response.code === 200) {
        versions.value = response.data || []
      }
      
      return response
    } catch (error) {
      console.error('获取版本列表失败:', error)
      throw error
    } finally {
      loading.value.versions = false
    }
  }
  
  /**
   * 创建规则
   * @param {object} data - 规则数据
   */
  async function createRule(data) {
    loading.value.saving = true
    try {
      const response = await ruleAPI.create(data)
      
      if (response.code === 200) {
        // 刷新列表
        await fetchRules()
      }
      
      return response
    } catch (error) {
      console.error('创建规则失败:', error)
      throw error
    } finally {
      loading.value.saving = false
    }
  }
  
  /**
   * 更新规则版本配置
   * @param {string} ruleId - 规则ID
   * @param {string} version - 版本号
   * @param {object} config - 配置数据
   */
  async function updateVersionConfig(ruleId, version, config) {
    loading.value.saving = true
    try {
      const response = await ruleAPI.updateVersion(ruleId, version, config)
      
      if (response.code === 200) {
        // 刷新版本列表
        await fetchVersions(ruleId)
      }
      
      return response
    } catch (error) {
      console.error('更新版本配置失败:', error)
      throw error
    } finally {
      loading.value.saving = false
    }
  }
  
  /**
   * 发布规则版本
   * @param {string} ruleId - 规则ID
   */
  async function publishRule(ruleId) {
    loading.value.publishing = true
    try {
      const response = await ruleAPI.publish(ruleId)
      
      if (response.code === 200) {
        // 刷新版本列表和规则详情
        await Promise.all([
          fetchVersions(ruleId),
          fetchRuleDetail(ruleId)
        ])
      }
      
      return response
    } catch (error) {
      console.error('发布规则失败:', error)
      throw error
    } finally {
      loading.value.publishing = false
    }
  }
  
  /**
   * 回滚到指定版本
   * @param {string} ruleId - 规则ID
   * @param {string} version - 版本号
   */
  async function rollbackRule(ruleId, version) {
    loading.value.publishing = true
    try {
      const response = await ruleAPI.rollback(ruleId, version)
      
      if (response.code === 200) {
        // 刷新版本列表和规则详情
        await Promise.all([
          fetchVersions(ruleId),
          fetchRuleDetail(ruleId)
        ])
      }
      
      return response
    } catch (error) {
      console.error('回滚规则失败:', error)
      throw error
    } finally {
      loading.value.publishing = false
    }
  }
  
  /**
   * 沙箱测试
   * @param {string} ruleId - 规则ID
   * @param {FormData} formData - 测试文件
   */
  async function testInSandbox(ruleId, formData) {
    loading.value.testing = true
    sandboxResult.value = null
    try {
      const response = await ruleAPI.sandbox(ruleId, formData)
      
      if (response.code === 200) {
        sandboxResult.value = response.data
      }
      
      return response
    } catch (error) {
      console.error('沙箱测试失败:', error)
      throw error
    } finally {
      loading.value.testing = false
    }
  }
  
  /**
   * 删除规则
   * @param {string} ruleId - 规则ID
   */
  async function deleteRule(ruleId) {
    try {
      const response = await ruleAPI.delete(ruleId)
      
      if (response.code === 200) {
        // 刷新列表
        await fetchRules()
      }
      
      return response
    } catch (error) {
      console.error('删除规则失败:', error)
      throw error
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
   * 设置当前规则
   * @param {object} rule - 规则对象
   */
  function setCurrentRule(rule) {
    currentRule.value = rule
  }
  
  /**
   * 设置当前版本
   * @param {object} version - 版本对象
   */
  function setCurrentVersion(version) {
    currentVersion.value = version
  }
  
  /**
   * 清除沙箱测试结果
   */
  function clearSandboxResult() {
    sandboxResult.value = null
  }
  
  /**
   * 重置状态
   */
  function reset() {
    rules.value = []
    currentRule.value = null
    versions.value = []
    currentVersion.value = null
    filters.value = {
      document_type: null,
      search: null
    }
    pagination.value = {
      page: 1,
      page_size: 20,
      total: 0
    }
    sandboxResult.value = null
  }

  // ==================== Return ====================
  
  return {
    // State
    rules,
    currentRule,
    versions,
    currentVersion,
    filters,
    pagination,
    loading,
    sandboxResult,
    
    // Getters
    isLoading,
    rulesByDocType,
    publishedVersion,
    draftVersion,
    
    // Actions
    fetchRules,
    fetchRuleDetail,
    fetchVersions,
    createRule,
    updateVersionConfig,
    publishRule,
    rollbackRule,
    testInSandbox,
    deleteRule,
    setFilters,
    setPagination,
    setCurrentRule,
    setCurrentVersion,
    clearSandboxResult,
    reset
  }
})
