<template>
  <div class="max-w-4xl mx-auto p-6">
    <!-- 页面标题和发布按钮 -->
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-5xl font-handwritten font-bold text-pencil" style="font-family: 'Kalam', cursive; font-weight: 700;">
        社区花园
      </h1>
      <router-link
        to="/community/create"
        class="px-6 py-3 text-lg border-[3px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[2px] hover:translate-y-[2px] active:shadow-none transition-all wobbly-sm no-underline text-pencil font-handwritten"
        style="font-family: 'Patrick Hand', cursive;"
      >
        + 发布帖子
      </router-link>
    </div>

    <!-- 情绪筛选 -->
    <div class="flex gap-2 mb-6 flex-wrap">
      <button
        @click="currentFilter = ''"
        class="px-4 py-2 border-[2px] border-pencil transition-all wobbly-sm font-handwritten"
        :class="currentFilter === '' ? 'bg-pencil text-white' : 'bg-white hover:bg-sticky'"
        style="font-family: 'Patrick Hand', cursive;"
      >
        全部
      </button>
      <button
        v-for="mood in moodFilters"
        :key="mood.label"
        @click="currentFilter = mood.label"
        class="px-4 py-2 border-[2px] border-pencil transition-all wobbly-sm font-handwritten"
        :class="currentFilter === mood.label ? 'bg-pencil text-white' : 'bg-white hover:bg-sticky'"
        style="font-family: 'Patrick Hand', cursive;"
      >
        {{ mood.emoji }} {{ mood.label }}
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-12 text-pencil/60 font-handwritten" style="font-family: 'Patrick Hand', cursive; font-size: 1.25rem;">
      加载中...
    </div>

    <!-- 空状态 -->
    <div v-else-if="posts.length === 0" class="text-center py-16">
      <div class="text-6xl mb-4">🌱</div>
      <p class="text-xl text-pencil/60 font-handwritten" style="font-family: 'Patrick Hand', cursive;">
        还没有帖子，来发布第一篇吧！
      </p>
    </div>

    <!-- 帖子列表 -->
    <div v-else class="space-y-6">
      <PostCard
        v-for="post in posts"
        :key="post.id"
        :post="post"
      />

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="flex justify-center gap-2 mt-8">
        <button
          @click="changePage(currentPage - 1)"
          :disabled="currentPage <= 1"
          class="px-4 py-2 border-[2px] border-pencil bg-white shadow-hard hover:shadow-hard-hover disabled:opacity-50 disabled:cursor-not-allowed transition-all wobbly-sm font-handwritten"
          style="font-family: 'Patrick Hand', cursive;"
        >
          上一页
        </button>
        <span class="px-4 py-2 font-handwritten text-pencil/70" style="font-family: 'Patrick Hand', cursive;">
          {{ currentPage }} / {{ totalPages }}
        </span>
        <button
          @click="changePage(currentPage + 1)"
          :disabled="currentPage >= totalPages"
          class="px-4 py-2 border-[2px] border-pencil bg-white shadow-hard hover:shadow-hard-hover disabled:opacity-50 disabled:cursor-not-allowed transition-all wobbly-sm font-handwritten"
          style="font-family: 'Patrick Hand', cursive;"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import PostCard from '@/components/PostCard.vue'
import { getCommunityPosts } from '@/api'

const posts = ref([])
const loading = ref(true)
const currentPage = ref(1)
const totalPages = ref(1)
const currentFilter = ref('')

const moodFilters = [
  { label: '开心', emoji: '😊' },
  { label: '平静', emoji: '😌' },
  { label: '中性', emoji: '😐' },
  { label: '焦虑', emoji: '😟' },
  { label: '悲伤', emoji: '😢' }
]

async function loadPosts() {
  loading.value = true
  try {
    const res = await getCommunityPosts({
      page: currentPage.value,
      mood_filter: currentFilter.value || undefined
    })
    if (res.data.success) {
      posts.value = res.data.data.posts
      totalPages.value = res.data.data.total_pages
    }
  } catch (error) {
    console.error('加载帖子失败:', error)
  } finally {
    loading.value = false
  }
}

function changePage(page) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

watch(currentFilter, () => {
  currentPage.value = 1
  loadPosts()
})

onMounted(() => {
  loadPosts()
})
</script>
