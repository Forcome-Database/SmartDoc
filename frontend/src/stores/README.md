# Store模块使用指南

## 概述

本目录包含所有Pinia Store模块，用于管理应用的全局状态。所有Store都使用Vue 3 Composition API风格编写。

## 目录结构

```
stores/
├── authStore.js        # 用户认证状态
├── dashboardStore.js   # 仪表盘数据
├── ruleStore.js        # 规则数据缓存
├── taskStore.js        # 任务列表状态
└── index.js            # 统一导出
```

## 使用方法

### 1. 导入Store

```javascript
// 导入单个Store
import { useTaskStore } from '@/stores'

// 导入多个Store
import { useTaskStore, useRuleStore, useAuthStore } from '@/stores'
```

### 2. 在组件中使用

```vue
<script setup>
import { useTaskStore } from '@/stores'

const taskStore = useTaskStore()

// 访问状态
console.log(taskStore.tasks)

// 访问计算属性
console.log(taskStore.isLoading)

// 调用方法
await taskStore.fetchTasks()
</script>
```

### 3. 在Options API中使用

```vue
<script>
import { useTaskStore } from '@/stores'

export default {
  computed: {
    tasks() {
      const taskStore = useTaskStore()
      return taskStore.tasks
    }
  },
  
  methods: {
    async loadTasks() {
      const taskStore = useTaskStore()
      await taskStore.fetchTasks()
    }
  }
}
</script>
```

## Store详解

### authStore - 用户认证状态

管理用户登录状态、Token和权限。

#### State

```javascript
const authStore = useAuthStore()

// 用户信息
authStore.user          // 当前用户对象
authStore.token         // 访问令牌

// 计算属性
authStore.isAuthenticated  // 是否已认证
authStore.userRole         // 用户角色
authStore.isAdmin          // 是否为管理员
authStore.isArchitect      // 是否为规则架构师
authStore.isAuditor        // 是否为审核员
authStore.isVisitor        // 是否为访客
```

#### Actions

```javascript
// 设置Token
authStore.setToken(token)

// 设置用户信息
authStore.setUser(userData)

// 登出
await authStore.logout()

// 初始化认证状态（从localStorage恢复）
authStore.initAuth()

// 检查角色权限
authStore.hasRole('admin')                    // 单个角色
authStore.hasRole(['admin', 'architect'])     // 多个角色

// 检查路由权限
authStore.canAccessRoute(route)
```

#### 使用示例

```vue
<script setup>
import { useAuthStore } from '@/stores'
import { authAPI } from '@/api'

const authStore = useAuthStore()

// 登录
async function login(username, password) {
  const response = await authAPI.login({ username, password })
  
  if (response.code === 200) {
    authStore.setToken(response.data.access_token)
    authStore.setUser(response.data.user)
  }
}

// 登出
async function logout() {
  await authStore.logout()
  router.push('/login')
}

// 权限检查
const canManageRules = authStore.hasRole(['admin', 'architect'])
</script>
```

### dashboardStore - 仪表盘数据

管理仪表盘的指标数据和图表数据。

#### State

```javascript
const dashboardStore = useDashboardStore()

// 时间范围
dashboardStore.timeRange        // 'today' | '7days' | '30days'

// 核心指标
dashboardStore.metrics          // 8个核心指标对象

// 图表数据
dashboardStore.throughputData        // 任务吞吐趋势
dashboardStore.exceptionData         // 异常分布
dashboardStore.rulePerformanceData   // 规则效能

// 加载状态
dashboardStore.loading          // 各个数据的加载状态

// 计算属性
dashboardStore.isLoading        // 是否有数据正在加载
dashboardStore.needsRefresh     // 是否需要刷新（超过5分钟）
```

#### Actions

```javascript
// 设置时间范围
dashboardStore.setTimeRange('7days')

// 加载数据
await dashboardStore.fetchMetrics()
await dashboardStore.fetchThroughput()
await dashboardStore.fetchExceptions()
await dashboardStore.fetchRulePerformance()

// 加载所有数据
await dashboardStore.fetchAll()

// 刷新数据
await dashboardStore.refresh()

// 重置状态
dashboardStore.reset()
```

#### 使用示例

```vue
<script setup>
import { useDashboardStore } from '@/stores'
import { onMounted, watch } from 'vue'

const dashboardStore = useDashboardStore()

// 组件挂载时加载数据
onMounted(async () => {
  await dashboardStore.fetchAll()
})

// 监听时间范围变化
watch(() => dashboardStore.timeRange, async () => {
  await dashboardStore.fetchAll()
})
</script>

<template>
  <div v-if="dashboardStore.isLoading">加载中...</div>
  <div v-else>
    <MetricCard 
      v-for="(value, key) in dashboardStore.metrics"
      :key="key"
      :value="value"
    />
  </div>
</template>
```

### ruleStore - 规则数据缓存

管理规则列表、版本和沙箱测试。

#### State

