<template>
  <div class="max-w-md mx-auto py-10 md:py-16">
    <h1 class="text-4xl md:text-5xl text-center mb-8" style="font-family: 'Kalam', cursive; font-weight: 700;">欢迎回来</h1>
    <form @submit.prevent="handleLogin" class="bg-white border-[3px] border-pencil p-8 wobbly-md shadow-hard">
      <div class="mb-5">
        <label class="block text-lg mb-1">用户名或邮箱</label>
        <input v-model="username" type="text" class="w-full px-4 py-3 text-lg border-[3px] border-pencil bg-white wobbly-sm focus:border-pen-blue focus:ring-2 focus:ring-pen-blue/20 outline-none" placeholder="输入用户名或邮箱">
      </div>
      <div class="mb-6">
        <label class="block text-lg mb-1">密码</label>
        <input v-model="password" type="password" class="w-full px-4 py-3 text-lg border-[3px] border-pencil bg-white wobbly-sm focus:border-pen-blue focus:ring-2 focus:ring-pen-blue/20 outline-none" placeholder="输入密码">
      </div>
      <p v-if="error" class="text-accent text-base mb-4">{{ error }}</p>
      <button type="submit" class="w-full py-3 text-xl border-[3px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[2px] hover:translate-y-[2px] active:shadow-none active:translate-x-[4px] active:translate-y-[4px] transition-all wobbly">登录</button>
      <p class="text-center mt-4 text-base">
        还没有账号？<router-link to="/register" class="text-pen-blue underline">注册</router-link>
      </p>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { login as loginApi } from '@/api'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const password = ref('')
const error = ref('')

async function handleLogin() {
  error.value = ''
  if (!username.value || !password.value) {
    error.value = '请填写所有字段'
    return
  }
  try {
    const res = await loginApi(username.value, '', password.value)
    auth.setAuth({ user_id: res.data.user_id, username: res.data.username, email: res.data.email }, res.data.token)
    router.push('/diaries')
  } catch (err) {
    error.value = err.message || '登录失败'
  }
}
</script>
