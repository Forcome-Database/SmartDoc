<script setup lang="ts">
/**
 * 栏目管理页面
 * 支持栏目的增删改查、拖拽排序、多语言标题编辑
 * 
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
 */
import type { CategoryNode } from '~/components/file-tree/FileTree.vue'

definePageMeta({
  middleware: ['auth'],
})

// 使用栏目管理 composable
const { 
  categories, 
  isLoading, 
  fetchCategories, 
  createCategory, 
  updateCategory, 
  deleteCategory,
  reorderCategories,
  flattenCategories,
} = useCategories()

// 语言列表
const locales = ref<Array<{ id: string; code: string; name: string; isEnabled: boolean }>>([])
const isLoadingLocales = ref(true)

// 对话框状态
const isDialogOpen = ref(false)
const editingCategory = ref<CategoryNode | null>(null)
const isDeleting = ref(false)
const deleteTarget = ref<CategoryNode | null>(null)
const isSaving = ref(false)

// 移动对话框
const isMoveDialogOpen = ref(false)
const moveTarget = ref<CategoryNode | null>(null)
const selectedParentId = ref<string | null>(null)

// 表单状态
const formState = reactive({
  slug: '',
  parentId: null as string | null,
  titles: {} as Record<string, string>,
})

// 表单验证错误
const formErrors = ref<{ name: string; message: string }[]>([])

// Toast 通知
const toast = useToast()

// 选中的栏目
const selectedCategoryId = ref<string | null>(null)

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
    fetchCategories(),
    fetchLocales(),
  ])
})

// 打开添加对话框
const openAddDialog = (parentId: string | null = null) => {
  editingCategory.value = null
  formState.slug = ''
  formState.parentId = parentId
  formState.titles = {}
  // 初始化所有启用语言的标题为空
  for (const locale of locales.value) {
    formState.titles[locale.code] = ''
  }
  formErrors.value = []
  isDialogOpen.value = true
}

// 打开编辑对话框
const openEditDialog = async (category: CategoryNode) => {
  editingCategory.value = category
  formState.slug = category.slug
  formState.parentId = category.parentId
  formState.titles = { ...category.titles }
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
  
  if (!formState.slug || formState.slug.length < 1) {
    formErrors.value.push({ name: 'slug', message: 'slug 不能为空' })
  } else if (!/^[a-z0-9-]+$/.test(formState.slug)) {
    formErrors.value.push({ name: 'slug', message: 'slug 只能包含小写字母、数字和连字符' })
  }
  
  // 检查是否所有启用语言都有标题
  for (const locale of locales.value) {
    if (!formState.titles[locale.code]?.trim()) {
      formErrors.value.push({ name: `title_${locale.code}`, message: `请输入 ${locale.name} 标题` })
    }
  }
  
  return formErrors.value.length === 0
}

