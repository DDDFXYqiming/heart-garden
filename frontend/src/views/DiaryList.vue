<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-3xl md:text-4xl" style="font-family: 'Kalam', cursive; font-weight: 700;">我的日记</h1>
      <router-link to="/diary/new" class="px-5 py-2 text-lg border-[3px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[2px] hover:translate-y-[2px] active:shadow-none active:translate-x-[4px] active:translate-y-[4px] transition-all wobbly no-underline text-pencil">写日记</router-link>
    </div>

    <div v-if="loading" class="text-center py-10">
      <div class="text-4xl animate-gentle-bounce">📖</div>
      <p class="text-lg mt-2">翻开日记本...</p>
    </div>

    <div v-else-if="diaries.length === 0" class="text-center py-10">
      <div class="text-5xl mb-3">📝</div>
      <p class="text-xl">还没有日记，开始你的第一篇吧！</p>
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

onMounted(async () => {
  try {
    const res = await getDiaries()
    diaries.value = res.data.items
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
})

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
