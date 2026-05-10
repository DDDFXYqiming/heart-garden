<template>
  <div class="max-w-2xl mx-auto p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-3xl font-handwritten font-bold text-pencil">通知中心</h1>
      <button
        v-if="unread_count > 0"
        @click="markAllRead"
        class="text-sm text-blue-500 hover:underline"
      >
        全部已读 ({{ unread_count }})
      </button>
    </div>
    
    <div v-if="loading" class="text-center py-8 text-pencil/60">
      加载中...
    </div>
    
    <div v-else-if="notifications.length === 0" class="text-center py-8 text-pencil/60">
      暂无通知
    </div>
    
    <div v-else class="space-y-4">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        @click="markAsRead(notification)"
        class="p-4 border-[2px] border-pencil cursor-pointer transition-colors"
        :class="notification.is_read ? 'bg-white/50' : 'bg-white hover:bg-sticky'"
      >
        <div class="flex items-start justify-between">
          <div>
            <h3 class="font-bold text-pencil">{{ notification.title }}</h3>
            <p class="text-pencil/70 mt-1">{{ notification.content }}</p>
            <p class="text-xs text-pencil/40 mt-2">{{ formatTime(notification.created_at) }}</p>
          </div>
          <div v-if="!notification.is_read" class="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 mt-1"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getNotifications, markNotificationRead, markAllNotificationsRead } from '@/api'

const notifications = ref([])
const loading = ref(true)
const unread_count = ref(0)

async function loadNotifications() {
  try {
    const res = await getNotifications()
    if (res.success) {
      notifications.value = res.data.notifications
      unread_count.value = res.data.unread_count
    }
  } catch (error) {
    console.error('加载通知失败:', error)
  } finally {
    loading.value = false
  }
}

async function markAsRead(notification) {
  if (notification.is_read) return
  
  try {
    await markNotificationRead(notification.id)
    notification.is_read = true
    unread_count.value--
  } catch (error) {
    console.error('标记已读失败:', error)
  }
}

async function markAllRead() {
  try {
    const res = await markAllNotificationsRead()
    if (res.success) {
      notifications.value.forEach(n => n.is_read = true)
      unread_count.value = 0
    }
  } catch (error) {
    console.error('全部标记已读失败:', error)
  }
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadNotifications()
})
</script>
