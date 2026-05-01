<template>
  <div class="min-h-screen bg-paper" style="font-family: 'Patrick Hand', cursive;">
    <header class="border-b-[3px] border-pencil bg-white shadow-hard-sm sticky top-0 z-50">
      <div class="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2 no-underline">
          <span class="text-2xl" style="font-family: 'Kalam', cursive; font-weight: 700;">心语花园</span>
        </router-link>
        <nav class="flex items-center gap-1 md:gap-3">
          <router-link to="/diaries" class="px-3 py-1.5 text-base md:text-lg hover:bg-muted wobbly-sm transition-colors no-underline text-pencil">日记</router-link>
          <router-link to="/chat" class="px-3 py-1.5 text-base md:text-lg hover:bg-muted wobbly-sm transition-colors no-underline text-pencil">陪伴</router-link>
          <router-link to="/mood" class="px-3 py-1.5 text-base md:text-lg hover:bg-muted wobbly-sm transition-colors no-underline text-pencil">情绪</router-link>
          <router-link to="/garden" class="px-3 py-1.5 text-base md:text-lg hover:bg-muted wobbly-sm transition-colors no-underline text-pencil">花园</router-link>
          <router-link to="/settings" class="px-3 py-1.5 text-base md:text-lg hover:bg-muted wobbly-sm transition-colors no-underline text-pencil">设置</router-link>
          <router-link to="/stats" class="px-3 py-1.5 text-base md:text-lg hover:bg-muted wobbly-sm transition-colors no-underline text-pencil">统计</router-link>
          <!-- 开发模式：隐藏退出按钮，恢复认证时取消注释 -->
          <!--
          <button @click="handleLogout" class="ml-2 px-4 py-1.5 text-base border-[3px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[2px] hover:translate-y-[2px] active:shadow-none active:translate-x-[4px] active:translate-y-[4px] transition-all wobbly no-underline text-pencil">退出</button>
          -->
        </nav>
      </div>
    </header>
    <main class="max-w-5xl mx-auto px-4 py-6 md:py-10">
      <router-view />
    </main>
  </div>
</template>

<script setup>
// 开发模式：auth 相关代码保留，恢复认证时使用
// import { useAuthStore } from '@/stores/auth'
// import { useRouter } from 'vue-router'
//
// const auth = useAuthStore()
// const router = useRouter()
//
// function handleLogout() {
//   auth.logout()
//   router.push('/login')
// }
</script>
