import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
})

// Attach token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401) {
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_URL}/api/v1/auth/refresh`, { refresh_token: refresh })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          err.config.headers.Authorization = `Bearer ${data.access_token}`
          return api(err.config)
        } catch {
          localStorage.clear()
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(err)
  }
)

// Auth
export const authApi = {
  register: (data: { name: string; email: string; password: string }) =>
    api.post('/auth/register', data),
  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),
  logout: (refresh_token: string) =>
    api.post('/auth/logout', { refresh_token }),
}

// Meetings
export const meetingsApi = {
  upload: (formData: FormData) =>
    api.post('/meetings/upload-meeting', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  getSummary: (id: string) =>
    api.get(`/meetings/meeting/${id}/summary`),
  search: (q: string) =>
    api.get(`/meetings/meetings/search?q=${encodeURIComponent(q)}`),
  updateActionItem: (id: string, status: string) =>
    api.patch(`/meetings/action-items/${id}/status?status_value=${status}`),
}

// Analytics
export const analyticsApi = {
  getEmployee: (id: string, weeks = 12) =>
    api.get(`/analytics/employee/${id}/analytics?weeks=${weeks}`),
  getTeam: (id: string) =>
    api.get(`/analytics/team/${id}/insights`),
  triggerScore: (id: string) =>
    api.post(`/analytics/employee/${id}/score`),
}
