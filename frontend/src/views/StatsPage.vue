<template>
  <div>
    <h1 class="text-3xl md:text-4xl mb-6" style="font-family: 'Kalam', cursive; font-weight: 700;">统计概览</h1>

    <div v-if="loading" class="text-center py-10">
      <div class="text-5xl animate-gentle-bounce">📊</div>
    </div>

    <div v-else class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <StatCard icon="📝" :value="stats.total_diaries" label="日记" />
      <StatCard icon="💬" :value="stats.total_conversations" label="对话" />
      <StatCard icon="📈" :value="stats.avg_mood_score" label="平均情绪分" />
      <StatCard icon="🏆" :value="stats.most_common_mood" label="最常情绪" />
    </div>

    <div class="bg-white border-[3px] border-pencil p-6 wobbly-md shadow-hard-sm">
      <h2 class="text-xl mb-4" style="font-family: 'Kalam', cursive; font-weight: 700;">近 7 天</h2>
      <div class="flex items-center gap-4">
        <div>
          <div class="text-sm text-pencil/60">平均情绪分</div>
          <div class="text-3xl font-bold" style="font-family: 'Kalam', cursive;">{{ stats.last_7_days.avg_score }}</div>
        </div>
        <div class="border-l-[3px] border-pencil pl-4">
          <div class="text-sm text-pencil/60">趋势</div>
          <div :class="['text-2xl font-bold', trendColor]">{{ stats.last_7_days.trend }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getStats } from '@/api'
import StatCard from '@/components/StatCard.vue'

const loading = ref(true)
const stats = ref({
  total_diaries: 0,
  total_conversations: 0,
  avg_mood_score: 0,
  most_common_mood: '-',
  last_7_days: { avg_score: 0, trend: '平稳' }
})

const trendColor = computed(() => {
  const map = { '上升': 'text-green-500', '下降': 'text-accent', '平稳': 'text-pencil' }
  return map[stats.value.last_7_days.trend] || ''
})

onMounted(async () => {
  try {
    const res = await getStats()
    stats.value = res.data
  } catch { /* keep defaults */ }
  finally { loading.value = false }
})
</script>
