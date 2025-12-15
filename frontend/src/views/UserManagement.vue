<template>
  <div class="user-management-page">
    <!-- 页面标题和操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">用户管理</h2>
        <p class="page-description">管理系统用户账号和权限</p>
      </div>
      <div class="header-right">
        <a-button type="primary" @click="handleCreate">
          <template #icon><PlusOutlined /></template>
          新建用户
        </a-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <a-space :size="16">
        <a-input
          v-model:value="filters.username"
          placeholder="搜索用户名"
          style="width: 200px"
          allow-clear
          @change="handleSearch"
        >
          <template #prefix><SearchOutlined /></template>
        </a-input>

        <a-input
          v-model:value="filters.email"
          placeholder="搜索邮箱"
          style="width: 200px"
          allow-clear
          @change="handleSearch"
        >
          <template #prefix><MailOutlined /></template>
        </a-input>

        <a-select
          v-model:value="filters.role"
          placeholder="筛选角色"
          style="width: 180px"
          allow-clear
          @change="handleSearch"
        >
          <a-select-option value="">全部角色</a-select-option>
          <a-select-option value="admin">超级管理员</a-select-option>
          <a-select-option value="architect">规则架构师</a-select-option>
          <a-select-option value="auditor">业务审核员</a-select-option>
          <a-select-option value="visitor">API访客</a-select-option>
        </a-select>

        <a-button @click="handleReset">重置</a-button>
      </a-space>
    </div>

    <!-- 用户列表表格 -->
    <div class="table-container">
      <a-table
        :columns="columns"
        :data-source="userList"
        :loading="loading"
        :pagination="pagination"
        :scroll="{ x: 1200 }"
        row-key="id"
        @change="handleTableChange"
      >
        <!-- 用户名列 -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'username'">
            <div class="username-cell">
              <UserOutlined class="user-icon" />
              <span>{{ record.username }}</span>
            </div>
          </template>

          <!-- 角色列 -->
          <template v-else-if="column.key === 'role'">
            <a-tag :color="getRoleColor(record.role)">
              {{ getRoleLabel(record.role) }}
            </a-tag>
          </template>

          <!-- 状态列 -->
          <template v-else-if="column.key === 'is_active'">
            <a-badge
              :status="record.is_active ? 'success' : 'default'"
              :text="record.is_active ? '正常' : '已禁用'"
            />
          </template>

          <!-- 创建时间列 -->
          <template v-else-if="column.key === 'created_at'">
            {{ formatDateTime(record.created_at) }}
          </template>

          <!-- 最后登录时间列 -->
          <template v-else-if="column.key === 'last_login_at'">
            {{ record.last_login_at ? formatDateTime(record.last_login_at) : '-' }}
          </template>

          <!-- 操作列 -->
          <template v-else-if="column.key === 'action'">
            <a-space :size="8">
              <a-button
                type="link"
                size="small"
                @click="handleEdit(record)"
              >
                编辑
              </a-button>

              <a-button
                type="link"
                size="small"
                :danger="record.is_active"
                @click="handleToggleStatus(record)"
              >
                {{ record.is_active ? '禁用' : '启用' }}
              </a-button>

              <a-popconfirm
                title="确定要删除该用户吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="handleDelete(record)"
              >
                <a-button
                  type="link"
                  size="small"
                  danger
                  :disabled="record.id === currentUserId"
                >
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 用户编辑对话框 -->
    <UserDialog
      v-model:visible="dialogVisible"
      :user="currentUser"
      @success="handleDialogSuccess"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  PlusOutlined,
  SearchOutlined,
  MailOutlined,
  UserOutlined
} from '@ant-design/icons-vue'
import { getUserList, updateUserStatus, deleteUser } from '@/api/user'
import { formatDateTime } from '@/utils/format'
import { useAuthStore } from '@/stores/authStore'
import UserDialog from '@/components/User/UserDialog.vue'

const authStore = useAuthStore()

// 当前登录用户ID
const currentUserId = computed(() => authStore.user?.id)

// 用户列表
const userList = ref([])
const loading = ref(false)

