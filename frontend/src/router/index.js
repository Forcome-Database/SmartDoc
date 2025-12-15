import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores'
import MainLayout from '@/components/Layout/MainLayout.vue'

/**
 * 路由配置
 * 使用懒加载优化首屏加载性能
 */
const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { 
      requiresAuth: false,
      title: '登录'
    }
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { 
          title: '仪表盘',
          icon: 'DashboardOutlined'
        }
      },
      {
        path: 'rules',
        name: 'RuleList',
        component: () => import('@/views/RuleList.vue'),
        meta: { 
          title: '规则管理',
          icon: 'FileTextOutlined'
          // 临时移除角色限制用于测试
          // roles: ['admin', 'architect']
        }
      },
      {
        path: 'rules/:id/edit',
        name: 'RuleEditor',
        component: () => import('@/views/RuleEditor.vue'),
        meta: { 
          title: '规则编辑器',
          hidden: true
          // 临时移除角色限制用于测试
          // roles: ['admin', 'architect']
        }
      },
      {
        path: 'pipelines',
        name: 'PipelineList',
        component: () => import('@/views/Pipeline/PipelineList.vue'),
        meta: { 
          title: '数据管道',
          icon: 'ApiOutlined'
          // 临时移除角色限制用于测试
          // roles: ['admin', 'architect']
        }
      },
      {
        path: 'upload',
        name: 'DocumentUpload',
        component: () => import('@/views/DocumentUpload.vue'),
        meta: { 
          title: '文档上传',
          icon: 'CloudUploadOutlined'
        }
      },
      {
        path: 'tasks',
        name: 'TaskList',
        component: () => import('@/views/TaskList.vue'),
        meta: { 
          title: '任务列表',
          icon: 'UnorderedListOutlined'
        }
      },
      {
        path: 'audit',
        name: 'ManualReview',
        component: () => import('@/views/ManualReview.vue'),
        meta: { 
          title: '人工审核',
          icon: 'AuditOutlined',
          roles: ['admin', 'auditor']
        }
      },
      {
        path: 'audit/detail',
        name: 'ReviewDetail',
        component: () => import('@/views/ReviewDetail.vue'),
        meta: { 
          title: '审核详情',
          hidden: true,
          roles: ['admin', 'auditor']
        }
      },
      {
        path: 'webhooks',
        name: 'WebhookConfig',
        component: () => import('@/views/WebhookConfig.vue'),
        meta: { 
          title: 'Webhook配置',
          icon: 'ApiOutlined'
          // 临时移除角色限制用于测试
          // roles: ['admin']
        }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: () => import('@/views/UserManagement.vue'),
        meta: { 
          title: '用户管理',
          icon: 'TeamOutlined',
          roles: ['admin']
        }
      },
      {
        path: 'settings',
        name: 'SystemSettings',
        component: () => import('@/views/SystemSettings.vue'),
        meta: { 
          title: '系统设置',
          icon: 'SettingOutlined',
          roles: ['admin']
        }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { 
      requiresAuth: false,
      title: '页面不存在'
    }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

/**
 * 全局前置守卫
 * 1. 验证用户登录状态
 * 2. 检查路由权限
 * 3. 设置页面标题
 */
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.meta.requiresAuth !== false // 默认需要认证
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - Enterprise IDP Platform`
  }
  
  // 检查登录状态
  if (requiresAuth && !authStore.isAuthenticated) {
    // 未登录，重定向到登录页
    next({ 
      name: 'Login', 
      query: { redirect: to.fullPath } 
    })
    return
  }
  
  // 已登录用户访问登录页，重定向到首页
  if (to.name === 'Login' && authStore.isAuthenticated) {
    next({ path: '/dashboard' })
    return
  }
  
  // 检查角色权限
  if (to.meta.roles && authStore.user) {
    const userRole = authStore.user.role
    if (!to.meta.roles.includes(userRole)) {
      // 无权限访问，重定向到首页
      next({ path: '/dashboard' })
      return
    }
  }
  
  next()
})

/**
 * 全局后置钩子
 * 用于页面加载完成后的处理
 */
router.afterEach(() => {
  // 可以在这里添加页面加载完成后的逻辑
  // 例如：关闭加载动画、埋点统计等
})

export default router
