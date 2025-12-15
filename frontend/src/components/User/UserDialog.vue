<template>
  <a-modal
    :open="visible"
    :title="isEdit ? '编辑用户' : '新建用户'"
    :confirm-loading="loading"
    @ok="handleSubmit"
    @cancel="handleCancel"
    width="600px"
  >
    <a-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 16 }"
    >
      <a-form-item label="用户名" name="username">
        <a-input
          v-model:value="formData.username"
          placeholder="请输入用户名"
          :disabled="isEdit"
        />
      </a-form-item>

      <a-form-item label="邮箱" name="email">
        <a-input
          v-model:value="formData.email"
          placeholder="请输入邮箱"
          type="email"
        />
      </a-form-item>

      <a-form-item label="角色" name="role">
        <a-select
          v-model:value="formData.role"
          placeholder="请选择角色"
        >
          <a-select-option value="admin">超级管理员 (Admin)</a-select-option>
          <a-select-option value="architect">规则架构师 (Architect)</a-select-option>
          <a-select-option value="auditor">业务审核员 (Auditor)</a-select-option>
          <a-select-option value="visitor">API访客 (Visitor)</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item
        v-if="!isEdit"
        label="密码"
        name="password"
      >
        <a-input-password
          v-model:value="formData.password"
          placeholder="请输入密码（至少8位）"
          autocomplete="new-password"
        />
      </a-form-item>

      <a-form-item
        v-if="!isEdit"
        label="确认密码"
        name="confirmPassword"
      >
        <a-input-password
          v-model:value="formData.confirmPassword"
          placeholder="请再次输入密码"
          autocomplete="new-password"
        />
      </a-form-item>

      <a-form-item
        v-if="isEdit"
        label="修改密码"
        name="newPassword"
      >
        <a-input-password
          v-model:value="formData.newPassword"
          placeholder="留空则不修改密码"
          autocomplete="new-password"
        />
      </a-form-item>

      <a-form-item
        v-if="isEdit && formData.newPassword"
        label="确认新密码"
        name="confirmNewPassword"
      >
        <a-input-password
          v-model:value="formData.confirmNewPassword"
          placeholder="请再次输入新密码"
          autocomplete="new-password"
        />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { message } from 'ant-design-vue'
import { createUser, updateUser } from '@/api/user'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  user: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'success'])

const formRef = ref()
const loading = ref(false)
const isEdit = ref(false)

// 表单数据
const formData = reactive({
  username: '',
  email: '',
  role: '',
  password: '',
  confirmPassword: '',
  newPassword: '',
  confirmNewPassword: ''
})

// 验证规则
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为3-50个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少8位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value) => {
        if (value !== formData.password) {
          return Promise.reject('两次输入的密码不一致')
        }
        return Promise.resolve()
      },
      trigger: 'blur'
    }
  ],
  newPassword: [
    { min: 8, message: '密码至少8位', trigger: 'blur' }
  ],
  confirmNewPassword: [
    {
      validator: (rule, value) => {
        if (formData.newPassword && value !== formData.newPassword) {
          return Promise.reject('两次输入的密码不一致')
        }
        return Promise.resolve()
      },
      trigger: 'blur'
    }
  ]
}

// 重置表单
const resetForm = () => {
  formData.username = ''
  formData.email = ''
  formData.role = ''
  formData.password = ''
  formData.confirmPassword = ''
  formData.newPassword = ''
  formData.confirmNewPassword = ''
  formRef.value?.clearValidate()
}

// 监听用户数据变化
watch(() => props.user, (newUser) => {
  if (newUser) {
    isEdit.value = true
    formData.username = newUser.username
    formData.email = newUser.email
    formData.role = newUser.role
    formData.newPassword = ''
    formData.confirmNewPassword = ''
  } else {
    isEdit.value = false
    resetForm()
  }
}, { immediate: true })

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    loading.value = true

    if (isEdit.value) {
      // 编辑用户
      const updateData = {
        email: formData.email,
        role: formData.role
      }
      
      // 如果填写了新密码，则包含密码字段（后端不需要旧密码验证，因为是Admin操作）
      if (formData.newPassword) {
        updateData.password = formData.newPassword
      }

      await updateUser(props.user.id, updateData)
      message.success('用户更新成功')
    } else {
      // 创建用户
      await createUser({
        username: formData.username,
        email: formData.email,
        role: formData.role,
        password: formData.password
      })
      message.success('用户创建成功')
    }

    emit('success')
    handleCancel()
  } catch (error) {
    if (error.errorFields) {
      // 表单验证错误
      return
    }
    console.error('保存用户失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '操作失败，请重试'
    message.error(errorMsg)
  } finally {
    loading.value = false
  }
}

// 取消
const handleCancel = () => {
  resetForm()
  emit('update:visible', false)
}
</script>

<style scoped>
/* 样式可以根据需要添加 */
</style>
