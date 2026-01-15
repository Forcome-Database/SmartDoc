<script setup lang="ts">
/**
 * 用户管理页面
 * 支持用户列表展示、角色修改
 * 
 * Requirements: 1.6
 */
import { useDebounceFn } from '@vueuse/core'
import type { User, UserRole } from '~/types'

definePageMeta({
  middleware: ['auth'],
})

// 用户列表
const users = ref<User[]>([])
const isLoading = ref(true)
const isSaving = ref(false)

// 分页
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
  totalPages: 0,
})

// 搜索和筛选
const searchQuery = ref('')
const roleFilter = ref<string>('all')

// 角色修改对话框
const isRoleDialogOpen = ref(false)
const editingUser = ref<User | null>(null)
const selectedRole = ref<UserRole>('editor')

// Toast 通知
const toast = useToast()

// 当前用户
const userStore = useUserStore()
const currentUser = computed(() => userStore.user)

// 角色选项
const roleOptions = [
  { value: 'admin', label: '管理员', description: '拥有所有权限，可管理用户和系统设置' },
  { value: 'editor', label: '编辑者', description: '可创建和编辑文档' },
  { value: 'viewer', label: '查看者', description: '只能查看文档' },
]

// 角色标签颜色
const getRoleBadgeColor = (role: UserRole) => {
  switch (role) {
    case 'admin':
      return 'error'
    case 'editor':
      return 'primary'
    case 'viewer':
      return 'neutral'
    default:
      return 'neutral'
  }
}

// 角色显示名称
const getRoleLabel = (role: UserRole) => {
  const option = roleOptions.find(o => o.value === role)
  return option?.label || role
}

// 获取用户列表
const fetchUsers = async () => {
  isLoading.value = true
  try {
    const params = new URLSearchParams({
      page: pagination.value.page.toString(),
      pageSize: pagination.value.pageSize.toString(),
    })
    
    if (searchQuery.value.trim()) {
      params.set('q', searchQuery.value.trim())
    }
    if (roleFilter.value) {
      params.set('role', roleFilter.value)
    }

    const data = await $fetch<{
      users: User[]
      pagination: typeof pagination.value
    }>(`/api/users?${params}`)
    
    users.value = data.users
    pagination.value = data.pagination
  } catch (error: any) {
    toast.add({
      title: '获取用户列表失败',
      description: error.data?.message || '请稍后重试',
      color: 'error',
    })
  } finally {
    isLoading.value = false
  }
}

// 初始化加载
onMounted(() => {
  fetchUsers()
})

// 监听搜索和筛选变化
const debouncedSearch = useDebounceFn(() => {
  pagination.value.page = 1
  fetchUsers()
}, 300)

watch([searchQuery, roleFilter], () => {
  debouncedSearch()
})

// 打开角色修改对话框
const openRoleDialog = (user: User) => {
  editingUser.value = user
  selectedRole.value = user.role
  isRoleDialogOpen.value = true
}

// 保存角色修改
const saveRole = async () => {
  if (!editingUser.value) return
  
  isSaving.value = true
  try {
    await $fetch(`/api/users/${editingUser.value.id}`, {
      method: 'PATCH',
      body: { role: selectedRole.value },
    })
    
    toast.add({
      title: '角色已更新',
      description: `用户 "${editingUser.value.name}" 的角色已更新为 ${getRoleLabel(selectedRole.value)}`,
      color: 'success',
    })
    
    isRoleDialogOpen.value = false
    await fetchUsers()
  } catch (error: any) {
    toast.add({
      title: '更新失败',
      description: error.data?.message || '请稍后重试',
      color: 'error',
    })
  } finally {
    isSaving.value = false
  }
}

// 分页变化
const handlePageChange = (page: number) => {
  pagination.value.page = page
  fetchUsers()
}

// 格式化日期
const formatDate = (date: Date | string) => {
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}
</script>

