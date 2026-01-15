<script setup lang="ts">
/**
 * 导航菜单管理页面
 * 支持菜单的增删改查、拖拽排序、多语言标题编辑、发布到 VitePress
 * 
 * Requirements: 5.1, 5.2
 */
import type { NavMenuNode } from '~/composables/useNavMenus'
import type { CategoryNode } from '~/composables/useCategories'

definePageMeta({
  middleware: ['auth'],
})

// 使用导航菜单管理 composable
const { 
  navMenus, 
  isLoading, 
  fetchNavMenus, 
  createNavMenu, 
  updateNavMenu, 
  deleteNavMenu,
  reorderNavMenus,
  publishNavMenus,
  flattenNavMenus,
  dropdownMenus,
  menuTypeOptions,
  targetTypeOptions,
} = useNavMenus()

// 使用栏目管理 composable（用于选择目标栏目）
const { categories, fetchCategories, flattenCategories } = useCategories()

// 语言列表
const locales = ref<Array<{ id: string; code: string; name: string; isEnabled: boolean }>>([])
const isLoadingLocales = ref(true)

// 对话框状态
const isDialogOpen = ref(false)
const editingMenu = ref<NavMenuNode | null>(null)
const isDeleting = ref(false)
const deleteTarget = ref<NavMenuNode | null>(null)
const isSaving = ref(false)
const isPublishing = ref(false)

// 表单状态
const formState = reactive({
  parentId: null as string | null,
  type: 'link' as 'link' | 'dropdown' | 'divider',
  targetType: 'none' as 'category' | 'document' | 'external' | 'none',
  targetId: null as string | null,
  externalUrl: '',
  openInNewTab: false,
  icon: '',
  isVisible: true,
  titles: {} as Record<string, string>,
})

// 表单验证错误
const formErrors = ref<{ name: string; message: string }[]>([])

// Toast 通知
const toast = useToast()

// 选中的菜单
const selectedMenuId = ref<string | null>(null)

// 获取语言列表
const fetchLocales = async () => {
  isLoadingLocales.value = true
  try {
    const data = await $fetch<Array<{ id: string; code: string; name: string; isEnabled: boolean }>>('/api/locales')
    locales.value = data.filter(l => l.isEnabled)
  } catch (error: any) {
    toast.add({
      title: '获取语言列表失败',
      description: error.data?.message || '请稍后重试',
      color: 'error',
    })
  } finally {
    isLoadingLocales.value = false
  }
}

// 初始化加载
onMounted(async () => {
  await Promise.all([
    fetchNavMenus(),
    fetchLocales(),
    fetchCategories(),
  ])
})

// 重置表单
const resetForm = () => {
  formState.parentId = null
  formState.type = 'link'
  formState.targetType = 'none'
  formState.targetId = null
  formState.externalUrl = ''
  formState.openInNewTab = false
  formState.icon = ''
  formState.isVisible = true
  formState.titles = {}
  // 初始化所有启用语言的标题为空
  for (const locale of locales.value) {
    formState.titles[locale.code] = ''
  }
  formErrors.value = []
}

// 打开添加对话框
const openAddDialog = (parentId: string | null = null) => {
  editingMenu.value = null
  resetForm()
  formState.parentId = parentId
  isDialogOpen.value = true
}

// 打开编辑对话框
const openEditDialog = (menu: NavMenuNode) => {
  editingMenu.value = menu
  formState.parentId = menu.parentId
  formState.type = menu.type
  formState.targetType = menu.targetType
  formState.targetId = menu.targetId
  formState.externalUrl = menu.externalUrl || ''
  formState.openInNewTab = menu.openInNewTab
  formState.icon = menu.icon || ''
  formState.isVisible = menu.isVisible
  formState.titles = { ...menu.titles }
  // 确保所有启用语言都有标题字段
  for (const locale of locales.value) {
    if (!formState.titles[locale.code]) {
      formState.titles[locale.code] = ''
    }
  }
  formErrors.value = []
  isDialogOpen.value = true
}

