<template>
  <div :class="[
    'border-[3px] border-pencil p-5 wobbly-md shadow-hard-sm card-hover relative',
    variant === 'garden' ? 'bg-white/80' : 'bg-white'
  ]">
    <!-- garden 变体：显示 emoji -->
    <div v-if="variant === 'garden'" class="tack"></div>
    <div v-if="variant === 'garden'" class="text-2xl mb-2">{{ moodEmoji(diary.mood_score) }}</div>

    <div class="flex items-start justify-between">
      <div class="flex-1">
        <h2 class="text-xl" style="font-family: 'Kalam', cursive; font-weight: 700;">
          {{ diary.title }}
        </h2>
        <p class="text-base text-pencil/70 mt-1">
          {{ diary.content.slice(0, variant === 'garden' ? 80 : 120) }}{{ diary.content.length > (variant === 'garden' ? 80 : 120) ? '...' : '' }}
        </p>
        <div class="flex items-center gap-3 mt-3">
          <span v-if="variant !== 'garden'" class="px-3 py-0.5 text-sm border-[2px] border-pencil wobbly-sm">
            {{ diary.mood_label }}
          </span>
          <span class="text-sm text-pencil/50">{{ diary.created_at }}</span>
        </div>
      </div>
      <div v-if="showActions" class="flex gap-2 ml-4">
        <router-link
          :to="`/diary/${diary.id}`"
          class="px-3 py-1 text-sm border-[2px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[1px] hover:translate-y-[1px] active:shadow-none transition-all wobbly-sm no-underline text-pencil"
        >
          编辑
        </router-link>
        <button
          @click="$emit('delete', diary.id)"
          class="px-3 py-1 text-sm border-[2px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[1px] hover:translate-y-[1px] active:shadow-none transition-all wobbly-sm"
        >
          删除
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

defineProps({
  diary: {
    type: Object,
    required: true,
    validator: (val) => val.id && val.title !== undefined
  },
  showActions: {
    type: Boolean,
    default: false
  },
  variant: {
    type: String,
    default: 'list',
    validator: (val) => ['list', 'garden'].includes(val)
  }
})

defineEmits(['delete'])

function moodEmoji(score) {
  if (score >= 75) return '😊'
  if (score >= 60) return '😌'
  if (score >= 40) return '😐'
  if (score >= 25) return '😟'
  return '😢'
}
</script>
