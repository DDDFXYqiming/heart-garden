<template>
  <div
    v-if="plant"
    data-testid="detail-panel"
    class="fixed inset-y-0 right-0 w-full max-w-md bg-white/95 backdrop-blur-sm border-l-[3px] border-pencil shadow-hard z-50 overflow-y-auto"
  >
    <!-- Header with close button -->
    <div class="flex items-center justify-between p-5 border-b-[3px] border-pencil/20">
      <h2 class="text-xl font-bold truncate pr-2" style="font-family: 'Kalam', cursive; font-weight: 700;">
        🌸 {{ plant.title }}
      </h2>
      <button
        aria-label="关闭详情"
        @click="$emit('close')"
        class="flex-shrink-0 w-8 h-8 flex items-center justify-center border-[2px] border-pencil bg-white shadow-hard-sm hover:shadow-hard-hover hover:translate-x-[1px] hover:translate-y-[1px] active:shadow-none transition-all wobbly-sm text-lg"
      >
        ✕
      </button>
    </div>

    <!-- Body -->
    <div class="p-5 space-y-4">
      <!-- Source type badge -->
      <div class="flex items-center gap-2">
        <span class="px-3 py-0.5 text-sm border-[2px] border-pencil wobbly-sm bg-white">
          {{ sourceTypeLabel }}
        </span>
        <span class="px-3 py-0.5 text-sm border-[2px] border-pencil wobbly-sm bg-white">
          {{ modelTypeLabel }}
        </span>
      </div>

      <!-- Date -->
      <div class="text-sm text-pencil/60">
        📅 {{ displayDate }}
      </div>

      <!-- Mood score -->
      <div class="flex items-center gap-2">
        <span class="text-sm text-pencil/70">情绪分：</span>
        <span class="text-lg font-bold" style="font-family: 'Kalam', cursive;">{{ displayMoodScore }}</span>
        <span class="px-2 py-0.5 text-sm border-[2px] border-pencil wobbly-sm bg-white">
          {{ plant.mood_label || plant.moodLabel || '' }}
        </span>
      </div>

      <!-- Content preview -->
      <div class="bg-white/60 border-[2px] border-pencil/20 p-4 wobbly-sm">
        <p class="text-base text-pencil leading-relaxed">
          {{ truncatedContent }}
        </p>
      </div>

      <!-- Growth story -->
      <div>
        <h3 class="text-sm font-bold text-pencil/60 mb-1" style="font-family: 'Kalam', cursive;">
          🌱 成长说明
        </h3>
        <p class="text-base text-pencil/80 leading-relaxed bg-amber-50/60 border-[2px] border-amber-200/50 p-4 wobbly-sm">
          {{ displayGrowthStory }}
        </p>
      </div>

      <!-- Action button -->
      <div class="pt-2">
        <button
          aria-label="查看原记录"
          @click="$emit('open-source', plant)"
          class="w-full px-4 py-2 text-base border-[2px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[1px] hover:translate-y-[1px] active:shadow-none transition-all wobbly-sm"
        >
          📖 查看原记录
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  plant: {
    type: Object,
    default: null
  }
})

defineEmits(['close', 'open-source'])

const SOURCE_TYPE_LABELS = {
  diary: '日记之花'
}

const MODEL_TYPE_LABELS = {
  sunflower: '向日葵',
  sprout: '新芽',
  cactus: '仙人掌',
  duskLeaf: '暮叶',
  flower: '花叶',
  leafBloom: '花叶'
}

const sourceTypeLabel = computed(() => {
  if (!props.plant) return ''
  const st = props.plant.sourceType || props.plant.source_type || ''
  return SOURCE_TYPE_LABELS[st] || st
})

const modelTypeLabel = computed(() => {
  if (!props.plant) return ''
  const mt = props.plant.modelType || props.plant.model_type || ''
  return MODEL_TYPE_LABELS[mt] || mt
})

const displayDate = computed(() => {
  if (!props.plant) return ''
  return props.plant.createdAt || props.plant.created_at || ''
})

const displayMoodScore = computed(() => {
  if (!props.plant) return ''
  const score = props.plant.moodScore ?? props.plant.mood_score
  return score != null ? String(score) : ''
})

const displayGrowthStory = computed(() => {
  if (!props.plant) return ''
  return props.plant.growthStory || props.plant.growth_story || ''
})

const truncatedContent = computed(() => {
  if (!props.plant) return ''
  const text = props.plant.contentPreview || props.plant.content || ''
  if (text.length > 120) {
    return text.slice(0, 120) + '...'
  }
  return text
})
</script>