// 筛选条件
const filters = reactive({
  username: '',
  email: '',
  role: ''
})

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total) => `共 ${total} 条记录`
})

// 表格列配置
const columns = [
  {
    title: '用户名',
    dataIndex: 'username',
    key: 'username',
    width: 150,
    fixed: 'left'
  },
  {
    title: '邮箱',
    dataIndex: 'email',
    key: 'email',
    width: 200
  },
  {
    title: '角色',
    dataIndex: 'role',
    key: 'role',
    width: 150
  },
  {
    title: '状态',
    dataIndex: 'is_active',
    key: 'is_active',
    width: 100
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 180
  },
  {
    title: '最后登录',
    dataIndex: 'last_login_at',
    key: 'last_login_at',
    width: 180
  },
  {
    title: '操作',
    key: 'action',
    width: 200,
    fixed: 'right'
  }
]

// 对话框状态
const dialogVisible = ref(false)
const currentUser = ref(null)

// 获取用户列表
const fetchUserList = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      ...filters
    }

    // 移除空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })

    const response = await getUserList(params)
    userList.value = response.items || []
    pagination.total = response.total || 0
  } catch (error) {
    console.error('获取用户列表失败:', error)
    message.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.current = 1
  fetchUserList()
}

// 重置筛选
const handleReset = () => {
  filters.username = ''
  filters.email = ''
  filters.role = ''
  pagination.current = 1
  fetchUserList()
}

// 表格变化
const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchUserList()
}

// 新建用户
const handleCreate = () => {
  currentUser.value = null
  dialogVisible.value = true
}

// 编辑用户
const handleEdit = (user) => {
  currentUser.value = { ...user }
  dialogVisible.value = true
}

// 切换用户状态
const handleToggleStatus = async (user) => {
  const action = user.is_active ? '禁用' : '启用'
  
  Modal.confirm({
    title: `确定要${action}该用户吗？`,
    content: user.is_active ? '禁用后该用户将无法登录系统' : '启用后该用户可以正常登录系统',
    okText: '确定',
    cancelText: '取消',
    onOk: async () => {
      try {
        await updateUserStatus(user.id, !user.is_active)
        message.success(`${action}成功`)
        fetchUserList()
      } catch (error) {
        console.error(`${action}用户失败:`, error)
        message.error(`${action}失败，请重试`)
      }
    }
  })
}

// 删除用户
const handleDelete = async (user) => {
  try {
    await deleteUser(user.id)
    message.success('删除成功')
    
    // 如果删除的是当前页最后一条记录，且不是第一页，则回到上一页
    if (userList.value.length === 1 && pagination.current > 1) {
      pagination.current--
    }
    
    fetchUserList()
  } catch (error) {
    console.error('删除用户失败:', error)
    message.error(error.message || '删除失败，请重试')
  }
}

// 对话框成功回调
const handleDialogSuccess = () => {
  fetchUserList()
}

// 获取角色颜色
const getRoleColor = (role) => {
  const colorMap = {
    admin: 'red',
    architect: 'blue',
    auditor: 'green',
    visitor: 'default'
  }
  return colorMap[role] || 'default'
}

// 获取角色标签
const getRoleLabel = (role) => {
  const labelMap = {
    admin: '超级管理员',
    architect: '规则架构师',
    auditor: '业务审核员',
    visitor: 'API访客'
  }
  return labelMap[role] || role
}

// 页面加载时获取数据
onMounted(() => {
  fetchUserList()
})
</script>

<style scoped>
.user-management-page {
  padding: 24px;
  background: #f0f2f5;
  min-height: calc(100vh - 64px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.header-left {
  flex: 1;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #262626;
}

.page-description {
  margin: 0;
  font-size: 14px;
  color: #8c8c8c;
}

.header-right {
  display: flex;
  gap: 12px;
}

.filter-bar {
  margin-bottom: 16px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.table-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  padding: 16px;
}

.username-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-icon {
  color: #1890ff;
  font-size: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-management-page {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .filter-bar {
    overflow-x: auto;
  }

  .filter-bar :deep(.ant-space) {
    flex-wrap: wrap;
  }
}
</style>
