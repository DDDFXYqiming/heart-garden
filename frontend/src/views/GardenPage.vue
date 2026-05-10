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

    <template v-else>
      <!-- Summary card -->
      <div class="bg-white border-[3px] border-pencil p-5 wobbly-md shadow-hard-sm mb-6">
        <h2 class="text-xl mb-3" style="font-family: 'Kalam', cursive; font-weight: 700;">🌿 花园概览</h2>
        <div class="flex flex-wrap gap-4 text-sm">
          <div>
            <span class="text-pencil/60">日记总数</span>
            <div class="text-2xl font-bold" style="font-family: 'Kalam', cursive;">{{ summary.totalCount }}</div>
          </div>
          <div>
            <span class="text-pencil/60">平均情绪分</span>
            <div class="text-2xl font-bold" style="font-family: 'Kalam', cursive;">{{ summary.avgScore }}</div>
          </div>
          <div>
            <span class="text-pencil/60">花园状态</span>
            <div class="text-2xl font-bold" style="font-family: 'Kalam', cursive;">{{ summary.status }}</div>
          </div>
        </div>
      </div>

      <!-- Plant tiles -->
      <div class="grid md:grid-cols-2 gap-5">
        <div
          v-for="d in garden"
          :key="d.id"
          class="border-[3px] border-pencil p-5 wobbly-md shadow-hard-sm card-hover relative bg-white/80"
        >
          <div class="tack"></div>
          <div class="text-3xl mb-2">{{ plantEmoji(d.mood_score) }}</div>
          <h2 class="text-xl" style="font-family: 'Kalam', cursive; font-weight: 700;">
            {{ d.title }}
          </h2>
          <p class="text-base text-pencil/70 mt-1">
            {{ d.content.slice(0, 80) }}{{ d.content.length > 80 ? '...' : '' }}
          </p>
          <div class="flex items-center gap-3 mt-3">
            <span class="text-sm text-pencil/50">{{ d.created_at }}</span>
            <span class="text-sm text-pencil/50">·</span>
            <span class="text-sm text-pencil/50">情绪 {{ d.mood_score }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getGarden } from '@/api'

const loading = ref(true)
const garden = ref([])

const summary = computed(() => {
  const items = garden.value
  const count = items.length
  if (count === 0) {
    return { totalCount: 0, avgScore: '0', status: '🌱 需要浇水' }
  }
  const total = items.reduce((sum, d) => sum + (d.mood_score || 0), 0)
  const avg = total / count
  const avgRounded = Math.round(avg * 10) / 10
  let status
  if (avg >= 70) {
    status = '🌻 繁花盛开'
  } else if (avg >= 40) {
    status = '🌿 稳定生长'
  } else {
    status = '🌱 需要浇水'
  }
  return { totalCount: count, avgScore: avgRounded.toFixed(1), status }
})

function plantEmoji(score) {
  if (score >= 75) return '🌻'
  if (score >= 60) return '🌿'
  if (score >= 40) return '🌱'
  if (score >= 25) return '🍂'
  return '🌵'
}

onMounted(async () => {
  try {
    const res = await getGarden()
    garden.value = res.data
  } catch { /* empty */ }
  finally { loading.value = false }
})
</script>
