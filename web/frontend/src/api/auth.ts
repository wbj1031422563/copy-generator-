import type { ApiResponse } from '@/types/api'
import { apiPost } from '@/api/client'

export interface AuthStatus {
  enabled: boolean
  authenticated: boolean
  username: string | null
}

export async function fetchAuthStatus(): Promise<AuthStatus> {
  const res = await fetch('/api/auth/status', { credentials: 'include' })
  const payload = (await res.json()) as ApiResponse<AuthStatus>
  if (!res.ok || payload.ok === false || !payload.data) {
    throw new Error(
      typeof payload.detail === 'string' ? payload.detail : '无法获取登录状态',
    )
  }
  return payload.data
}

export async function login(username: string, password: string): Promise<string> {
  const data = await apiPost<{ username: string; auth_disabled?: boolean }>(
    '/api/auth/login',
    { username, password },
  )
  return data.username
}

export async function logout(): Promise<void> {
  await apiPost('/api/auth/logout', {})
}
