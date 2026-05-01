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

    <div class="bg-white border-[3px] border-pencil p-6 wobbly-md shadow-hard-sm mb-6">
      <h2 class="text-xl mb-4" style="font-family: 'Kalam', cursive; font-weight: 700;">
        AI 对话模式
        <span :class="['ml-2 text-sm px-2 py-0.5 border-[2px] border-pencil wobbly-sm', llmConfig.enabled ? 'bg-green-200' : 'bg-yellow-200']">
          {{ llmConfig.enabled ? '大模型模式' : '规则模式' }}
        </span>
      </h2>

      <div class="mb-4">
        <label class="flex items-center gap-3 cursor-pointer">
          <input type="checkbox" v-model="llmConfig.enabled" class="w-5 h-5 border-[2px] border-pencil rounded">
          <span class="text-lg">启用大模型对话</span>
        </label>
        <p class="text-sm text-pencil/60 mt-1 ml-8">开启后使用大模型进行智能对话，关闭则使用本地规则匹配</p>
      </div>

      <div v-if="llmConfig.enabled" class="space-y-4 pl-8 border-l-[3px] border-pencil/20 ml-2">
        <div>
          <label class="block text-sm font-bold mb-1">API 基础 URL</label>
          <input v-model="llmConfig.base_url"
            class="w-full px-3 py-2 text-base border-[2px] border-pencil bg-white wobbly-sm focus:border-pen-blue focus:ring-2 outline-none"
            placeholder="https://api.deepseek.com/v1">
        </div>

        <div>
          <label class="block text-sm font-bold mb-1">API Key</label>
          <input v-model="llmConfig.api_key" type="password"
            class="w-full px-3 py-2 text-base border-[2px] border-pencil bg-white wobbly-sm focus:border-pen-blue focus:ring-2 outline-none"
            placeholder="sk-...">
          <p v-if="llmConfig.api_key && llmConfig.api_key.includes('****')" class="text-xs text-pencil/50 mt-1">已保存，留空则保持不变</p>
        </div>

        <div>
          <label class="block text-sm font-bold mb-1">模型名称</label>
          <input v-model="llmConfig.model"
            class="w-full px-3 py-2 text-base border-[2px] border-pencil bg-white wobbly-sm focus:border-pen-blue focus:ring-2 outline-none"
            placeholder="deepseek-chat">
        </div>

        <div>
          <label class="block text-sm font-bold mb-1">温度: {{ llmConfig.temperature }}</label>
          <input v-model.number="llmConfig.temperature" type="range" min="0" max="2" step="0.1"
            class="w-full accent-pen-blue">
          <div class="flex justify-between text-xs text-pencil/50">
            <span>精确 (0)</span>
            <span>创意 (2)</span>
          </div>
        </div>

        <div class="flex gap-3">
          <button @click="testConnection" :disabled="testing"
            class="px-4 py-2 text-sm border-[2px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[1px] hover:translate-y-[1px] active:shadow-none transition-all wobbly-sm disabled:opacity-50">
            {{ testing ? '测试中...' : '测试连接' }}
          </button>
          <button @click="saveConfig" :disabled="saving"
            class="px-4 py-2 text-sm border-[2px] border-pencil bg-pen-blue text-white shadow-hard hover:shadow-hard-hover hover:translate-x-[1px] hover:translate-y-[1px] active:shadow-none transition-all wobbly-sm disabled:opacity-50">
            {{ saving ? '保存中...' : '保存配置' }}
          </button>
        </div>

        <p v-if="testResult" :class="['text-sm', testResult.success ? 'text-green-600' : 'text-accent']">
          {{ testResult.success ? '连接成功！模型: ' + testResult.model : '连接失败: ' + testResult.message }}
        </p>
        <p v-if="saveSuccess" class="text-sm text-green-600">配置已保存</p>
      </div>

      <p v-else class="text-sm text-pencil/60 pl-8">当前使用本地规则匹配模式，无需配置 API</p>
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
import { getCustomWords, addCustomWord, deleteCustomWord, getLLMConfig, saveLLMConfig, testLLMConnection } from '@/api'

const auth = useAuthStore()
const user = auth.user
const words = ref([])
const error = ref('')
const newWord = reactive({ word: '', word_type: 'positive' })

const llmConfig = reactive({
  enabled: false,
  base_url: '',
  api_key: '',
  model: 'deepseek-chat',
  temperature: 0.7
})
const testing = ref(false)
const saving = ref(false)
const testResult = ref(null)
const saveSuccess = ref(false)

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

async function fetchLLMConfig() {
  try {
    const res = await getLLMConfig()
    if (res.data) {
      Object.assign(llmConfig, res.data)
    }
  } catch {
    // keep defaults
  }
}

async function testConnection() {
  testing.value = true
  testResult.value = null
  try {
    const res = await testLLMConnection({
      base_url: llmConfig.base_url,
      api_key: llmConfig.api_key,
      model: llmConfig.model
    })
    testResult.value = res.data
  } catch (err) {
    testResult.value = { success: false, message: err.message || '测试失败' }
  } finally {
    testing.value = false
  }
}

async function saveConfig() {
  saving.value = true
  saveSuccess.value = false
  try {
    const payload = { ...llmConfig }
    if (payload.api_key && payload.api_key.includes('****')) {
      delete payload.api_key
    }
    await saveLLMConfig(payload)
    saveSuccess.value = true
    setTimeout(() => { saveSuccess.value = false }, 3000)
  } catch (err) {
    error.value = err.message || '保存失败'
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchWords()
  fetchLLMConfig()
})
</script>
