<template>
  <aside
    v-if="plant"
    data-testid="detail-panel"
    class="fixed inset-y-0 right-0 z-50 w-full max-w-md overflow-y-auto border-l-[3px] border-pencil bg-paper/95 p-4 shadow-hard backdrop-blur-sm"
  >
    <div class="relative min-h-full border-[3px] border-pencil bg-white p-5 shadow-hard-sm wobbly-md">
      <div class="absolute -top-3 left-1/2 h-7 w-24 -translate-x-1/2 rotate-1 bg-muted/75"></div>

      <header class="mb-5 flex items-start justify-between gap-4 border-b-[3px] border-dashed border-pencil/25 pb-4">
        <div class="min-w-0">
          <div class="mb-2 inline-flex border-[2px] border-pencil bg-sticky px-3 py-0.5 text-sm shadow-hard-sm wobbly-sm">
            花园札记
          </div>
          <h2 class="truncate text-2xl font-bold" style="font-family: 'Kalam', cursive; font-weight: 700;">
            {{ plant.title }}
          </h2>
          <p class="mt-1 text-sm text-pencil/55">📅 {{ displayDate }}</p>
        </div>
        <button
          aria-label="关闭详情"
          @click="$emit('close')"
          class="flex h-9 w-9 flex-shrink-0 items-center justify-center border-[2px] border-pencil bg-white text-lg shadow-hard-sm transition-all hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-hard-hover active:shadow-none wobbly-sm"
        >
          ✕
        </button>
      </header>

      <div class="mb-5 grid grid-cols-2 gap-3">
        <div class="border-[2px] border-pencil bg-white p-3 shadow-hard-sm wobbly-sm">
          <div class="text-xs text-pencil/55">来源</div>
          <div class="mt-1 font-bold">{{ sourceTypeLabel }}</div>
        </div>
        <div class="border-[2px] border-pencil bg-white p-3 shadow-hard-sm wobbly-sm">
          <div class="text-xs text-pencil/55">植物</div>
          <div class="mt-1 font-bold">{{ modelTypeLabel }}</div>
        </div>
      </div>

      <div class="mb-5 flex items-center justify-between gap-3 border-[3px] border-pencil bg-sticky p-4 shadow-hard-sm wobbly-md">
        <div>
          <div class="text-xs text-pencil/55">情绪分</div>
          <div class="text-4xl font-bold" style="font-family: 'Kalam', cursive;">{{ displayMoodScore }}</div>
        </div>
        <div class="border-[2px] border-pencil bg-white px-4 py-2 text-xl font-bold shadow-hard-sm wobbly">
          {{ moodStamp }}
        </div>
      </div>

      <section class="mb-5">
        <h3 class="mb-2 text-sm font-bold text-pencil/60" style="font-family: 'Kalam', cursive;">正文摘录</h3>
        <div class="border-[2px] border-pencil/35 bg-paper p-4 shadow-hard-sm wobbly-sm">
          <p class="text-base leading-relaxed text-pencil">
            {{ truncatedContent }}
          </p>
        </div>
      </section>

      <section class="mb-5">
        <h3 class="mb-2 text-sm font-bold text-pencil/60" style="font-family: 'Kalam', cursive;">🌱 成长说明</h3>
        <p class="border-[2px] border-pencil bg-white p-4 text-base leading-relaxed text-pencil/80 shadow-hard-sm wobbly-sm">
          {{ displayGrowthStory }}
        </p>
      </section>

      <button
        aria-label="查看原记录"
        @click="$emit('open-source', plant)"
        class="w-full border-[3px] border-pencil bg-white px-4 py-3 text-base shadow-hard transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:bg-accent hover:text-white hover:shadow-hard-hover active:translate-x-[4px] active:translate-y-[4px] active:shadow-none wobbly"
      >
        📖 查看原记录
      </button>
    </div>
  </aside>
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
  leafBloom: '花团'
}

const MOOD_STAMPS = {
  高能量: '阳光',
  温暖: '绽放',
  平静: '新芽',
  沉思: '静叶',
  坚韧: '守护'
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

const displayMoodLabel = computed(() => {
  if (!props.plant) return ''
  return props.plant.mood_label || props.plant.moodLabel || ''
})

const moodStamp = computed(() => {
  return MOOD_STAMPS[displayMoodLabel.value] || displayMoodLabel.value || '记忆'
})

const displayGrowthStory = computed(() => {
  if (!props.plant) return ''
  return props.plant.growthStory || props.plant.growth_story || ''
})

const truncatedContent = computed(() => {
  if (!props.plant) return ''
  const text = props.plant.contentPreview || props.plant.content || ''
  if (text.length > 140) {
    return text.slice(0, 140) + '...'
  }
  return text
})
</script>
