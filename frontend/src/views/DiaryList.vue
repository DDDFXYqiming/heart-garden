<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-3xl md:text-4xl" style="font-family: 'Kalam', cursive; font-weight: 700;">我的日记</h1>
      <router-link to="/diary/new" class="px-5 py-2 text-lg border-[3px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[2px] hover:translate-y-[2px] active:shadow-none active:translate-x-[4px] active:translate-y-[4px] transition-all wobbly no-underline text-pencil">写日记</router-link>
    </div>

    <!-- 搜索 & 筛选工具栏 -->
    <div class="flex flex-col sm:flex-row gap-3 mb-6">
      <input
        v-model="query"
        type="text"
        placeholder="搜索日记..."
        class="flex-1 px-4 py-2 border-2 border-pencil/30 rounded-lg focus:border-pencil outline-none transition-colors"
        @keyup.enter="fetchDiaries()"
      />
      <select
        v-model="selectedMood"
        class="px-4 py-2 border-2 border-pencil/30 rounded-lg focus:border-pencil outline-none transition-colors bg-white"
        @change="fetchDiaries()"
      >
        <option value="">全部情绪</option>
        <option value="开心">😊 开心</option>
        <option value="平静">😌 平静</option>
        <option value="中性">😐 中性</option>
        <option value="焦虑">😰 焦虑</option>
        <option value="悲伤">😢 悲伤</option>
      </select>
      <button
        @click="fetchDiaries()"
        class="px-4 py-2 bg-pencil text-white rounded-lg hover:opacity-90 transition-opacity"
      >
        搜索
      </button>
    </div>

    <div v-if="loading" class="text-center py-10">
      <div class="text-4xl animate-gentle-bounce">📖</div>
      <p class="text-lg mt-2">翻开日记本...</p>
    </div>

    <div v-else-if="diaries.length === 0 && query === '' && selectedMood === ''" class="text-center py-10">
      <div class="text-5xl mb-3">📝</div>
      <p class="text-xl">还没有日记，开始你的第一篇吧！</p>
    </div>

    <div v-else-if="diaries.length === 0" class="text-center py-10">
      <div class="text-5xl mb-3">🔍</div>
      <p class="text-xl">没有找到匹配的日记</p>
    </div>

    <div v-else class="space-y-4">
      <DiaryCard v-for="d in diaries" :key="d.id" :diary="d" :showActions="true" @delete="handleDelete" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDiaries, deleteDiary } from '@/api'
import DiaryCard from '@/components/DiaryCard.vue'

const diaries = ref([])
const loading = ref(true)
const query = ref('')
const selectedMood = ref('')
const total = ref(0)

onMounted(async () => {
  await fetchDiaries()
})

async function fetchDiaries() {
  loading.value = true
  try {
    const filters = {}
    if (query.value.trim()) {
      filters.q = query.value.trim()
    }
    if (selectedMood.value) {
      filters.mood = selectedMood.value
    }
    const res = await getDiaries(1, 10, filters)
    diaries.value = res.data.items
    total.value = res.data.total
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

async function handleDelete(id) {
  if (!confirm('确定删除这篇日记吗？')) return
  try {
    await deleteDiary(id)
    diaries.value = diaries.value.filter(d => d.id !== id)
  } catch (err) {
    alert(err.message || '删除失败')
  }
}
</script>
