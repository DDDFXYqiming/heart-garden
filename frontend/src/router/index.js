import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('@/views/HomePage.vue') },
  { path: '/login', name: 'Login', component: () => import('@/views/LoginPage.vue') },
  { path: '/register', name: 'Register', component: () => import('@/views/RegisterPage.vue') },
  { path: '/diaries', name: 'Diaries', component: () => import('@/views/DiaryList.vue') },
  { path: '/diary/new', name: 'DiaryNew', component: () => import('@/views/DiaryEdit.vue') },
  { path: '/diary/:id', name: 'DiaryEdit', component: () => import('@/views/DiaryEdit.vue') },
  { path: '/chat', name: 'Chat', component: () => import('@/views/ChatPage.vue') },
  { path: '/mood', name: 'Mood', component: () => import('@/views/MoodTrend.vue') },
  { path: '/stats', name: 'Stats', component: () => import('@/views/StatsPage.vue') },
  { path: '/garden', name: 'Garden', component: () => import('@/views/GardenPage.vue') },
  { path: '/settings', name: 'Settings', component: () => import('@/views/SettingsPage.vue') },
  { path: '/reminders', name: 'Reminders', component: () => import('@/views/RemindersPage.vue') },
  { path: '/notifications', name: 'Notifications', component: () => import('@/views/NotificationsPage.vue') },
  { path: '/community', name: 'Community', component: () => import('@/views/CommunityPage.vue') },
  { path: '/community/create', name: 'CreatePost', component: () => import('@/views/CreatePostPage.vue') },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 路由守卫
// 开发服务器默认允许免登录浏览，避免本地单机调试被认证流程打断。
// 生产构建或显式设置 VITE_DEV_AUTH_BYPASS=false 时启用登录保护。
router.beforeEach((to) => {
  const devAuthBypass = import.meta.env.DEV && import.meta.env.VITE_DEV_AUTH_BYPASS !== 'false'
  if (devAuthBypass) return true

  const token = localStorage.getItem('token')
  const publicPages = ['Home', 'Login', 'Register']

  if (!token && !publicPages.includes(to.name)) {
    return { name: 'Login' }
  }

  if (token && ['Login', 'Register'].includes(to.name)) {
    return { name: 'Diaries' }
  }

  return true
})

export default router
