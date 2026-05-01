import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
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

export function getDiaries(page = 1, perPage = 10) {
  return api.get('/diaries', { params: { page, per_page: perPage } })
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

export function getGarden() {
  return api.get('/garden')
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

export default api
