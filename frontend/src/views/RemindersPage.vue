<template>
  <div class="max-w-2xl mx-auto p-6">
    <h1 class="text-3xl font-handwritten font-bold text-pencil mb-6">提醒设置</h1>
    
    <div v-if="loading" class="text-center py-8 text-pencil/60">
      加载中...
    </div>
    
    <div v-else class="space-y-6">
      <div
        v-for="setting in settings"
        :key="setting.reminder_type"
        class="bg-white/80 border-[2px] border-pencil p-4 wobbly-sm"
      >
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-handwritten font-bold text-pencil">
            {{ setting.reminder_type === 'mood_alert' ? '情绪预警' : '每日关怀' }}
          </h2>
          <label class="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              v-model="setting.enabled"
              class="sr-only peer"
            />
            <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-500"></div>
          </label>
        </div>
        
        <div v-if="setting.reminder_type === 'mood_alert'" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-pencil/70 mb-1">
              情绪分数阈值（低于此分数触发预警）
            </label>
            <input
              type="number"
              v-model.number="setting.threshold_score"
              min="0"
              max="100"
              class="w-full px-3 py-2 border-[2px] border-pencil bg-white"
            />
          </div>
        </div>
        
        <div class="mt-4 space-y-2">
          <div class="flex items-center gap-2">
            <label class="text-sm text-pencil/70">免打扰开始：</label>
            <input
              type="time"
              v-model="setting.quiet_hours_start"
              class="px-2 py-1 border-[2px] border-pencil bg-white"
            />
          </div>
          <div class="flex items-center gap-2">
            <label class="text-sm text-pencil/70">免打扰结束：</label>
            <input
              type="time"
              v-model="setting.quiet_hours_end"
              class="px-2 py-1 border-[2px] border-pencil bg-white"
            />
          </div>
        </div>
      </div>
      
      <button
        @click="saveSettings"
        :disabled="saving"
        class="w-full py-3 bg-pencil text-white font-handwritten text-lg border-[2px] border-pencil hover:bg-pencil/80 transition-colors disabled:opacity-50"
      >
        {{ saving ? '保存中...' : '保存设置' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getReminderSettings, updateReminderSettings } from '@/api'

const settings = ref([])
const loading = ref(true)
const saving = ref(false)

async function loadSettings() {
  try {
    const res = await getReminderSettings()
    if (res.success) {
      settings.value = res.data
    }
  } catch (error) {
    console.error('加载提醒设置失败:', error)
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  try {
    const res = await updateReminderSettings(settings.value)
    if (res.success) {
      alert('设置已保存')
    }
  } catch (error) {
    console.error('保存设置失败:', error)
    alert('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>
