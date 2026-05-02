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
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// ========================================
// 路由守卫 - 开发阶段已禁用
// 启用时取消下方注释，并注释掉 router.afterEach
// ========================================
// router.beforeEach((to, from, next) => {
//   const token = localStorage.getItem('token')
//   const publicPages = ['Home', 'Login', 'Register']
//   if (!token && !publicPages.includes(to.name)) {
//     next({ name: 'Login' })
//   } else {
//     next()
//   }
// })

export default router