```javascript
const ruleStore = useRuleStore()

// 规则数据
ruleStore.rules              // 规则列表
ruleStore.currentRule        // 当前选中的规则
ruleStore.versions           // 当前规则的版本列表
ruleStore.currentVersion     // 当前选中的版本

// 筛选和分页
ruleStore.filters            // 筛选条件
ruleStore.pagination         // 分页信息

// 加载状态
ruleStore.loading            // 各个操作的加载状态

// 沙箱测试
ruleStore.sandboxResult      // 沙箱测试结果

// 计算属性
ruleStore.isLoading          // 是否有操作正在进行
ruleStore.rulesByDocType     // 按文档类型分组的规则
ruleStore.publishedVersion   // 已发布版本
ruleStore.draftVersion       // 草稿版本
```

#### Actions

```javascript
// 获取数据
await ruleStore.fetchRules()
await ruleStore.fetchRuleDetail(ruleId)
await ruleStore.fetchVersions(ruleId)

// 创建和更新
await ruleStore.createRule(data)
await ruleStore.updateVersionConfig(ruleId, version, config)

// 版本管理
await ruleStore.publishRule(ruleId)
await ruleStore.rollbackRule(ruleId, version)

// 沙箱测试
await ruleStore.testInSandbox(ruleId, formData)
ruleStore.clearSandboxResult()

// 删除
await ruleStore.deleteRule(ruleId)

// 设置状态
ruleStore.setFilters({ document_type: '发票' })
ruleStore.setPagination({ page: 2 })
ruleStore.setCurrentRule(rule)
ruleStore.setCurrentVersion(version)

// 重置
ruleStore.reset()
```

#### 使用示例

```vue
<script setup>
import { useRuleStore } from '@/stores'
import { onMounted } from 'vue'

const ruleStore = useRuleStore()

onMounted(async () => {
  await ruleStore.fetchRules()
})

// 发布规则
async function publishRule(ruleId) {
  await ruleStore.publishRule(ruleId)
  message.success('规则发布成功')
}

// 沙箱测试
async function testRule(ruleId, file) {
  const formData = new FormData()
  formData.append('file', file)
  
  await ruleStore.testInSandbox(ruleId, formData)
  
  if (ruleStore.sandboxResult) {
    console.log('测试结果:', ruleStore.sandboxResult)
  }
}
</script>

<template>
  <div>
    <!-- 按文档类型分组显示 -->
    <div v-for="(rules, docType) in ruleStore.rulesByDocType" :key="docType">
      <h3>{{ docType }}</h3>
      <RuleCard 
        v-for="rule in rules" 
        :key="rule.id"
        :rule="rule"
        @publish="publishRule"
      />
    </div>
  </div>
</template>
```

### taskStore - 任务列表状态

管理任务列表、详情和操作。

#### State

```javascript
const taskStore = useTaskStore()

// 任务数据
taskStore.tasks              // 任务列表
taskStore.currentTask        // 当前任务详情

// 筛选、分页、排序
taskStore.filters            // 筛选条件
taskStore.pagination         // 分页信息
taskStore.sorting            // 排序信息

// 加载状态
taskStore.loading            // 各个操作的加载状态

// 计算属性
taskStore.isLoading          // 是否有操作正在进行
taskStore.tasksByStatus      // 按状态分组的任务统计
taskStore.pendingAuditCount  // 待审核任务数量
taskStore.pushFailedCount    // 推送失败任务数量
```

#### Actions

```javascript
// 获取数据
await taskStore.fetchTasks()
await taskStore.fetchTaskDetail(taskId)

// 上传文件
await taskStore.uploadFile(formData)

// 更新状态
await taskStore.updateTaskStatus(taskId, { status, data })

// 导出任务
await taskStore.exportTasks({ format: 'csv' })

// 设置状态
taskStore.setFilters({ status: 'pending_audit' })
taskStore.setPagination({ page: 2, page_size: 50 })
taskStore.setSorting('created_at', 'desc')
taskStore.setCurrentTask(task)
taskStore.clearCurrentTask()

// 刷新和重置
await taskStore.refresh()
taskStore.reset()
```

#### 使用示例

```vue
<script setup>
import { useTaskStore } from '@/stores'
import { onMounted, watch } from 'vue'

const taskStore = useTaskStore()

onMounted(async () => {
  await taskStore.fetchTasks()
})

// 监听筛选条件变化
watch(() => taskStore.filters, async () => {
  await taskStore.fetchTasks()
}, { deep: true })

// 上传文件
async function uploadFile(file, ruleId) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('rule_id', ruleId)
  
  const response = await taskStore.uploadFile(formData)
  
  if (response.data.is_instant) {
    message.success('秒传成功！')
  } else {
    message.success('文件上传成功，正在处理...')
  }
}

// 导出任务
async function exportTasks() {
  await taskStore.exportTasks({
    format: 'csv',
    status: 'completed'
  })
}
</script>

<template>
  <div>
    <!-- 状态统计 -->
    <div class="stats">
      <StatCard 
        label="待审核"
        :value="taskStore.pendingAuditCount"
        type="warning"
      />
      <StatCard 
        label="推送失败"
        :value="taskStore.pushFailedCount"
        type="error"
      />
    </div>
    
    <!-- 任务列表 -->
    <TaskTable 
      :tasks="taskStore.tasks"
      :loading="taskStore.loading.list"
      :pagination="taskStore.pagination"
      @page-change="taskStore.setPagination"
    />
  </div>
</template>
```

