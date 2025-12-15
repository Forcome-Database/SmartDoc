import { defineStore } from 'pinia'
import { dashboardAPI } from '@/api/dashboard'

/**
 * 仪表盘状态管理
 */
export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    // 时间范围
    timeRange: '7days',
    
    // 核心指标
    metrics: {
      total_tasks: 0,
      total_tasks_trend: 0,
      total_pages: 0,
      total_pages_trend: 0,
      processing_tasks: 0,
      processing_tasks_trend: 0,
      pending_audit_tasks: 0,
      pending_audit_tasks_trend: 0,
      push_failed_tasks: 0,
      stp_rate: 0,
      stp_rate_trend: 0,
      cost_saving: null,
      llm_cost: null
    },
    
    // 任务吞吐数据
    throughputData: [],
    
    // 异常分布数据
    exceptionData: [],
    
    // 规则效能数据
    rulePerformanceData: [],
    
    // 加载状态
    loading: {
      metrics: false,
      throughput: false,
      exceptions: false,
      rulePerformance: false
    },
    
    // 缓存时间戳
    lastUpdate: null
  }),
  
  getters: {
    /**
     * 是否有任何数据正在加载
     */
    isLoading: (state) => {
      return Object.values(state.loading).some(v => v)
    },
    
    /**
     * 数据是否需要刷新（超过5分钟）
     */
    needsRefresh: (state) => {
      if (!state.lastUpdate) return true
      const fiveMinutes = 5 * 60 * 1000
      return Date.now() - state.lastUpdate > fiveMinutes
    }
  },
  
  actions: {
    /**
     * 设置时间范围
     */
    setTimeRange(range) {
      this.timeRange = range
    },
    
    /**
     * 加载核心指标
     */
    async fetchMetrics() {
      this.loading.metrics = true
      try {
        const response = await dashboardAPI.getMetrics({
          time_range: this.timeRange
        })
        
        if (response.code === 200) {
          this.metrics = response.data
          this.lastUpdate = Date.now()
        }
        
        return response
      } catch (error) {
        console.error('加载指标失败:', error)
        throw error
      } finally {
        this.loading.metrics = false
      }
    },
    
    /**
     * 加载任务吞吐趋势
     */
    async fetchThroughput() {
      this.loading.throughput = true
      try {
        const response = await dashboardAPI.getThroughput({
          time_range: this.timeRange
        })
        
        if (response.code === 200) {
          this.throughputData = response.data || []
        }
        
        return response
      } catch (error) {
        console.error('加载吞吐趋势失败:', error)
        throw error
      } finally {
        this.loading.throughput = false
      }
    },
    
    /**
     * 加载异常分布
     */
    async fetchExceptions() {
      this.loading.exceptions = true
      try {
        const response = await dashboardAPI.getExceptions({
          time_range: this.timeRange
        })
        
        if (response.code === 200) {
          this.exceptionData = response.data || []
        }
        
        return response
      } catch (error) {
        console.error('加载异常分布失败:', error)
        throw error
      } finally {
        this.loading.exceptions = false
      }
    },
    
    /**
     * 加载规则效能
     */
    async fetchRulePerformance() {
      this.loading.rulePerformance = true
      try {
        const response = await dashboardAPI.getRulePerformance({
          time_range: this.timeRange
        })
        
        if (response.code === 200) {
          this.rulePerformanceData = response.data || []
        }
        
        return response
      } catch (error) {
        console.error('加载规则效能失败:', error)
        throw error
      } finally {
        this.loading.rulePerformance = false
      }
    },
    
    /**
     * 加载所有数据
     */
    async fetchAll() {
      await Promise.all([
        this.fetchMetrics(),
        this.fetchThroughput(),
        this.fetchExceptions(),
        this.fetchRulePerformance()
      ])
    },
    
    /**
     * 刷新数据
     */
    async refresh() {
      await this.fetchAll()
    },
    
    /**
     * 重置状态
     */
    reset() {
      this.timeRange = '7days'
      this.metrics = {
        total_tasks: 0,
        total_tasks_trend: 0,
        total_pages: 0,
        total_pages_trend: 0,
        processing_tasks: 0,
        processing_tasks_trend: 0,
        pending_audit_tasks: 0,
        pending_audit_tasks_trend: 0,
        push_failed_tasks: 0,
        stp_rate: 0,
        stp_rate_trend: 0,
        cost_saving: null,
        llm_cost: null
      }
      this.throughputData = []
      this.exceptionData = []
      this.rulePerformanceData = []
      this.lastUpdate = null
    }
  }
})
