<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>{{ appTitle }}</h1>
        <p>智能文档处理中台</p>
      </div>
      
      <a-form
        ref="formRef"
        :model="formState"
        :rules="rules"
        @finish="handleLogin"
        class="login-form"
      >
        <a-form-item name="username">
          <a-input
            v-model:value="formState.username"
            size="large"
            placeholder="用户名"
            :disabled="loading"
            @pressEnter="handleLogin"
          >
            <template #prefix>
              <UserOutlined />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item name="password">
          <a-input-password
            v-model:value="formState.password"
            size="large"
            placeholder="密码"
            :disabled="loading"
            @pressEnter="handleLogin"
          >
            <template #prefix>
              <LockOutlined />
            </template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            :loading="loading"
            block
          >
            {{ loading ? '登录中...' : '登录' }}
          </a-button>
        </a-form-item>
      </a-form>
      
      <div class="login-footer">
        <p>默认管理员账号：admin / admin123</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores'
import { authAPI } from '@/api'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const appTitle = import.meta.env.VITE_APP_TITLE || 'FORCOME文档中台'

const formRef = ref()
const formState = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度应在3-50个字符之间', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6个字符', trigger: 'blur' }
  ]
}

const loading = ref(false)

/**
 * 处理登录
 */
const handleLogin = async () => {
  try {
    // 验证表单
    await formRef.value.validate()
    
    loading.value = true
    
    // 1. 调用登录API获取token
    const loginResponse = await authAPI.login(formState)
    const token = loginResponse.access_token
    
    // 2. 保存token到store和localStorage
    authStore.setToken(token)
    
    // 3. 获取用户信息
    try {
      const userResponse = await authAPI.getCurrentUser()
      authStore.setUser(userResponse)
    } catch (userError) {
      console.error('获取用户信息失败:', userError)
      // 如果获取用户信息失败，从token中解析基本信息
      // JWT token的payload部分包含用户信息
      try {
        const payload = JSON.parse(atob(token.split('.')[1]))
        authStore.setUser({
          id: payload.sub,
          username: payload.username,
          email: payload.email,
          role: payload.role
        })
      } catch (parseError) {
        console.error('解析token失败:', parseError)
        throw new Error('无法获取用户信息')
      }
    }
    
    // 4. 显示成功消息
    message.success('登录成功')
    
    // 5. 跳转到目标页面（如果有redirect参数则跳转到该页面，否则跳转到仪表盘）
    const redirect = route.query.redirect || '/dashboard'
    router.push(redirect)
    
  } catch (error) {
    console.error('登录错误:', error)
    
    // 处理不同类型的错误
    if (error.response) {
      // 服务器返回的错误
      const status = error.response.status
      const detail = error.response.data?.detail || '登录失败'
      
      if (status === 401) {
        message.error('用户名或密码错误')
      } else if (status === 403) {
        message.error('用户已被禁用，请联系管理员')
      } else {
        message.error(detail)
      }
    } else if (error.message) {
      // 其他错误（如网络错误、解析错误）
      message.error(error.message)
    } else {
      message.error('登录失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1677ff;
  margin-bottom: 8px;
}

.login-header p {
  font-size: 14px;
  color: #666;
}

.login-form {
  margin-top: 24px;
}

.login-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 12px;
  color: #999;
}
</style>
