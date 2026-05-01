<template>
  <div>
    <h1 class="text-3xl md:text-4xl mb-6" style="font-family: 'Kalam', cursive; font-weight: 700;">情绪趋势</h1>

    <div class="bg-white border-[3px] border-pencil p-6 wobbly-md shadow-hard-sm mb-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl" style="font-family: 'Kalam', cursive; font-weight: 700;">近 {{ days }} 天情绪曲线</h2>
        <select v-model="days" @change="fetchData" class="px-3 py-1.5 text-base border-[2px] border-pencil bg-white wobbly-sm">
          <option :value="7">7天</option>
          <option :value="30">30天</option>
          <option :value="90">90天</option>
        </select>
      </div>
      <div v-if="loading" class="text-center py-10">
        <div class="text-4xl animate-gentle-bounce">📊</div>
      </div>
      <div v-else-if="records.length === 0" class="text-center py-10 text-pencil/50 text-lg">
        还没有情绪记录
      </div>
      <div v-else class="space-y-3">
        <div v-for="r in records" :key="r.timestamp" class="flex items-center gap-4 p-3 border-b-[2px] border-muted last:border-0">
          <div :class="['w-3 h-3 rounded-full', moodColor(r.label)]"></div>
          <div class="flex-1">
            <div class="h-4 bg-muted wobbly-sm relative overflow-hidden">
              <div :class="['h-full wobbly-sm', moodColor(r.label)]" :style="{ width: r.score + '%' }"></div>
            </div>
          </div>
          <span class="text-sm w-8 text-right">{{ r.score }}</span>
          <span class="text-sm text-pencil/50 w-12">{{ r.label }}</span>
          <span class="text-xs text-pencil/40 hidden md:block">{{ formatDate(r.timestamp) }}</span>
        </div>
      </div>
    </div>

    <div class="bg-white border-[3px] border-pencil p-6 wobbly-md shadow-hard-sm">
      <h2 class="text-xl mb-4" style="font-family: 'Kalam', cursive; font-weight: 700;">情绪分布</h2>
      <div v-if="loadingDist" class="text-center py-6">
        <div class="text-3xl animate-gentle-bounce">📊</div>
      </div>
      <div v-else class="space-y-3">
        <div v-for="(count, label) in distribution" :key="label" class="flex items-center gap-3">
          <span class="w-10 text-sm">{{ label }}</span>
          <div class="flex-1 h-5 bg-muted wobbly-sm relative overflow-hidden">
            <div :class="['h-full wobbly-sm', moodColor(label)]" :style="{ width: barWidth(count) + '%' }"></div>
          </div>
          <span class="text-sm w-8 text-right">{{ count }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getMoodTrend, getMoodDistribution } from '@/api'

const days = ref(7)
const records = ref([])
const distribution = ref({})
const loading = ref(true)
const loadingDist = ref(true)

function moodColor(label) {
  const map = { '开心': 'bg-yellow-400', '平静': 'bg-green-400', '中性': 'bg-blue-400', '焦虑': 'bg-orange-400', '悲伤': 'bg-purple-400' }
  return map[label] || 'bg-gray-400'
}

function formatDate(ts) {
  return ts ? ts.slice(0, 10) : ''
}

function barWidth(count) {
  const max = Math.max(...Object.values(distribution.value), 1)
  return (count / max) * 100
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getMoodTrend(days.value)
    records.value = res.data
  } catch { records.value = [] }
  finally { loading.value = false }

  loadingDist.value = true
  try {
    const res = await getMoodDistribution(days.value)
    distribution.value = res.data
  } catch { distribution.value = {} }
  finally { loadingDist.value = false }
}

onMounted(fetchData)
</script>
