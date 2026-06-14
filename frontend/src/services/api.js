import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// Response interceptor — handle 401
api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('enterprise-ai-auth')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// Documents
export const uploadDocument = (file, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: e => onProgress?.(Math.round((e.loaded / e.total) * 100)),
  })
}
export const listDocuments = (params) => api.get('/documents/', { params })
export const getDocument = (id) => api.get(`/documents/${id}`)
export const deleteDocument = (id) => api.delete(`/documents/${id}`)

// Analytics
export const getAnalyticsOverview = () => api.get('/analytics/overview')
export const getAnalyticsTrends = (months = 6) => api.get('/analytics/trends', { params: { months } })
export const getRiskDistribution = () => api.get('/analytics/risk-distribution')
export const getRecentActivity = (limit = 10) => api.get('/analytics/recent-activity', { params: { limit } })

// Workflow
export const listWorkflows = (params) => api.get('/workflow/', { params })
export const getWorkflow = (id) => api.get(`/workflow/${id}`)
export const getWorkflowByDoc = (docId) => api.get(`/workflow/document/${docId}`)
export const updateWorkflow = (id, data) => api.patch(`/workflow/${id}`, data)

// Chat
export const createChatSession = (title) => api.post('/chat/sessions', null, { params: { title } })
export const listChatSessions = () => api.get('/chat/sessions')
export const sendMessage = (sessionId, data) => api.post(`/chat/sessions/${sessionId}/messages`, data)
export const getMessages = (sessionId) => api.get(`/chat/sessions/${sessionId}/messages`)

// Users
export const listUsers = () => api.get('/users/')
export const getMe = () => api.get('/auth/me')

export default api