<template>
  <div class="p-8 lg:p-12 max-w-6xl mx-auto">
    <!-- 页面标题 -->
    <div class="mb-8">
      <h1 class="text-2xl font-semibold text-gray-900 dark:text-white tracking-tight">
        用户管理
      </h1>
      <p class="text-gray-500 dark:text-gray-400 mt-1">
        管理系统用户和角色权限
      </p>
    </div>

    <!-- 搜索和筛选 -->
    <div class="flex flex-col sm:flex-row gap-4 mb-6">
      <UInput
        v-model="searchQuery"
        placeholder="搜索用户名、邮箱或部门..."
        icon="i-lucide-search"
        class="flex-1"
      />
      <USelect
        v-model="roleFilter"
        :items="[
          { value: 'all', label: '全部角色' },
          ...roleOptions.map(r => ({ value: r.value, label: r.label }))
        ]"
        class="w-full sm:w-40"
      />
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="flex items-center justify-center py-20">
      <UIcon name="i-lucide-loader-2" class="w-8 h-8 text-primary-500 animate-spin" />
    </div>

    <!-- 空状态 -->
    <div 
      v-else-if="users.length === 0" 
      class="text-center py-20 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/60 dark:border-gray-800"
    >
      <UIcon name="i-lucide-users" class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
      <p class="text-gray-500 dark:text-gray-400">
        {{ searchQuery || roleFilter ? '没有找到匹配的用户' : '暂无用户' }}
      </p>
    </div>

    <!-- 用户列表 -->
    <div 
      v-else 
      class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/60 dark:border-gray-800 overflow-hidden"
    >
      <table class="w-full">
        <thead class="bg-gray-50 dark:bg-gray-800/50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">用户</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">部门</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">角色</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">加入时间</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
          <tr v-for="user in users" :key="user.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
            <!-- 用户信息 -->
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex items-center gap-3">
                <UAvatar
                  :src="user.avatar"
                  :alt="user.name"
                  size="sm"
                />
                <div>
                  <div class="font-medium text-gray-900 dark:text-white">
                    {{ user.name }}
                    <UBadge 
                      v-if="user.id === currentUser?.id" 
                      color="primary" 
                      variant="subtle"
                      size="xs"
                      class="ml-2"
                    >
                      我
                    </UBadge>
                  </div>
                  <div class="text-sm text-gray-500 dark:text-gray-400">
                    {{ user.email || user.mobile || '-' }}
                  </div>
                </div>
              </div>
            </td>
            <!-- 部门 -->
            <td class="px-6 py-4 whitespace-nowrap">
              <span class="text-gray-600 dark:text-gray-300">
                {{ user.department || '-' }}
              </span>
            </td>
            <!-- 角色 -->
            <td class="px-6 py-4 whitespace-nowrap">
              <UBadge :color="getRoleBadgeColor(user.role)" variant="subtle">
                {{ getRoleLabel(user.role) }}
              </UBadge>
            </td>
            <!-- 加入时间 -->
            <td class="px-6 py-4 whitespace-nowrap">
              <span class="text-gray-500 dark:text-gray-400 text-sm">
                {{ formatDate(user.createdAt) }}
              </span>
            </td>
            <!-- 操作 -->
            <td class="px-6 py-4 whitespace-nowrap">
              <UButton
                variant="ghost"
                color="neutral"
                size="sm"
                icon="i-lucide-pencil"
                :disabled="user.id === currentUser?.id"
                @click="openRoleDialog(user)"
              >
                {{ user.id === currentUser?.id ? '当前用户' : '修改角色' }}
              </UButton>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 分页 -->
      <div 
        v-if="pagination.totalPages > 1" 
        class="flex items-center justify-between px-6 py-4 border-t border-gray-200/60 dark:border-gray-800"
      >
        <div class="text-sm text-gray-500 dark:text-gray-400">
          共 {{ pagination.total }} 个用户
        </div>
        <UPagination
          :model-value="pagination.page"
          :total="pagination.total"
          :page-count="pagination.pageSize"
          @update:model-value="handlePageChange"
        />
      </div>
    </div>

    <!-- 角色修改对话框 -->
    <UModal v-model:open="isRoleDialogOpen">
      <template #content>
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
              修改用户角色
            </h3>
            <UButton
              color="neutral"
              variant="ghost"
              icon="i-lucide-x"
              size="sm"
              @click="isRoleDialogOpen = false"
            />
          </div>

          <div v-if="editingUser" class="space-y-6">
            <!-- 用户信息 -->
            <div class="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <UAvatar
                :src="editingUser.avatar"
                :alt="editingUser.name"
                size="md"
              />
              <div>
                <div class="font-medium text-gray-900 dark:text-white">
                  {{ editingUser.name }}
                </div>
                <div class="text-sm text-gray-500 dark:text-gray-400">
                  {{ editingUser.department || editingUser.email || '-' }}
                </div>
              </div>
            </div>

            <!-- 角色选择 -->
            <div class="space-y-3">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
                选择角色
              </label>
              <div class="space-y-2">
                <label
                  v-for="option in roleOptions"
                  :key="option.value"
                  class="flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors"
                  :class="[
                    selectedRole === option.value
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-500/10'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  ]"
                >
                  <input
                    v-model="selectedRole"
                    type="radio"
                    :value="option.value"
                    class="mt-1"
                  />
                  <div>
                    <div class="font-medium text-gray-900 dark:text-white">
                      {{ option.label }}
                    </div>
                    <div class="text-sm text-gray-500 dark:text-gray-400">
                      {{ option.description }}
                    </div>
                  </div>
                </label>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="flex justify-end gap-3 pt-4">
              <UButton
                variant="ghost"
                color="neutral"
                @click="isRoleDialogOpen = false"
              >
                取消
              </UButton>
              <UButton
                color="primary"
                :loading="isSaving"
                :disabled="selectedRole === editingUser.role"
                @click="saveRole"
              >
                保存
              </UButton>
            </div>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
