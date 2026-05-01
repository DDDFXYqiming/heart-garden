<template>
  <div class="max-w-2xl mx-auto">
    <h1 class="text-3xl md:text-4xl mb-6" style="font-family: 'Kalam', cursive; font-weight: 700;">设置</h1>

    <div class="bg-white border-[3px] border-pencil p-6 wobbly-md shadow-hard-sm mb-6">
      <h2 class="text-xl mb-4" style="font-family: 'Kalam', cursive; font-weight: 700;">账号信息</h2>
      <div class="space-y-2">
        <p class="text-lg">用户名: <strong>{{ user?.username }}</strong></p>
        <p class="text-lg">邮箱: <strong>{{ user?.email }}</strong></p>
        <p class="text-lg">日记数: <strong>{{ user?.diary_count || 0 }}</strong></p>
      </div>
    </div>

    <div class="bg-white border-[3px] border-pencil p-6 wobbly-md shadow-hard-sm">
      <h2 class="text-xl mb-4" style="font-family: 'Kalam', cursive; font-weight: 700;">自定义情绪词库</h2>

      <form @submit.prevent="handleAdd" class="flex gap-3 mb-4">
        <input v-model="newWord.word" class="flex-1 px-3 py-2 text-base border-[2px] border-pencil bg-white wobbly-sm focus:border-pen-blue focus:ring-2 outline-none" placeholder="新词语">
        <select v-model="newWord.word_type" class="px-3 py-2 text-base border-[2px] border-pencil bg-white wobbly-sm">
          <option value="positive">正向</option>
          <option value="negative">负向</option>
        </select>
        <button type="submit" class="px-4 py-2 text-base border-[2px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[1px] hover:translate-y-[1px] active:shadow-none transition-all wobbly-sm">添加</button>
      </form>

      <div v-if="words.length === 0" class="text-center py-6 text-pencil/50">
        <p class="text-lg">还没有自定义词语</p>
      </div>

      <div v-else class="space-y-2">
        <div v-for="w in words" :key="w.id" class="flex items-center justify-between p-3 border-[2px] border-pencil wobbly-sm">
          <div class="flex items-center gap-3">
            <span class="text-lg">{{ w.word }}</span>
            <span :class="['px-2 py-0.5 text-xs border-[2px] border-pencil wobbly-sm', w.word_type === 'positive' ? 'bg-green-200' : 'bg-red-200']">{{ w.word_type === 'positive' ? '正向' : '负向' }}</span>
            <span class="text-xs text-pencil/40">{{ w.category }}</span>
          </div>
          <button @click="handleDelete(w.id)" class="px-2 py-1 text-sm border-[2px] border-pencil bg-white wobbly-sm">删除</button>
        </div>
      </div>
      <p v-if="error" class="text-accent text-sm mt-3">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getCustomWords, addCustomWord, deleteCustomWord } from '@/api'

const auth = useAuthStore()
const user = auth.user
const words = ref([])
const error = ref('')
const newWord = reactive({ word: '', word_type: 'positive' })

async function fetchWords() {
  try {
    const res = await getCustomWords()
    words.value = res.data
  } catch { words.value = [] }
}

async function handleAdd() {
  error.value = ''
  if (!newWord.word.trim()) {
    error.value = '词语不能为空'
    return
  }
  try {
    await addCustomWord(newWord.word.trim(), '自定义', newWord.word_type)
    newWord.word = ''
    await fetchWords()
  } catch (err) {
    error.value = err.message || '添加失败'
  }
}

async function handleDelete(id) {
  try {
    await deleteCustomWord(id)
    words.value = words.value.filter(w => w.id !== id)
  } catch (err) {
    alert(err.message || '删除失败')
  }
}

onMounted(fetchWords)
</script>