// 验证表单
const validateForm = (): boolean => {
  formErrors.value = []
  
  // 分割线不需要标题
  if (formState.type !== 'divider') {
    // 检查是否至少有一个语言的标题
    const hasTitle = Object.values(formState.titles).some(t => t?.trim())
    if (!hasTitle) {
      formErrors.value.push({ name: 'titles', message: '请至少输入一个语言的标题' })
    }
  }
  
  // 外部链接需要 URL
  if (formState.targetType === 'external' && !formState.externalUrl?.trim()) {
    formErrors.value.push({ name: 'externalUrl', message: '请输入外部链接 URL' })
  }
  
  // 验证 URL 格式
  if (formState.externalUrl?.trim()) {
    try {
      new URL(formState.externalUrl)
    } catch {
      formErrors.value.push({ name: 'externalUrl', message: '请输入有效的 URL' })
    }
  }
  
  return formErrors.value.length === 0
}

// 保存菜单
const saveMenu = async () => {
  if (!validateForm()) return
  
  isSaving.value = true
  try {
    const data = {
      parentId: formState.parentId,
      type: formState.type,
      targetType: formState.targetType,
      targetId: formState.targetId,
      externalUrl: formState.externalUrl || null,
      openInNewTab: formState.openInNewTab,
      icon: formState.icon || null,
      isVisible: formState.isVisible,
      titles: formState.titles,
    }
    
    if (editingMenu.value) {
      // 更新
      await updateNavMenu(editingMenu.value.id, data)
      toast.add({
        title: '更新成功',
        description: '菜单项已更新',
        color: 'success',
      })
    } else {
      // 创建
      await createNavMenu(data)
      toast.add({
        title: '创建成功',
        description: '菜单项已创建',
        color: 'success',
      })
    }
    isDialogOpen.value = false
  } catch (error: any) {
    toast.add({
      title: editingMenu.value ? '更新失败' : '创建失败',
      description: error.data?.message || '请稍后重试',
      color: 'error',
    })
  } finally {
    isSaving.value = false
  }
}

// 确认删除
const confirmDelete = async () => {
  if (!deleteTarget.value) return
  
  isSaving.value = true
  try {
    await deleteNavMenu(deleteTarget.value.id)
    toast.add({
      title: '删除成功',
      description: '菜单项已删除',
      color: 'success',
    })
    isDeleting.value = false
    deleteTarget.value = null
    if (selectedMenuId.value === deleteTarget.value?.id) {
      selectedMenuId.value = null
    }
  } catch (error: any) {
    toast.add({
      title: '删除失败',
      description: error.data?.message || '请稍后重试',
      color: 'error',
    })
  } finally {
    isSaving.value = false
  }
}

// 发布到 VitePress
const handlePublish = async () => {
  isPublishing.value = true
  try {
    const result = await publishNavMenus()
    toast.add({
      title: '发布成功',
      description: `已生成 ${result.locales.length} 种语言的导航配置`,
      color: 'success',
    })
  } catch (error: any) {
    toast.add({
      title: '发布失败',
      description: error.data?.message || '请稍后重试',
      color: 'error',
    })
  } finally {
    isPublishing.value = false
  }
}

// 切换可见性
const toggleVisibility = async (menu: NavMenuNode) => {
  try {
    await updateNavMenu(menu.id, { isVisible: !menu.isVisible })
    toast.add({
      title: menu.isVisible ? '已隐藏' : '已显示',
      color: 'success',
    })
  } catch (error: any) {
    toast.add({
      title: '操作失败',
      description: error.data?.message || '请稍后重试',
      color: 'error',
    })
  }
}

// 获取菜单类型图标
const getTypeIcon = (type: string) => {
  const option = menuTypeOptions.find(o => o.value === type)
  return option?.icon || 'i-lucide-circle'
}

// 获取菜单类型标签
const getTypeLabel = (type: string) => {
  const option = menuTypeOptions.find(o => o.value === type)
  return option?.label || type
}

// 获取目标类型标签
const getTargetTypeLabel = (type: string) => {
  const option = targetTypeOptions.find(o => o.value === type)
  return option?.label || type
}

// 获取表单错误
const getFieldError = (name: string) => {
  return formErrors.value.find(e => e.name === name)?.message
}

// 获取菜单显示标题
const getMenuTitle = (menu: NavMenuNode) => {
  return menu.titles['zh'] || menu.titles['en'] || menu.titles['vi'] || `菜单 ${menu.id.slice(0, 8)}`
}
</script>

