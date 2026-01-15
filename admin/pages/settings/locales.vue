<script setup lang="ts">
/**
 * 语言管理页面
 * 支持语言的增删改查、拖拽排序、启用/禁用
 * 
 * Requirements: 6.9
 */
import type { Locale } from '~/types'

definePageMeta({
  middleware: ['auth'],
})

// 语言列表
const locales = ref<Locale[]>([])
const isLoading = ref(true)
const isSaving = ref(false)

// 对话框状态
const isDialogOpen = ref(false)
const editingLocale = ref<Locale | null>(null)
const isDeleting = ref(false)
const deleteTarget = ref<Locale | null>(null)

// 表单状态
const formState = reactive({
  code: '',
  name: '',
  nativeName: '',
  isDefault: false,
  isEnabled: true,
})

// 表单验证错误
const formErrors = ref<{ name: string; message: string }[]>([])

// Toast 通知
const toast = useToast()

// 获取语言列表
const fetchLocales = async () => {
  isLoading.value = true
  try {
    const data = await $fetch<Locale[]>('/api/locales')
    locales.value = data
  } catch (error: any) {
    toast.add({
      title: '获取语言列表失败',
      description: error.data?.message || '请稍后重试',
      color: 'error',
    })
  } finally {
    isLoading.value = false
  }
}

// 初始化加载
onMounted(() => {
  fetchLocales()
})

// 打开添加对话框
const openAddDialog = () => {
  editingLocale.value = null
  formState.code = ''
  formState.name = ''
  formState.nativeName = ''
  formState.isDefault = false
  formState.isEnabled = true
  formErrors.value = []
  isDialogOpen.value = true
}

// 打开编辑对话框
const openEditDialog = (locale: Locale) => {
  editingLocale.value = locale
  formState.code = locale.code
  formState.name = locale.name
  formState.nativeName = locale.nativeName
  formState.isDefault = locale.isDefault
  formState.isEnabled = locale.isEnabled
  formErrors.value = []
  isDialogOpen.value = true
}

// 验证表单
const validateForm = (): boolean => {
  formErrors.value = []
  
  if (!formState.code || formState.code.length < 2) {
    formErrors.value.push({ name: 'code', message: '语言代码至少需要 2 个字符' })
  }
  if (!formState.name) {
    formErrors.value.push({ name: 'name', message: '请输入语言名称' })
  }
  if (!formState.nativeName) {
    formErrors.value.push({ name: 'nativeName', message: '请输入本地名称' })
  }
  
  return formErrors.value.length === 0
}

// 保存语言
const saveLocale = async () => {
  if (!validateForm()) return
  
  isSaving.value = true
  try {
    if (editingLocale.value) {
      // 更新
      await $fetch(`/api/locales/${editingLocale.value.id}`, {
        method: 'PATCH',
        body: formState,
      })
      toast.add({
        title: '更新成功',
        description: `语言 "${formState.name}" 已更新`,
        color: 'success',
      })
    } else {
      // 创建
      await $fetch('/api/locales', {
        method: 'POST',
        body: formState,
      })
      toast.add({
        title: '添加成功',
        description: `语言 "${formState.name}" 已添加`,
        color: 'success',
      })
    }
    isDialogOpen.value = false
    await fetchLocales()
  } catch (error: any) {
    toast.add({
      title: editingLocale.value ? '更新失败' : '添加失败',
      description: error.data?.message || '请稍后重试',
      color: 'error',
    })
  } finally {
    isSaving.value = false
  }
}

// 切换启用状态
const toggleEnabled = async (locale: Locale) => {
  try {
    await $fetch(`/api/locales/${locale.id}`, {
      method: 'PATCH',
      body: { isEnabled: !locale.isEnabled },
    })
    toast.add({
      title: locale.isEnabled ? '已禁用' : '已启用',
      description: `语言 "${locale.name}" ${locale.isEnabled ? '已禁用' : '已启用'}`,
      color: 'success',
    })
    await fetchLocales()
  } catch (error: any) {
    toast.add({
      title: '操作失败',
      description: error.data?.message || '请稍后重试',
      color: 'error',
    })
  }
}

