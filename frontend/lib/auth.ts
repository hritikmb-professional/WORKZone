'use client'

function parseJwt(token: string) {
  try {
    return JSON.parse(atob(token.split('.')[1]))
  } catch { return null }
}

export function getToken() {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('access_token')
}

export function getUser() {
  if (typeof window === 'undefined') return null
  const raw = localStorage.getItem('user')
  return raw ? JSON.parse(raw) : null
}

export function setAuth(data: { access_token: string; refresh_token: string }) {
  localStorage.setItem('access_token', data.access_token)
  localStorage.setItem('refresh_token', data.refresh_token)
  // Decode JWT to get employee_id, role, team_id
  const payload = parseJwt(data.access_token)
  if (payload) {
    localStorage.setItem('user', JSON.stringify({
      employee_id: payload.sub,
      role: payload.role,
      team_id: payload.team_id,
      name: localStorage.getItem('pending_name') || 'User',
    }))
    localStorage.removeItem('pending_name')
  }
}

export function setPendingName(name: string) {
  localStorage.setItem('pending_name', name)
}

export function clearAuth() {
  localStorage.clear()
}

export function isAuthenticated() {
  return !!getToken()
}