## 最佳实践

### 1. 在setup中使用Store

```vue
<script setup>
import { useTaskStore } from '@/stores'

const taskStore = useTaskStore()

// 直接使用Store的状态和方法
</script>
```

### 2. 响应式解构

如果需要解构Store的状态，使用`storeToRefs`保持响应性：

```vue
<script setup>
import { storeToRefs } from 'pinia'
import { useTaskStore } from '@/stores'

const taskStore = useTaskStore()
const { tasks, loading } = storeToRefs(taskStore)

// tasks和loading是响应式的
</script>
```

### 3. 组合多个Store

```vue
<script setup>
import { useTaskStore, useRuleStore, useAuthStore } from '@/stores'

const taskStore = useTaskStore()
const ruleStore = useRuleStore()
const authStore = useAuthStore()

// 根据用户角色显示不同内容
const canEdit = authStore.hasRole(['admin', 'architect'])
</script>
```

### 4. 在路由守卫中使用

```javascript
// router/index.js
import { useAuthStore } from '@/stores'

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.roles && !authStore.hasRole(to.meta.roles)) {
    next('/403')
  } else {
    next()
  }
})
```

### 5. 错误处理

```vue
<script setup>
import { useTaskStore } from '@/stores'
import { message } from 'ant-design-vue'

const taskStore = useTaskStore()

async function loadTasks() {
  try {
    await taskStore.fetchTasks()
  } catch (error) {
    message.error('加载任务失败')
    console.error(error)
  }
}
</script>
```

### 6. 加载状态管理

```vue
<script setup>
import { useTaskStore } from '@/stores'

const taskStore = useTaskStore()
</script>

<template>
  <div v-if="taskStore.loading.list">
    <a-spin />
  </div>
  <div v-else>
    <!-- 内容 -->
  </div>
</template>
```

### 7. 数据刷新

```vue
<script setup>
import { useTaskStore } from '@/stores'
import { onMounted, onUnmounted } from 'vue'

const taskStore = useTaskStore()

// 定时刷新
let refreshTimer = null

onMounted(() => {
  taskStore.fetchTasks()
  
  // 每30秒刷新一次
  refreshTimer = setInterval(() => {
    taskStore.refresh()
  }, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>
```

## 调试技巧

### 1. 使用Vue DevTools

安装Vue DevTools浏览器扩展，可以查看和修改Store状态。

### 2. 打印Store状态

```javascript
const taskStore = useTaskStore()
console.log('当前状态:', taskStore.$state)
```

### 3. 监听状态变化

```javascript
import { watch } from 'vue'

const taskStore = useTaskStore()

watch(
  () => taskStore.tasks,
  (newTasks, oldTasks) => {
    console.log('任务列表变化:', newTasks)
  },
  { deep: true }
)
```

### 4. 重置Store

```javascript
// 重置单个Store
taskStore.reset()

// 重置所有Store
taskStore.$reset()
```

## 常见问题

### Q: Store的状态会在页面刷新后丢失吗？

A: 是的，Store状态存储在内存中。需要持久化的数据（如Token、用户信息）应该存储在localStorage中。authStore已经实现了自动持久化。

### Q: 如何在Store之间共享数据？

A: 可以在一个Store中导入并使用另一个Store：

```javascript
import { useAuthStore } from './authStore'

export const useTaskStore = defineStore('task', () => {
  const authStore = useAuthStore()
  
  // 使用authStore的数据
  const userId = authStore.user?.id
})
```

### Q: 如何处理并发请求？

A: Store中的loading状态可以防止重复请求：

```javascript
async function fetchTasks() {
  if (loading.value.list) return // 如果正在加载，直接返回
  
  loading.value.list = true
  try {
    // 请求逻辑
  } finally {
    loading.value.list = false
  }
}
```

### Q: 如何实现乐观更新？

A: 先更新本地状态，再发送请求：

```javascript
async function updateTask(taskId, data) {
  // 乐观更新
  const index = tasks.value.findIndex(t => t.id === taskId)
  if (index !== -1) {
    tasks.value[index] = { ...tasks.value[index], ...data }
  }
  
  try {
    await taskAPI.updateStatus(taskId, data)
  } catch (error) {
    // 失败时回滚
    await fetchTasks()
    throw error
  }
}
```

### Q: 如何清理Store状态？

A: 在组件卸载或路由离开时调用reset方法：

```vue
<script setup>
import { useTaskStore } from '@/stores'
import { onUnmounted } from 'vue'

const taskStore = useTaskStore()

onUnmounted(() => {
  taskStore.reset()
})
</script>
```
