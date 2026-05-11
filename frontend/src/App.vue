<template>
  <div class="min-h-screen bg-paper" style="font-family: 'Patrick Hand', cursive;">
    <header class="border-b-[3px] border-pencil bg-white shadow-hard-sm sticky top-0 z-50">
      <div class="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2 no-underline">
          <span class="text-2xl" style="font-family: 'Kalam', cursive; font-weight: 700;">心语花园</span>
        </router-link>
        <nav class="flex items-center gap-1 md:gap-3">
          <router-link
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            :aria-current="isNavActive(item) ? 'page' : undefined"
            :class="[
              'nav-link relative px-3 py-1.5 text-base md:text-lg transition-all duration-100 no-underline text-pencil',
              isNavActive(item) ? 'nav-link-active bg-sticky border-[2px] border-pencil shadow-hard-hover -rotate-1' : 'hover:bg-muted hover:-rotate-1'
            ]"
          >
            {{ item.label }}
          </router-link>
          <!-- 开发模式：隐藏退出按钮，恢复认证时取消注释 -->
          <!--
          <button @click="handleLogout" class="ml-2 px-4 py-1.5 text-base border-[3px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[2px] hover:translate-y-[2px] active:shadow-none active:translate-x-[4px] active:translate-y-[4px] transition-all wobbly no-underline text-pencil">退出</button>
          -->
        </nav>
      </div>
    </header>
    <main :class="mainClasses">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const navItems = [
  { label: '日记', to: '/diaries', names: ['Diaries', 'DiaryNew', 'DiaryEdit'] },
  { label: '陪伴', to: '/chat', names: ['Chat'] },
  { label: '情绪', to: '/mood', names: ['Mood'] },
  { label: '花园', to: '/garden', names: ['Garden'] },
  { label: '设置', to: '/settings', names: ['Settings'] },
  { label: '统计', to: '/stats', names: ['Stats'] },
]

function isNavActive(item) {
  return item.names.includes(route.name)
}

const mainClasses = computed(() => [
  'mx-auto px-4 py-6 md:py-10',
  route.name === 'Garden' ? 'max-w-[1500px]' : 'max-w-5xl'
])

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

<style scoped>
.nav-link {
  border-radius: 30px 10px 40px 10px / 10px 30px 10px 40px;
}

.nav-link-active::after {
  content: '';
  position: absolute;
  left: 14%;
  right: 10%;
  bottom: -7px;
  height: 6px;
  border-bottom: 3px solid #ff4d4d;
  border-radius: 70% 45% 60% 50%;
  transform: rotate(-1deg);
}
</style>
