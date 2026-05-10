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
      <h2 class="text-xl mb-3" style="font-family: 'Kalam', cursive; font-weight: 700;">本地数据</h2>
      <p class="text-sm text-pencil/60 mb-4">把日记、情绪记录和对话导出为 JSON 文件，只保存在你的电脑上。</p>
      <button @click="downloadExport" :disabled="exporting"
        class="px-4 py-2 text-sm border-[2px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[1px] hover:translate-y-[1px] active:shadow-none transition-all wobbly-sm disabled:opacity-50">
        {{ exporting ? '导出中...' : '导出本地数据' }}
      </button>
      <p v-if="exportMessage" class="text-sm text-green-600 mt-2">{{ exportMessage }}</p>
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
          <input v-model="apiKeyInput" type="password"
            class="w-full px-3 py-2 text-base border-[2px] border-pencil bg-white wobbly-sm focus:border-pen-blue focus:ring-2 outline-none"
            :placeholder="hasSavedApiKey ? '已保存，留空保持不变' : 'sk-...'"
            autocomplete="off">
          <p v-if="hasSavedApiKey" class="text-xs text-pencil/50 mt-1">已保存，留空则保持不变</p>
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
        <p v-if="error" class="text-accent text-sm mt-2">{{ error }}</p>
      </div>

      <p v-else class="text-sm text-pencil/60 pl-8">当前使用本地规则匹配模式，无需配置 API</p>
    </div>

    <!-- 自定义情绪词库暂时关闭：先不展示入口，也不触发相关 API。 -->
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getLLMConfig, saveLLMConfig, testLLMConnection, exportLocalData } from '@/api'

const auth = useAuthStore()
const user = auth.user
const error = ref('')

const llmConfig = reactive({
  enabled: false,
  base_url: '',
  model: 'deepseek-chat',
  temperature: 0.7
})
const apiKeyInput = ref('')
const hasSavedApiKey = ref(false)
const testing = ref(false)
const saving = ref(false)
const testResult = ref(null)
const saveSuccess = ref(false)
const exporting = ref(false)
const exportMessage = ref('')

async function fetchLLMConfig() {
  try {
    const res = await getLLMConfig()
    if (res.data) {
      const { api_key, api_key_saved, api_key_preview, ...safeConfig } = res.data
      Object.assign(llmConfig, safeConfig)
      hasSavedApiKey.value = Boolean(api_key_saved || api_key_preview || api_key?.includes('****'))
      apiKeyInput.value = ''
    }
  } catch {
    // keep defaults
  }
}

function buildLLMPayload() {
  const payload = { ...llmConfig }
  const key = apiKeyInput.value.trim()
  if (key) {
    payload.api_key = key
  }
  return payload
}

async function testConnection() {
  testing.value = true
  testResult.value = null
  try {
    const payload = buildLLMPayload()
    const res = await testLLMConnection({
      base_url: payload.base_url,
      api_key: payload.api_key,
      model: payload.model,
      temperature: payload.temperature
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
  error.value = ''
  try {
    const res = await saveLLMConfig(buildLLMPayload())
    if (res.data) {
      const { api_key, api_key_saved, api_key_preview, ...safeConfig } = res.data
      Object.assign(llmConfig, safeConfig)
      hasSavedApiKey.value = Boolean(api_key_saved || api_key_preview || api_key?.includes('****'))
      apiKeyInput.value = ''
    }
    saveSuccess.value = true
    setTimeout(() => { saveSuccess.value = false }, 3000)
  } catch (err) {
    error.value = err.message || '保存失败'
  } finally {
    saving.value = false
  }
}

async function downloadExport() {
  exporting.value = true
  exportMessage.value = ''
  error.value = ''
  try {
    const res = await exportLocalData()
    const payload = res.data
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `heart-garden-export-${new Date().toISOString().slice(0, 10)}.json`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
    exportMessage.value = '导出完成，文件已经保存到浏览器下载目录。'
    setTimeout(() => { exportMessage.value = '' }, 3000)
  } catch (err) {
    error.value = err.message || '导出失败'
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  fetchLLMConfig()
})
</script>
