<template>
  <div class="border-[3px] border-pencil p-5 wobbly-md shadow-hard-sm card-hover relative bg-white/80">
    <!-- 装饰：胶带效果 -->
    <div class="absolute -top-2 left-1/2 -translate-x-1/2 w-12 h-4 bg-gray-300/50 rotate-2"></div>
    
    <div class="flex items-start justify-between">
      <div class="flex-1">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-sm text-pencil/60">{{ post.display_name || '匿名用户' }}</span>
          <span v-if="post.mood_label" class="px-3 py-0.5 text-sm border-[2px] border-pencil wobbly-sm">
            {{ post.mood_label }}
          </span>
        </div>
        
        <p class="text-base text-pencil/80 mt-1 line-clamp-3">
          {{ post.content }}
        </p>
        
        <div class="flex items-center gap-4 mt-3">
          <span class="text-sm text-pencil/50">
            {{ formatTime(post.created_at) }}
          </span>
          <span class="text-sm text-pencil/60 flex items-center gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
            {{ post.likes_count || 0 }}
          </span>
          <span class="text-sm text-pencil/60 flex items-center gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            {{ post.comments_count || 0 }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'

defineProps({
  post: {
    type: Object,
    required: true,
    validator: (val) => val.id && val.content !== undefined
  }
})

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}小时前`
  
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 30) return `${diffDays}天前`
  
  return date.toLocaleDateString('zh-CN')
}
</script>
