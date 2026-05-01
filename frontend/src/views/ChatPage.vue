<template>
  <div class="max-w-2xl mx-auto">
    <h1 class="text-3xl md:text-4xl mb-6" style="font-family: 'Kalam', cursive; font-weight: 700;">AI 陪伴</h1>

    <div class="bg-white border-[3px] border-pencil wobbly-md shadow-hard-sm mb-4 h-[400px] md:h-[500px] overflow-y-auto p-4 space-y-3">
      <div v-for="(msg, i) in messages" :key="i" :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']">
        <div :class="['max-w-[80%] px-4 py-2 border-[2px] border-pencil', msg.role === 'user' ? 'bg-sticky' : 'bg-white', 'wobbly-sm']">
          <p class="text-base whitespace-pre-line">{{ msg.content }}</p>
          <div v-if="msg.mood_label" class="flex items-center gap-2 mt-1">
            <span class="text-xs text-pencil/50">{{ msg.mood_label }}</span>
            <span v-if="msg.response_mode" :class="['text-xs px-1.5 py-0.5 border border-pencil/30 rounded', msg.response_mode === 'llm' ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-500']">
              {{ msg.response_mode === 'llm' ? 'AI' : '规则' }}
            </span>
          </div>
        </div>
      </div>
      <div v-if="loading" class="flex justify-start">
        <div class="px-4 py-2 border-[2px] border-pencil bg-white wobbly-sm">
          <div class="flex gap-1">
            <span class="w-2 h-2 bg-pencil rounded-full animate-gentle-bounce"></span>
            <span class="w-2 h-2 bg-pencil rounded-full animate-gentle-bounce" style="animation-delay: 0.2s"></span>
            <span class="w-2 h-2 bg-pencil rounded-full animate-gentle-bounce" style="animation-delay: 0.4s"></span>
          </div>
        </div>
      </div>
    </div>

    <form @submit.prevent="handleSend" class="flex gap-3">
      <input v-model="input" type="text" class="flex-1 px-4 py-3 text-lg border-[3px] border-pencil bg-white wobbly-sm focus:border-pen-blue focus:ring-2 focus:ring-pen-blue/20 outline-none" placeholder="说点什么吧...">
      <button type="submit" class="px-6 py-3 text-lg border-[3px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[2px] hover:translate-y-[2px] active:shadow-none active:translate-x-[4px] active:translate-y-[4px] transition-all wobbly">发送</button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { chat } from '@/api'

const messages = ref([])
const input = ref('')
const loading = ref(false)
let conversationId = null

async function handleSend() {
  if (!input.value.trim()) return
  const msg = input.value
  input.value = ''
  messages.value.push({ role: 'user', content: msg })
  loading.value = true
  try {
    const res = await chat(msg, conversationId)
    conversationId = res.data.conversation_id
    messages.value.push({ role: 'assistant', content: res.data.response, mood_label: res.data.mood, response_mode: res.data.response_mode })
  } catch (err) {
    messages.value.push({ role: 'assistant', content: '抱歉，我走神了，能再说一遍吗？' })
  } finally {
    loading.value = false
  }
}
</script>
