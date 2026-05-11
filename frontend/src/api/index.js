import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  response => response.data,
  error => {
    const data = error.response?.data
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.hash = '#/login'
    }
    return Promise.reject(data?.error || { message: '网络错误' })
  }
)

export function register(username, email, password) {
  return api.post('/auth/register', { username, email, password })
}

export function login(username, email, password) {
  return api.post('/auth/login', { username, email, password })
}

export function getMe() {
  return api.get('/auth/me')
}

export function getDiaries(page = 1, perPage = 10, filters = {}) {
  return api.get('/diaries', { params: { page, per_page: perPage, ...filters } })
}

export function getDiary(id) {
  return api.get(`/diaries/${id}`)
}

export function createDiary(title, content) {
  return api.post('/diaries', { title, content })
}

export function updateDiary(id, data) {
  return api.put(`/diaries/${id}`, data)
}

export function deleteDiary(id) {
  return api.delete(`/diaries/${id}`)
}

export function chat(message, conversationId = null) {
  return api.post('/chat', { message, conversation_id: conversationId })
}

export async function chatStream(message, conversationId = null) {
  const token = localStorage.getItem('token')
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    },
    body: JSON.stringify({ message, conversation_id: conversationId })
  })

  if (!response.ok) {
    let errorMessage = `请求失败 (${response.status})`
    try {
      const data = await response.clone().json()
      errorMessage = data?.error?.message || errorMessage
    } catch (e) {
      // 保留默认错误信息
    }
    throw new Error(errorMessage)
  }

  if (!response.body) {
    throw new Error('浏览器不支持流式响应')
  }

  return response
}

export function getConversations() {
  return api.get('/conversations')
}

export function getConversation(id) {
  return api.get(`/conversations/${id}`)
}

export function deleteConversation(id) {
  return api.delete(`/conversations/${id}`)
}

export function getMoodTrend(days = 7) {
  return api.get('/mood/trend', { params: { days } })
}

export function getMoodDistribution(days = 7) {
  return api.get('/mood/distribution', { params: { days } })
}

export function analyzeMood(text) {
  return api.post('/mood/analyze', { text })
}

export function getStats() {
  return api.get('/stats/overview')
}

export function exportLocalData() {
  return api.get('/export')
}

export function getGarden() {
  return api.get('/garden')
}

export function getGardenWorld() {
  return api.get('/garden/world')
}

export function getCustomWords() {
  return api.get('/mood/words')
}

export function addCustomWord(word, category, wordType) {
  return api.post('/mood/words', { word, category, word_type: wordType })
}

export function deleteCustomWord(id) {
  return api.delete(`/mood/words/${id}`)
}

export function getLLMConfig() {
  return api.get('/llm/config')
}

export function saveLLMConfig(config) {
  return api.post('/llm/config', config)
}

export function testLLMConnection(config) {
  return api.post('/llm/test', config)
}

export function getReminderSettings() {
  return api.get('/reminders/settings')
}

export function updateReminderSettings(settings) {
  return api.put('/reminders/settings', settings)
}

export function getNotifications(params) {
  return api.get('/notifications', { params })
}

export function markNotificationRead(id) {
  return api.put(`/notifications/${id}/read`)
}

export function markAllNotificationsRead() {
  return api.put('/notifications/read-all')
}

export function getCommunityPosts(params) {
  return api.get('/community/posts', { params })
}

export function createCommunityPost(data) {
  return api.post('/community/posts', data)
}

export default api
