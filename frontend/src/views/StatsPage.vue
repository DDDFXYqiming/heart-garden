<template>
  <div>
    <h1 class="text-3xl md:text-4xl mb-6" style="font-family: 'Kalam', cursive; font-weight: 700;">统计概览</h1>

    <div v-if="loading" class="text-center py-10">
      <div class="text-5xl animate-gentle-bounce">📊</div>
    </div>

    <template v-else>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard icon="📝" :value="stats.total_diaries" label="日记" />
        <StatCard icon="💬" :value="stats.total_conversations" label="对话" />
        <StatCard icon="📈" :value="stats.avg_mood_score" label="平均情绪分" />
        <StatCard icon="🏆" :value="stats.most_common_mood" label="最常情绪" />
      </div>

      <div class="bg-white border-[3px] border-pencil p-6 wobbly-md shadow-hard-sm mb-6">
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

      <div class="bg-white border-[3px] border-pencil p-6 wobbly-md shadow-hard-sm">
        <div class="flex items-start gap-3 mb-4">
          <div class="text-4xl">💌</div>
          <div>
            <h2 class="text-xl" style="font-family: 'Kalam', cursive; font-weight: 700;">温柔回顾</h2>
            <p class="text-sm text-pencil/60">基于近 {{ stats.insight.window_days }} 天的记录，给你一点轻轻的提醒。</p>
          </div>
        </div>

        <p class="text-lg leading-relaxed mb-3">{{ stats.insight.summary }}</p>
        <p class="text-base leading-relaxed text-pencil/70 mb-5">{{ stats.insight.suggestion }}</p>

        <div class="grid md:grid-cols-3 gap-3 mb-5">
          <div class="border-[2px] border-pencil p-3 bg-paper wobbly-sm">
            <div class="text-sm text-pencil/60">连续记录</div>
            <div class="text-2xl font-bold" style="font-family: 'Kalam', cursive;">{{ stats.insight.streak_days }} 天</div>
          </div>
          <div class="border-[2px] border-pencil p-3 bg-paper wobbly-sm">
            <div class="text-sm text-pencil/60">活跃天数</div>
            <div class="text-2xl font-bold" style="font-family: 'Kalam', cursive;">{{ stats.insight.active_days }} 天</div>
          </div>
          <div class="border-[2px] border-pencil p-3 bg-paper wobbly-sm">
            <div class="text-sm text-pencil/60">情绪倾向</div>
            <div class="text-base font-bold">{{ moodBalanceText }}</div>
          </div>
        </div>

        <div class="grid md:grid-cols-2 gap-3">
          <div v-if="stats.insight.best_day" class="border-[2px] border-pencil p-3 bg-green-50 wobbly-sm">
            <div class="text-sm text-pencil/60">最明亮的一天</div>
            <div class="font-bold">{{ stats.insight.best_day.date }} · {{ stats.insight.best_day.avg_score }}</div>
          </div>
          <div v-if="stats.insight.lowest_day" class="border-[2px] border-pencil p-3 bg-yellow-50 wobbly-sm">
            <div class="text-sm text-pencil/60">最需要照顾的一天</div>
            <div class="font-bold">{{ stats.insight.lowest_day.date }} · {{ stats.insight.lowest_day.avg_score }}</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getStats } from '@/api'
import StatCard from '@/components/StatCard.vue'

const defaultInsight = {
  summary: '还没有足够的情绪记录，花园正在等待第一颗种子。',
  suggestion: '今天先写下三句话：发生了什么、你的感受、接下来想怎样照顾自己。',
  active_days: 0,
  streak_days: 0,
  best_day: null,
  lowest_day: null,
  mood_balance: { positive: 0, neutral: 0, negative: 0 },
  window_days: 30
}

const loading = ref(true)
const stats = ref({
  total_diaries: 0,
  total_conversations: 0,
  avg_mood_score: 0,
  most_common_mood: '-',
  last_7_days: { avg_score: 0, trend: '平稳' },
  insight: { ...defaultInsight }
})

const trendColor = computed(() => {
  const map = { '上升': 'text-green-500', '下降': 'text-accent', '平稳': 'text-pencil' }
  return map[stats.value.last_7_days.trend] || ''
})

const moodBalanceText = computed(() => {
  const balance = stats.value.insight.mood_balance || defaultInsight.mood_balance
  if (balance.positive >= balance.neutral && balance.positive >= balance.negative && balance.positive > 0) {
    return '更多明亮时刻'
  }
  if (balance.negative > balance.positive && balance.negative > balance.neutral) {
    return '需要多抱抱自己'
  }
  return '整体比较平稳'
})

onMounted(async () => {
  try {
    const res = await getStats()
    stats.value = {
      ...stats.value,
      ...res.data,
      insight: { ...defaultInsight, ...(res.data?.insight || {}) }
    }
  } catch { /* keep defaults */ }
  finally { loading.value = false }
})
</script>
