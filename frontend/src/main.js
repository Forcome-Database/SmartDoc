import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import router from './router'
import App from './App.vue'
import { useAuthStore } from './stores'

// Styles
import 'ant-design-vue/dist/reset.css'
import './style.css'

const app = createApp(App)

// 创建Pinia实例
const pinia = createPinia()
app.use(pinia)

// 初始化认证状态（从localStorage恢复）
const authStore = useAuthStore()
authStore.initAuth()

app.use(router)
app.use(Antd)

app.mount('#app')