<template>
  <div class="p-8 lg:p-12 max-w-6xl mx-auto">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-semibold text-gray-900 dark:text-white tracking-tight">
          导航菜单管理
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          管理网站顶部导航菜单，支持多级下拉和多语言
        </p>
      </div>
      <div class="flex items-center gap-3">
        <UButton
          variant="outline"
          color="neutral"
          :loading="isPublishing"
          @click="handlePublish"
        >
          <UIcon name="i-lucide-upload" class="w-4 h-4 mr-2" />
          发布到 VitePress
        </UButton>
        <UButton
          color="primary"
          class="shadow-sm shadow-primary-500/20"
          @click="openAddDialog(null)"
        >
          <UIcon name="i-lucide-plus" class="w-4 h-4 mr-2" />
          新建菜单项
        </UButton>
      </div>
    </div>

    <!-- 提示信息 -->
    <div class="bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20 rounded-xl p-4 mb-8">
      <div class="flex items-start gap-3">
        <UIcon name="i-lucide-info" class="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
        <div class="text-sm text-blue-700 dark:text-blue-300">
          <p class="font-medium mb-1">使用提示</p>
          <ul class="list-disc list-inside space-y-1 text-blue-600 dark:text-blue-400">
            <li>链接类型可指向栏目、文档或外部链接</li>
            <li>下拉菜单可包含子菜单项</li>
            <li>分割线用于在下拉菜单中分隔不同组</li>
            <li>修改后需点击"发布到 VitePress"才能生效</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- 菜单列表 -->
    <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200/60 dark:border-gray-800 overflow-hidden">
      <!-- 加载状态 -->
      <div v-if="isLoading" class="p-12 text-center">
        <UIcon name="i-lucide-loader-2" class="w-8 h-8 text-gray-400 animate-spin mx-auto" />
        <p class="text-gray-500 mt-4">加载中...</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="navMenus.length === 0" class="p-12 text-center">
        <UIcon name="i-lucide-menu" class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto" />
        <p class="text-gray-500 dark:text-gray-400 mt-4">暂无导航菜单</p>
        <UButton
          color="primary"
          variant="soft"
          class="mt-4"
          @click="openAddDialog(null)"
        >
          创建第一个菜单项
        </UButton>
      </div>

      <!-- 菜单树 -->
      <div v-else class="divide-y divide-gray-100 dark:divide-gray-800">
        <template v-for="menu in navMenus" :key="menu.id">
          <NavMenuItem
            :menu="menu"
            :level="0"
            @edit="openEditDialog"
            @delete="(m) => { deleteTarget = m; isDeleting = true }"
            @add-child="openAddDialog"
            @toggle-visibility="toggleVisibility"
          />
        </template>
      </div>
    </div>

    <!-- 添加/编辑对话框 -->
    <UModal v-model:open="isDialogOpen" :ui="{ width: 'max-w-2xl' }">
      <template #content>
        <div class="p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
            {{ editingMenu ? '编辑菜单项' : '新建菜单项' }}
          </h3>
          
          <form @submit.prevent="saveMenu" class="space-y-5">
            <!-- 菜单类型 -->
            <UFormField label="菜单类型" required>
              <USelectMenu
                v-model="formState.type"
                :items="menuTypeOptions"
                value-key="value"
                :disabled="isSaving"
              >
                <template #leading="{ item }">
                  <UIcon v-if="item?.icon" :name="item.icon" class="w-4 h-4" />
                </template>
              </USelectMenu>
            </UFormField>

            <!-- 父菜单（仅当有下拉菜单时显示） -->
            <UFormField v-if="dropdownMenus.length > 0" label="父菜单">
              <USelectMenu
                v-model="formState.parentId"
                :items="[
                  { label: '无（顶级菜单）', value: null },
                  ...dropdownMenus
                    .filter(m => m.id !== editingMenu?.id)
                    .map(m => ({
                      label: m.fullPath,
                      value: m.id,
                    }))
                ]"
                value-key="value"
                :disabled="isSaving"
              />
            </UFormField>

            <!-- 多语言标题（分割线除外） -->
            <div v-if="formState.type !== 'divider'" class="space-y-3">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                多语言标题 <span class="text-red-500">*</span>
              </label>
              <div 
                v-for="locale in locales" 
                :key="locale.code"
                class="flex items-center gap-3"
              >
                <span class="w-16 text-sm text-gray-500 dark:text-gray-400 shrink-0">
                  {{ locale.name }}
                </span>
                <UInput
                  v-model="formState.titles[locale.code]"
                  :placeholder="`输入 ${locale.name} 标题`"
                  :disabled="isSaving"
                  class="flex-1"
                />
              </div>
              <p v-if="getFieldError('titles')" class="text-sm text-red-500">
                {{ getFieldError('titles') }}
              </p>
            </div>

            <!-- 目标类型（仅链接类型） -->
            <UFormField v-if="formState.type === 'link'" label="链接目标" required>
              <USelectMenu
                v-model="formState.targetType"
                :items="targetTypeOptions"
                value-key="value"
                :disabled="isSaving"
              >
                <template #leading="{ item }">
                  <UIcon v-if="item?.icon" :name="item.icon" class="w-4 h-4" />
                </template>
              </USelectMenu>
            </UFormField>

            <!-- 目标栏目选择 -->
            <UFormField v-if="formState.type === 'link' && formState.targetType === 'category'" label="选择栏目">
              <USelectMenu
                v-model="formState.targetId"
                :items="flattenCategories.map(cat => ({
                  label: cat.fullPath,
                  value: cat.id,
                }))"
                value-key="value"
                placeholder="选择目标栏目"
                :disabled="isSaving"
              />
            </UFormField>

            <!-- 外部链接 URL -->
            <UFormField 
              v-if="formState.type === 'link' && formState.targetType === 'external'" 
              label="外部链接 URL"
              :error="getFieldError('externalUrl')"
              required
            >
              <UInput
                v-model="formState.externalUrl"
                placeholder="https://example.com"
                :disabled="isSaving"
              />
            </UFormField>

            <!-- 新窗口打开 -->
            <UFormField v-if="formState.type === 'link'">
              <UCheckbox
                v-model="formState.openInNewTab"
                label="在新窗口打开"
                :disabled="isSaving"
              />
            </UFormField>

            <!-- 图标 -->
            <UFormField v-if="formState.type !== 'divider'" label="图标（可选）">
              <UInput
                v-model="formState.icon"
                placeholder="例如: i-lucide-home"
                :disabled="isSaving"
              />
              <template #hint>
                <span class="text-xs text-gray-400">使用 Iconify 图标名称</span>
              </template>
            </UFormField>

            <!-- 可见性 -->
            <UFormField>
              <UCheckbox
                v-model="formState.isVisible"
                label="在导航中显示"
                :disabled="isSaving"
              />
            </UFormField>

            <!-- 操作按钮 -->
            <div class="flex justify-end gap-3 pt-4">
              <UButton
                variant="ghost"
                color="neutral"
                :disabled="isSaving"
                @click="isDialogOpen = false"
              >
                取消
              </UButton>
              <UButton
                type="submit"
                color="primary"
                :loading="isSaving"
              >
                {{ editingMenu ? '保存' : '创建' }}
              </UButton>
            </div>
          </form>
        </div>
      </template>
    </UModal>

    <!-- 删除确认对话框 -->
    <UModal v-model:open="isDeleting">
      <template #content>
        <div class="p-6">
          <div class="flex items-start gap-4">
            <div class="p-3 rounded-full bg-red-100 dark:bg-red-500/20">
              <UIcon name="i-lucide-alert-triangle" class="w-6 h-6 text-red-600 dark:text-red-400" />
            </div>
            <div class="flex-1">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                确认删除
              </h3>
              <p class="text-gray-500 dark:text-gray-400 mt-2">
                确定要删除菜单项 "{{ deleteTarget ? getMenuTitle(deleteTarget) : '' }}" 吗？
              </p>
              <p v-if="deleteTarget?.children?.length" class="text-sm text-red-500 mt-2">
                注意：该菜单下有 {{ deleteTarget.children.length }} 个子菜单，需要先删除或移动它们。
              </p>
            </div>
          </div>
          
          <div class="flex justify-end gap-3 mt-6">
            <UButton
              variant="ghost"
              color="neutral"
              @click="isDeleting = false"
            >
              取消
            </UButton>
            <UButton
              color="error"
              :loading="isSaving"
              @click="confirmDelete"
            >
              删除
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
