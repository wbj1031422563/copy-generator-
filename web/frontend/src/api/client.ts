import type { ApiResponse } from '@/types/api'

export class ApiError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

function unwrap<T>(payload: ApiResponse<T>, path: string): T {
  if (payload.ok === false) {
    throw new ApiError(
      typeof payload.detail === 'string' ? payload.detail : '请求失败',
    )
  }
  if (payload.data === undefined) {
    throw new ApiError(`接口 ${path} 返回异常（缺少 data 字段）`)
  }
  return payload.data
}

async function request<T>(
  path: string,
  opts: RequestInit & { body?: unknown } = {},
): Promise<T> {
  const headers: Record<string, string> = {
    ...(opts.headers as Record<string, string>),
  }
  let body = opts.body as BodyInit | undefined
  if (body !== undefined && typeof body !== 'string') {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(body)
  }

  const res = await fetch(path, { ...opts, headers, body, credentials: 'include' })
  if (res.status === 401 && !path.startsWith('/api/auth/')) {
    const redirect = encodeURIComponent(
      window.location.pathname + window.location.search,
    )
    window.location.assign(`/login?redirect=${redirect}`)
    throw new ApiError('请先登录')
  }
  if (!res.ok) {
    let msg = res.statusText
    try {
      const j = await res.json()
      if (typeof j.detail === 'string') msg = j.detail
      else if (Array.isArray(j.detail))
        msg = j.detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join('; ')
      else if (j.detail) msg = JSON.stringify(j.detail)
      else if (j.message) msg = j.message
      else msg = JSON.stringify(j)
    } catch {
      try {
        msg = await res.text()
      } catch {
        /* ignore */
      }
    }
    throw new ApiError(typeof msg === 'string' ? msg : JSON.stringify(msg))
  }
  return res.json() as Promise<T>
}

export async function apiGet<T>(path: string): Promise<T> {
  const r = await request<ApiResponse<T>>(path)
  return unwrap(r, path)
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const r = await request<ApiResponse<T>>(path, { method: 'POST', body })
  return unwrap(r, path)
}

export async function apiPut<T>(path: string, body?: unknown): Promise<T | void> {
  const r = await request<ApiResponse<T>>(path, { method: 'PUT', body })
  if (r.data === undefined) return undefined
  return r.data as T
}

export async function apiDelete(path: string): Promise<void> {
  await request(path, { method: 'DELETE' })
}

export async function apiPostRaw<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: 'POST', body })
}

export async function exportVariants(
  variants: unknown[],
  format: 'txt' | 'json',
): Promise<string> {
  const r = await request<{ ok: boolean; content: string }>('/api/export', {
    method: 'POST',
    body: { variants, format },
  })
  return r.content
}

export function downloadText(content: string, filename: string, mime: string) {
  const blob = new Blob([content], { type: mime })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename
  a.click()
  URL.revokeObjectURL(a.href)
}
