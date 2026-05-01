import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getMe } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const token = ref(localStorage.getItem('token' || ''))

  const isLoggedIn = computed(() => !!token.value)

  function setAuth(userData, authToken) {
    user.value = userData
    token.value = authToken
    localStorage.setItem('user', JSON.stringify(userData))
    localStorage.setItem('token', authToken)
  }

  function logout() {
    user.value = null
    token.value = ''
    localStorage.removeItem('user')
    localStorage.removeItem('token')
  }

  async function fetchUser() {
    try {
      const res = await getMe()
      user.value = res.data
      localStorage.setItem('user', JSON.stringify(res.data))
    } catch {
      logout()
    }
  }

  return { user, token, isLoggedIn, setAuth, logout, fetchUser }
})
