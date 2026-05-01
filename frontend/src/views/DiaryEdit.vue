<template>
  <div class="max-w-2xl mx-auto">
    <h1 class="text-3xl md:text-4xl mb-6" style="font-family: 'Kalam', cursive; font-weight: 700;">{{ isEdit ? '编辑日记' : '写日记' }}</h1>
    <form @submit.prevent="handleSave" class="bg-white border-[3px] border-pencil p-6 md:p-8 wobbly-md shadow-hard">
      <div class="mb-4">
        <input v-model="title" type="text" class="w-full px-4 py-3 text-xl border-[3px] border-pencil bg-white wobbly-sm focus:border-pen-blue focus:ring-2 focus:ring-pen-blue/20 outline-none" placeholder="给今天取个标题..." style="font-family: 'Kalam', cursive; font-weight: 700;">
      </div>
      <div class="mb-4">
        <textarea v-model="content" rows="8" class="w-full px-4 py-3 text-lg border-[3px] border-pencil bg-white wobbly-sm focus:border-pen-blue focus:ring-2 focus:ring-pen-blue/20 outline-none resize-y" placeholder="今天发生了什么？"></textarea>
      </div>
      <div v-if="result" class="mb-4 p-4 border-[2px] border-pencil wobbly-sm bg-muted">
        <p>情绪分数: <strong>{{ result.mood_score }}</strong></p>
        <p>情绪标签: <strong>{{ result.mood_label }}</strong></p>
        <p v-if="result.keywords.length">关键词: {{ result.keywords.join(', ') }}</p>
      </div>
      <p v-if="error" class="text-accent text-base mb-4">{{ error }}</p>
      <div class="flex gap-3">
        <button type="submit" class="px-6 py-3 text-lg border-[3px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[2px] hover:translate-y-[2px] active:shadow-none active:translate-x-[4px] active:translate-y-[4px] transition-all wobbly">{{ isEdit ? '保存' : '发布' }}</button>
        <router-link to="/diaries" class="px-6 py-3 text-lg border-[3px] border-pencil bg-muted shadow-hard hover:shadow-hard-hover hover:translate-x-[2px] hover:translate-y-[2px] active:shadow-none active:translate-x-[4px] active:translate-y-[4px] transition-all wobbly no-underline text-pencil">取消</router-link>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createDiary, updateDiary, getDiary } from '@/api'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const title = ref('')
const content = ref('')
const result = ref(null)
const error = ref('')

onMounted(async () => {
  if (isEdit.value) {
    try {
      const res = await getDiary(route.params.id)
      const diary = res.data
      title.value = diary.title
      content.value = diary.content
      result.value = { mood_score: diary.mood_score, mood_label: diary.mood_label, keywords: [] }
    } catch (err) {
      error.value = '加载日记失败'
    }
  }
})

async function handleSave() {
  error.value = ''
  if (!content.value) {
    error.value = '内容不能为空'
    return
  }
  try {
    if (isEdit.value) {
      await updateDiary(route.params.id, { title: title.value, content: content.value })
    } else {
      await createDiary(title.value, content.value)
    }
    router.push('/diaries')
  } catch (err) {
    error.value = err.message || '保存失败'
  }
}
</script>
