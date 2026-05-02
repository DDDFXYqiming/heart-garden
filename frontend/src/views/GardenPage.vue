<template>
  <div>
    <h1 class="text-3xl md:text-4xl mb-6" style="font-family: 'Kalam', cursive; font-weight: 700;">记忆花园</h1>

    <div v-if="loading" class="text-center py-10">
      <div class="text-5xl animate-gentle-bounce">🌸</div>
      <p class="text-lg mt-2">花园正在生长...</p>
    </div>

    <div v-else-if="garden.length === 0" class="text-center py-10">
      <div class="text-5xl mb-3">🌱</div>
      <p class="text-xl">你的花园还是空地，种下第一篇日记吧</p>
    </div>

    <div v-else class="grid md:grid-cols-2 gap-5">
      <DiaryCard v-for="d in garden" :key="d.id" :diary="d" variant="garden" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getGarden } from '@/api'
import DiaryCard from '@/components/DiaryCard.vue'

const loading = ref(true)
const garden = ref([])

function moodEmoji(score) {
  if (score >= 75) return '😊'
  if (score >= 60) return '😌'
  if (score >= 40) return '😐'
  if (score >= 25) return '😟'
  return '😢'
}

onMounted(async () => {
  try {
    const res = await getGarden()
    garden.value = res.data
  } catch { /* empty */ }
  finally { loading.value = false }
})
</script>