// 确认删除
const confirmDelete = async () => {
  if (!deleteTarget.value) return
  
  isSaving.value = true
  try {
    await $fetch(`/api/locales/${deleteTarget.value.id}`, {
      method: 'DELETE',
    })
    toast.add({
      title: '删除成功',
      description: `语言 "${deleteTarget.value.name}" 已删除`,
      color: 'success',
    })
    isDeleting.value = false
    deleteTarget.value = null
    await fetchLocales()
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

// 处理拖拽排序
const handleReorder = async (newOrder: string[]) => {
  try {
    await $fetch('/api/locales/reorder', {
      method: 'POST',
      body: { ids: newOrder },
    })
    toast.add({
      title: '排序已更新',
      color: 'success',
    })
    await fetchLocales()
  } catch (error: any) {
    toast.add({
      title: '排序失败',
      description: error.data?.message || '请稍后重试',
      color: 'error',
    })
    // 重新获取以恢复原顺序
    await fetchLocales()
  }
}
</script>

<template>
  <div class="p-8 lg:p-12 max-w-4xl mx-auto">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-semibold text-gray-900 dark:text-white tracking-tight">
          语言管理
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          管理系统支持的语言，拖拽调整显示顺序
        </p>
      </div>
      <UButton
        color="primary"
        size="md"
        class="shadow-sm shadow-primary-500/20"
        @click="openAddDialog"
      >
        <UIcon name="i-lucide-plus" class="w-4 h-4 mr-2" />
        添加语言
      </UButton>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="flex items-center justify-center py-20">
      <UIcon name="i-lucide-loader-2" class="w-8 h-8 text-primary-500 animate-spin" />
    </div>

    <!-- 空状态 -->
    <div 
      v-else-if="locales.length === 0" 
      class="text-center py-20 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/60 dark:border-gray-800"
    >
      <UIcon name="i-lucide-languages" class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
      <p class="text-gray-500 dark:text-gray-400 mb-4">暂无语言配置</p>
      <UButton color="primary" @click="openAddDialog">
        <UIcon name="i-lucide-plus" class="w-4 h-4 mr-2" />
        添加第一个语言
      </UButton>
    </div>

    <!-- 语言列表 -->
    <div 
      v-else 
      class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/60 dark:border-gray-800 overflow-hidden"
    >
      <SettingsLocaleTable
        :locales="locales"
        @edit="openEditDialog"
        @delete="(locale) => { deleteTarget = locale; isDeleting = true }"
        @toggle-enabled="toggleEnabled"
        @reorder="handleReorder"
      />
    </div>

    <!-- 添加/编辑对话框 -->
    <UModal v-model:open="isDialogOpen">
      <template #content>
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ editingLocale ? '编辑语言' : '添加语言' }}
            </h3>
            <UButton
              color="neutral"
              variant="ghost"
              icon="i-lucide-x"
              size="sm"
              @click="isDialogOpen = false"
            />
          </div>

          <SettingsLocaleForm
            :form-state="formState"
            :form-errors="formErrors"
            :is-saving="isSaving"
            :is-editing="!!editingLocale"
            @submit="saveLocale"
            @cancel="isDialogOpen = false"
          />
        </div>
      </template>
    </UModal>

    <!-- 删除确认对话框 -->
    <UModal v-model:open="isDeleting">
      <template #content>
        <div class="p-6">
          <div class="flex items-start gap-4">
            <div class="p-2 rounded-full bg-red-100 dark:bg-red-500/20">
              <UIcon name="i-lucide-alert-triangle" class="w-5 h-5 text-red-600 dark:text-red-400" />
            </div>
            <div class="flex-1">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                确认删除
              </h3>
              <p class="text-gray-500 dark:text-gray-400 mt-2">
                确定要删除语言 "{{ deleteTarget?.name }}" 吗？此操作无法撤销。
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
