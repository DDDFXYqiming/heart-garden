<template>
  <div class="max-w-2xl mx-auto p-6">
    <h1 class="text-5xl font-handwritten font-bold text-pencil mb-8" style="font-family: 'Kalam', cursive; font-weight: 700;">
      发布帖子
    </h1>

    <div class="border-[3px] border-pencil p-6 wobbly-md shadow-hard-sm bg-white/80 relative">
      <!-- 装饰：胶带效果 -->
      <div class="absolute -top-2 left-1/2 -translate-x-1/2 w-16 h-5 bg-gray-300/50 rotate-1"></div>

      <!-- 情绪标签选择 -->
      <div class="mb-6">
        <label class="block text-lg font-handwritten text-pencil mb-3" style="font-family: 'Patrick Hand', cursive;">
          心情标签（可选）
        </label>
        <div class="flex gap-2 flex-wrap">
          <button
            v-for="mood in moods"
            :key="mood.label"
            @click="selectedMood = mood"
            class="px-4 py-2 border-[2px] border-pencil transition-all wobbly-sm font-handwritten"
            :class="selectedMood?.label === mood.label ? 'bg-pencil text-white' : 'bg-white hover:bg-sticky'"
            style="font-family: 'Patrick Hand', cursive;"
          >
            {{ mood.emoji }} {{ mood.label }}
          </button>
          <button
            @click="selectedMood = null"
            class="px-4 py-2 border-[2px] border-pencil transition-all wobbly-sm font-handwritten"
            :class="!selectedMood ? 'bg-pencil text-white' : 'bg-white hover:bg-sticky'"
            style="font-family: 'Patrick Hand', cursive;"
          >
            ✕ 不选择
          </button>
        </div>
      </div>

      <!-- 内容编辑 -->
      <div class="mb-6">
        <label class="block text-lg font-handwritten text-pencil mb-3" style="font-family: 'Patrick Hand', cursive;">
          分享你的心情...
        </label>
        <textarea
          v-model="content"
          rows="8"
          class="w-full p-4 border-[2px] border-pencil wobbly-md font-handwritten text-pencil text-lg resize-none focus:outline-none focus:border-blue-500"
          style="font-family: 'Patrick Hand', cursive; background-color: rgba(255, 255, 255, 0.9);"
          placeholder="写下你想分享的心情、故事或感悟..."
          maxlength="1000"
        ></textarea>
        <div class="text-right text-sm text-pencil/50 mt-1 font-handwritten" style="font-family: 'Patrick Hand', cursive;">
          {{ content.length }} / 1000
        </div>
      </div>

      <!-- 匿名开关 -->
      <div class="flex items-center justify-between mb-8 p-4 border-[2px] border-pencil wobbly-sm bg-sticky/30">
        <div>
          <div class="font-handwritten text-pencil font-bold" style="font-family: 'Patrick Hand', cursive; font-size: 1.125rem;">
            匿名发布
          </div>
          <div class="text-sm text-pencil/60 font-handwritten" style="font-family: 'Patrick Hand', cursive;">
            开启后，其他用户将无法看到你的用户名
          </div>
        </div>
        <button
          @click="isAnonymous = !isAnonymous"
          class="w-16 h-8 border-[2px] border-pencil transition-all wobbly-sm relative"
          :class="isAnonymous ? 'bg-blue-500' : 'bg-gray-300'"
          style="border-radius: 255px 15px 225px 15px / 15px 225px 15px 255px;"
        >
          <div
            class="absolute top-0.5 w-6 h-6 bg-white border-[2px] border-pencil transition-all"
            :class="isAnonymous ? 'left-8' : 'left-0.5'"
            style="border-radius: 255px 15px 225px 15px / 15px 225px 15px 255px;"
          ></div>
        </button>
      </div>

      <!-- 操作按钮 -->
      <div class="flex gap-4 justify-end">
        <router-link
          to="/community"
          class="px-6 py-3 text-lg border-[3px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[2px] hover:translate-y-[2px] active:shadow-none transition-all wobbly-sm no-underline text-pencil font-handwritten"
          style="font-family: 'Patrick Hand', cursive;"
        >
          取消
        </router-link>
        <button
          @click="publishPost"
          :disabled="!content.trim() || publishing"
          class="px-8 py-3 text-lg border-[3px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[2px] hover:translate-y-[2px] active:shadow-none transition-all wobbly-sm font-handwritten disabled:opacity-50 disabled:cursor-not-allowed"
          :class="content.trim() ? 'hover:bg-red-500 hover:text-white' : ''"
          style="font-family: 'Patrick Hand', cursive;"
        >
          {{ publishing ? '发布中...' : '发布帖子' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { createCommunityPost } from '@/api'

const router = useRouter()
const content = ref('')
const selectedMood = ref(null)
const isAnonymous = ref(true)
const publishing = ref(false)

const moods = [
  { label: '开心', emoji: '😊', score: 80 },
  { label: '平静', emoji: '😌', score: 65 },
  { label: '中性', emoji: '😐', score: 50 },
  { label: '焦虑', emoji: '😟', score: 30 },
  { label: '悲伤', emoji: '😢', score: 15 }
]

async function publishPost() {
  if (!content.value.trim() || publishing.value) return

  publishing.value = true
  try {
    const res = await createCommunityPost({
      content: content.value.trim(),
      mood_label: selectedMood.value?.label,
      mood_score: selectedMood.value?.score,
      is_anonymous: isAnonymous.value
    })

    if (res.success) {
      router.push('/community')
    }
  } catch (error) {
    console.error('发布失败:', error)
    alert('发布失败，请重试')
  } finally {
    publishing.value = false
  }
}
</script>
