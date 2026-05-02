<template>
  <!-- 情绪趋势条 -->
  <div v-if="type === 'trend'" class="flex items-center gap-4 p-3 border-b-[2px] border-muted last:border-0">
    <div :class="['w-3 h-3 rounded-full', moodColor(data.label)]"></div>
    <div class="flex-1">
      <div class="h-4 bg-muted wobbly-sm relative overflow-hidden">
        <div
          :class="['h-full wobbly-sm', moodColor(data.label)]"
          :style="{ width: data.score + '%' }"
        ></div>
      </div>
    </div>
    <span class="text-sm w-8 text-right">{{ data.score }}</span>
    <span class="text-sm text-pencil/50 w-12">{{ data.label }}</span>
    <span class="text-xs text-pencil/40 hidden md:block">{{ formatDate(data.timestamp) }}</span>
  </div>

  <!-- 情绪分布条 -->
  <div v-else-if="type === 'distribution'" class="flex items-center gap-3">
    <span class="w-10 text-sm">{{ label }}</span>
    <div class="flex-1 h-5 bg-muted wobbly-sm relative overflow-hidden">
      <div
        :class="['h-full wobbly-sm', moodColor(label)]"
        :style="{ width: barWidth + '%' }"
      ></div>
    </div>
    <span class="text-sm w-8 text-right">{{ count }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: {
    type: String,
    required: true,
    validator: (val) => ['trend', 'distribution'].includes(val)
  },
  data: {
    type: [Object, Array],
    default: null
  },
  label: {
    type: String,
    default: ''
  },
  count: {
    type: Number,
    default: 0
  },
  maxValue: {
    type: Number,
    default: 1
  }
})

const barWidth = computed(() => {
  if (props.type !== 'distribution') return 0
  return (props.count / props.maxValue) * 100
})

function moodColor(label) {
  const map = {
    '开心': 'bg-yellow-400',
    '平静': 'bg-green-400',
    '中性': 'bg-blue-400',
    '焦虑': 'bg-orange-400',
    '悲伤': 'bg-purple-400'
  }
  return map[label] || 'bg-gray-400'
}

function formatDate(ts) {
  return ts ? ts.slice(0, 10) : ''
}
</script>
