<template>
  <div class="max-w-md mx-auto py-10 md:py-16">
    <h1 class="text-4xl md:text-5xl text-center mb-8" style="font-family: 'Kalam', cursive; font-weight: 700;">加入花园</h1>
    <form @submit.prevent="handleRegister" class="bg-white border-[3px] border-pencil p-8 wobbly-md shadow-hard">
      <div class="mb-4">
        <label class="block text-lg mb-1">用户名</label>
        <input v-model="username" type="text" class="w-full px-4 py-3 text-lg border-[3px] border-pencil bg-white wobbly-sm focus:border-pen-blue focus:ring-2 focus:ring-pen-blue/20 outline-none" placeholder="给自己取个名字">
      </div>
      <div class="mb-4">
        <label class="block text-lg mb-1">邮箱</label>
        <input v-model="email" type="email" class="w-full px-4 py-3 text-lg border-[3px] border-pencil bg-white wobbly-sm focus:border-pen-blue focus:ring-2 focus:ring-pen-blue/20 outline-none" placeholder="your@email.com">
      </div>
      <div class="mb-6">
        <label class="block text-lg mb-1">密码</label>
        <input v-model="password" type="password" class="w-full px-4 py-3 text-lg border-[3px] border-pencil bg-white wobbly-sm focus:border-pen-blue focus:ring-2 focus:ring-pen-blue/20 outline-none" placeholder="至少 6 位">
      </div>
      <p v-if="error" class="text-accent text-base mb-4">{{ error }}</p>
      <button type="submit" class="w-full py-3 text-xl border-[3px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[2px] hover:translate-y-[2px] active:shadow-none active:translate-x-[4px] active:translate-y-[4px] transition-all wobbly">注册</button>
      <p class="text-center mt-4 text-base">
        已有账号？<router-link to="/login" class="text-pen-blue underline">登录</router-link>
      </p>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { register } from '@/api'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const email = ref('')
const password = ref('')
const error = ref('')

async function handleRegister() {
  error.value = ''
  if (!username.value || !email.value || !password.value) {
    error.value = '请填写所有字段'
    return
  }
  if (password.value.length < 6) {
    error.value = '密码至少 6 位'
    return
  }
  try {
    const res = await register(username.value, email.value, password.value)
    auth.setAuth({ user_id: res.data.user_id, username: res.data.username, email: res.data.email }, res.data.token)
    router.push('/diaries')
  } catch (err) {
    error.value = err.message || '注册失败'
  }
}
</script>