// 保存栏目
const saveCategory = async () => {
  if (!validateForm()) return
  
  isSaving.value = true
  try {
    if (editingCategory.value) {
      // 更新
      await updateCategory(editingCategory.value.id, {
        slug: formState.slug,
        titles: formState.titles,
      })
      toast.add({
        title: '更新成功',
        description: `栏目已更新`,
        color: 'success',
      })
    } else {
      // 创建
      await createCategory({
        slug: formState.slug,
        parentId: formState.parentId,
        titles: formState.titles,
      })
      toast.add({
        title: '创建成功',
        description: `栏目已创建`,
        color: 'success',
      })
    }
    isDialogOpen.value = false
  } catch (error: any) {
    toast.add({
      title: editingCategory.value ? '更新失败' : '创建失败',
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
    await deleteCategory(deleteTarget.value.id)
    toast.add({
      title: '删除成功',
      description: `栏目已删除`,
      color: 'success',
    })
    isDeleting.value = false
    deleteTarget.value = null
    if (selectedCategoryId.value === deleteTarget.value?.id) {
      selectedCategoryId.value = null
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

// 处理文件树选择
const handleSelect = (item: { type: 'category' | 'document'; data: any }) => {
  if (item.type === 'category') {
    selectedCategoryId.value = item.data.id
  }
}

// 处理重命名
const handleRename = (item: { type: 'category' | 'document'; data: any }) => {
  if (item.type === 'category') {
    openEditDialog(item.data as CategoryNode)
  }
}

// 处理删除
const handleDelete = (item: { type: 'category' | 'document'; data: any }) => {
  if (item.type === 'category') {
    deleteTarget.value = item.data as CategoryNode
    isDeleting.value = true
  }
}

// 处理移动
const handleMove = (item: { type: 'category' | 'document'; data: any }) => {
  if (item.type === 'category') {
    moveTarget.value = item.data as CategoryNode
    selectedParentId.value = item.data.parentId
    isMoveDialogOpen.value = true
  }
}

// 确认移动
const confirmMove = async () => {
  if (!moveTarget.value) return
  
  isSaving.value = true
  try {
    await reorderCategories([{
      id: moveTarget.value.id,
      parentId: selectedParentId.value,
      sortOrder: 0, // 移动到新父级的第一个位置
    }])
    toast.add({
      title: '移动成功',
      description: `栏目已移动`,
      color: 'success',
    })
    isMoveDialogOpen.value = false
    moveTarget.value = null
  } catch (error: any) {
    toast.add({
      title: '移动失败',
      description: error.data?.message || '请稍后重试',
      color: 'error',
    })
  } finally {
    isSaving.value = false
  }
}

// 处理拖拽排序
const handleReorder = async (items: Array<{ id: string; parentId: string | null; sortOrder: number }>) => {
  try {
    await reorderCategories(items)
    toast.add({
      title: '排序已更新',
      color: 'success',
    })
  } catch (error: any) {
    toast.add({
      title: '排序失败',
      description: error.data?.message || '请稍后重试',
      color: 'error',
    })
    // 重新获取以恢复原顺序
    await fetchCategories()
  }
}

// 可选的父栏目列表（排除自己和子孙）
const availableParents = computed(() => {
  if (!moveTarget.value) return flattenCategories.value
  
  const targetId = moveTarget.value.id
  
  // 获取所有子孙 ID
  const getDescendantIds = (cat: CategoryNode): string[] => {
    const ids = [cat.id]
    if (cat.children) {
      for (const child of cat.children) {
        ids.push(...getDescendantIds(child))
      }
    }
    return ids
  }
  
  const excludeIds = new Set(getDescendantIds(moveTarget.value))
  
  return flattenCategories.value.filter(cat => !excludeIds.has(cat.id))
})

// 获取表单错误
const getFieldError = (name: string) => {
  return formErrors.value.find(e => e.name === name)?.message
}

// 创建文档相关状态
const isCreateDocDialogOpen = ref(false)
const createDocCategoryId = ref<string | null>(null)
const isCreatingDoc = ref(false)
const newDocForm = reactive({
  title: '',
  slug: '',
})

// 处理创建文档
const handleCreateDocument = (categoryId: string) => {
  createDocCategoryId.value = categoryId
  newDocForm.title = ''
  newDocForm.slug = ''
  isCreateDocDialogOpen.value = true
}

// 自动生成 slug
watch(() => newDocForm.title, (title) => {
  if (title && !newDocForm.slug) {
    newDocForm.slug = title
      .toLowerCase()
      .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-')
      .replace(/^-|-$/g, '')
  }
})

// 创建文档
const createDocument = async () => {
  if (!newDocForm.title.trim()) return
  
  isCreatingDoc.value = true
  try {
    const doc = await $fetch<{ id: string }>('/api/documents', {
      method: 'POST',
      body: {
        title: newDocForm.title,
        slug: newDocForm.slug || newDocForm.title.toLowerCase().replace(/\s+/g, '-'),
        categoryId: createDocCategoryId.value,
        content: '',
      },
    })
    
    isCreateDocDialogOpen.value = false
    toast.add({
      title: '文档创建成功',
      color: 'success',
    })
    
    // 跳转到新文档编辑页
    navigateTo(`/documents/${doc.id}`)
  } catch (error: any) {
    toast.add({
      title: '创建文档失败',
      description: error.data?.message || '请稍后重试',
      color: 'error',
    })
  } finally {
    isCreatingDoc.value = false
  }
}
</script>

<template>
  <div class="flex h-full">
    <!-- 左侧文件树 -->
    <div class="w-72 border-r border-gray-200 dark:border-gray-800 bg-white/50 dark:bg-gray-900/50 flex flex-col">
      <FileTree
        :categories="categories"
        :selected-id="selectedCategoryId ? `cat-${selectedCategoryId}` : null"
        :is-loading="isLoading"
        @select="handleSelect"
        @create-category="openAddDialog"
        @create-document="handleCreateDocument"
        @rename="handleRename"
        @delete="handleDelete"
        @move="handleMove"
        @reorder="handleReorder"
        @refresh="fetchCategories"
      />
    </div>

    <!-- 右侧内容区 -->
    <div class="flex-1 p-8 lg:p-12 overflow-auto">
      <!-- 页面标题 -->
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-2xl font-semibold text-gray-900 dark:text-white tracking-tight">
            栏目管理
          </h1>
          <p class="text-gray-500 dark:text-gray-400 mt-1">
            管理文档栏目结构，支持拖拽排序和多语言标题
          </p>
        </div>
        <UButton
          color="primary"
          size="md"
          class="shadow-sm shadow-primary-500/20"
          @click="openAddDialog(null)"
        >
          <UIcon name="i-lucide-folder-plus" class="w-4 h-4 mr-2" />
          新建栏目
        </UButton>
      </div>

      <!-- 提示信息 -->
      <div class="bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20 rounded-xl p-4 mb-8">
        <div class="flex items-start gap-3">
          <UIcon name="i-lucide-info" class="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
          <div class="text-sm text-blue-700 dark:text-blue-300">
            <p class="font-medium mb-1">使用提示</p>
            <ul class="list-disc list-inside space-y-1 text-blue-600 dark:text-blue-400">
              <li>在左侧文件树中右键点击栏目可进行操作</li>
              <li>拖拽栏目可调整顺序或移动到其他父栏目</li>
              <li>每个栏目需要设置所有启用语言的标题</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 统计信息 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200/60 dark:border-gray-800 p-6">
          <div class="flex items-center gap-4">
            <div class="p-3 rounded-xl bg-amber-100 dark:bg-amber-500/20">
              <UIcon name="i-lucide-folder" class="w-6 h-6 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <p class="text-2xl font-semibold text-gray-900 dark:text-white">
                {{ flattenCategories.length }}
              </p>
              <p class="text-sm text-gray-500 dark:text-gray-400">总栏目数</p>
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200/60 dark:border-gray-800 p-6">
          <div class="flex items-center gap-4">
            <div class="p-3 rounded-xl bg-blue-100 dark:bg-blue-500/20">
              <UIcon name="i-lucide-layers" class="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p class="text-2xl font-semibold text-gray-900 dark:text-white">
                {{ categories.length }}
              </p>
              <p class="text-sm text-gray-500 dark:text-gray-400">顶级栏目</p>
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200/60 dark:border-gray-800 p-6">
          <div class="flex items-center gap-4">
            <div class="p-3 rounded-xl bg-green-100 dark:bg-green-500/20">
              <UIcon name="i-lucide-languages" class="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p class="text-2xl font-semibold text-gray-900 dark:text-white">
                {{ locales.length }}
              </p>
              <p class="text-sm text-gray-500 dark:text-gray-400">支持语言</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加/编辑对话框 -->
    <UModal v-model:open="isDialogOpen">
      <template #content>
        <div class="p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
            {{ editingCategory ? '编辑栏目' : '新建栏目' }}
          </h3>
          
          <form @submit.prevent="saveCategory" class="space-y-4">
            <!-- Slug -->
            <UFormField label="Slug" :error="getFieldError('slug')" required>
              <UInput
                v-model="formState.slug"
                placeholder="例如: getting-started"
                :disabled="isSaving"
              />
              <template #hint>
                <span class="text-xs text-gray-400">URL 路径标识，只能包含小写字母、数字和连字符</span>
              </template>
            </UFormField>

            <!-- 父栏目（仅新建时显示） -->
            <UFormField v-if="!editingCategory && flattenCategories.length > 0" label="父栏目">
              <USelectMenu
                v-model="formState.parentId"
                :items="[
                  { label: '无（顶级栏目）', value: null },
                  ...flattenCategories.map(cat => ({
                    label: cat.fullPath,
                    value: cat.id,
                  }))
                ]"
                value-key="value"
                :disabled="isSaving"
              />
            </UFormField>

            <!-- 多语言标题 -->
            <div class="space-y-3">
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
                  :color="getFieldError(`title_${locale.code}`) ? 'error' : undefined"
                />
              </div>
              <p v-if="formErrors.some(e => e.name.startsWith('title_'))" class="text-sm text-red-500">
                请填写所有语言的标题
              </p>
            </div>

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
                {{ editingCategory ? '保存' : '创建' }}
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
                确定要删除栏目 "{{ deleteTarget?.titles?.zh || deleteTarget?.slug }}" 吗？
              </p>
              <p class="text-sm text-red-500 mt-2">
                注意：如果该栏目下有子栏目或文档，需要先删除或移动它们。
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

    <!-- 移动对话框 -->
    <UModal v-model:open="isMoveDialogOpen">
      <template #content>
        <div class="p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
            移动栏目
          </h3>
          
          <p class="text-gray-500 dark:text-gray-400 mb-4">
            将 "{{ moveTarget?.titles?.zh || moveTarget?.slug }}" 移动到：
          </p>

          <USelectMenu
            v-model="selectedParentId"
            :items="[
              { label: '顶级（无父栏目）', value: null },
              ...availableParents.map(cat => ({
                label: cat.fullPath,
                value: cat.id,
              }))
            ]"
            value-key="value"
            :disabled="isSaving"
            class="mb-6"
          />
          
          <div class="flex justify-end gap-3">
            <UButton
              variant="ghost"
              color="neutral"
              @click="isMoveDialogOpen = false"
            >
              取消
            </UButton>
            <UButton
              color="primary"
              :loading="isSaving"
              @click="confirmMove"
            >
              移动
            </UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- 新建文档对话框 -->
    <UModal v-model:open="isCreateDocDialogOpen">
      <template #content>
        <div class="p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            新建文档
          </h3>
          
          <div class="space-y-4">
            <UFormField label="标题" required>
              <UInput
                v-model="newDocForm.title"
                placeholder="输入文档标题"
                autofocus
              />
            </UFormField>

            <UFormField label="路径 (slug)">
              <UInput
                v-model="newDocForm.slug"
                placeholder="自动根据标题生成"
              />
            </UFormField>
          </div>

          <div class="flex justify-end gap-3 mt-6">
            <UButton
              variant="ghost"
              color="neutral"
              @click="isCreateDocDialogOpen = false"
            >
              取消
            </UButton>
            <UButton
              :loading="isCreatingDoc"
              :disabled="!newDocForm.title.trim()"
              @click="createDocument"
            >
              创建
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
