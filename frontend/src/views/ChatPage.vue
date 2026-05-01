<template>
  <div class="max-w-6xl mx-auto flex gap-4">
    <!-- 左侧对话列表 -->
    <div class="w-64 flex-shrink-0">
      <h2 class="text-xl mb-3" style="font-family: 'Kalam', cursive; font-weight: 700;">对话记录</h2>
      <div class="space-y-2">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          @click="loadConversation(conv.id)"
          :class="[
            'p-3 border-[2px] border-pencil cursor-pointer transition-all',
            currentConvId === conv.id
              ? 'bg-pen-blue/10 shadow-hard-sm'
              : 'bg-white hover:bg-pen-yellow/20',
            'wobbly-sm'
          ]"
        >
          <p class="text-sm font-semibold truncate">{{ conv.title || '新对话' }}</p>
          <p class="text-xs text-pencil/50 mt-1 truncate">{{ conv.last_message || '暂无消息' }}</p>
        </div>
        <div v-if="conversations.length === 0" class="text-center text-pencil/40 text-sm py-8">
          还没有对话哦~<br>开始和 AI 聊聊吧
        </div>
      </div>
    </div>

    <!-- 右侧聊天区域 -->
    <div class="flex-1 max-w-2xl">
      <h1 class="text-3xl md:text-4xl mb-6" style="font-family: 'Kalam', cursive; font-weight: 700;">AI 陪伴</h1>

      <div class="bg-white border-[3px] border-pencil wobbly-md shadow-hard-sm mb-4 h-[400px] md:h-[500px] overflow-y-auto p-4 space-y-3">
        <div v-if="messages.length === 0 && !loading" class="text-center text-pencil/30 py-20">
          选择左侧对话，或开始新的聊天~
        </div>
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
        <button type="submit" :disabled="!input.trim()" class="px-6 py-3 text-lg border-[3px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[2px] hover:translate-y-[2px] active:shadow-none active:translate-x-[4px] active:translate-y-[4px] transition-all wobbly disabled:opacity-50 disabled:cursor-not-allowed">发送</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { chat, getConversations, getConversation } from '@/api'

const messages = ref([])
const conversations = ref([])
const input = ref('')
const loading = ref(false)
const currentConvId = ref(null)

// 页面加载时获取对话列表，自动加载最新对话
onMounted(async () => {
  try {
    const res = await getConversations()
    if (res.data && res.data.length > 0) {
      conversations.value = res.data
      // 自动加载最新对话
      await loadConversation(res.data[0].id)
    }
  } catch (err) {
    console.error('获取对话列表失败:', err)
  }
})

// 加载指定对话的消息
async function loadConversation(id) {
  currentConvId.value = id
  loading.value = true
  try {
    const res = await getConversation(id)
    if (res.data && res.data.messages) {
      // 按时间顺序排列（API 已经排好了）
      messages.value = res.data.messages.map(m => ({
        role: m.role,
        content: m.content,
        mood_label: m.mood_label || undefined,
        response_mode: undefined  // 历史消息不保存 response_mode
      }))
      // 滚动到底部
      setTimeout(() => {
        const chatBox = document.querySelector('.overflow-y-auto')
        if (chatBox) chatBox.scrollTop = chatBox.scrollHeight
      }, 50)
    }
  } catch (err) {
    console.error('加载对话失败:', err)
    messages.value = []
  } finally {
    loading.value = false
  }
}

// 发送消息（SSE 流式）
async function handleSend() {
  if (!input.value.trim()) return
  const msg = input.value
  input.value = ''

  messages.value.push({ role: 'user', content: msg })
  // 添加空的 assistant 消息用于流式填充
  const assistantMsg = { role: 'assistant', content: '', mood_label: undefined, response_mode: undefined }
  messages.value.push(assistantMsg)
  loading.value = true

  try {
    const response = await chatStream(msg, currentConvId.value)
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop() // 保留未完成的行

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'chunk') {
            assistantMsg.content += data.content
          } else if (data.type === 'done') {
            currentConvId.value = data.conversation_id
            assistantMsg.mood_label = data.mood
            assistantMsg.response_mode = data.response_mode
          }
        } catch (e) { /* ignore parse errors */ }
      }
    }

    refreshConversationList()
  } catch (err) {
    assistantMsg.content = assistantMsg.content || '抱歉，我走神了，能再说一遍吗？'
  } finally {
    loading.value = false
  }
}

// 刷新对话列表（不改变当前选中）
async function refreshConversationList() {
  try {
    const res = await getConversations()
    if (res.data) {
      conversations.value = res.data
    }
  } catch (err) {
    // 静默失败
  }
}
</script>
