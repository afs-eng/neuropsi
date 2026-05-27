function normalizeApiBaseUrl() {
  // Prioridade: variável de ambiente NEXT_PUBLIC_API_BASE_URL
  const envUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (envUrl) return envUrl.replace(/\/+$/, ''); // remove trailing slash

  const isBrowser = typeof window !== 'undefined';
  const isLocalHost = isBrowser && (
    window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1'
  );

  // Em desenvolvimento local fora do Docker, o navegador fala direto com o Django.
  if (isLocalHost) return 'http://127.0.0.1:8000';

  // Fallback para produção (deve ser configurado via NEXT_PUBLIC_API_BASE_URL)
  return '';
}

const API_URL = normalizeApiBaseUrl();

export function resolveApiUrl(path: string) {
  if (!path) return API_URL
  if (/^https?:\/\//i.test(path)) return path
  return `${API_URL}${path.startsWith('/') ? path : `/${path}`}`
}

if (typeof window !== 'undefined') {
  console.log('🔌 Conexão Direta Estabelecida:', API_URL);
}

export interface ApiError {
  message: string
  status: number
}

function stringifyApiError(value: unknown): string {
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)

  if (Array.isArray(value)) {
    const items = value
      .map((item) => stringifyApiError(item))
      .filter(Boolean)
    return items.join(', ')
  }

  if (value && typeof value === 'object') {
    if ('msg' in value && typeof (value as { msg?: unknown }).msg === 'string') {
      return (value as { msg: string }).msg
    }

    if ('message' in value) {
      return stringifyApiError((value as { message?: unknown }).message)
    }

    if ('detail' in value) {
      return stringifyApiError((value as { detail?: unknown }).detail)
    }

    const entries = Object.entries(value as Record<string, unknown>)
      .map(([key, entryValue]) => {
        const text = stringifyApiError(entryValue)
        return text ? `${key}: ${text}` : ''
      })
      .filter(Boolean)

    return entries.join(', ')
  }

  return ''
}

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

  const isGetRequest = !options.method || options.method === 'GET'
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
  
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  let res: Response

  try {
    res = await fetch(`${API_URL}${normalizedEndpoint}`, {
      ...options,
      cache: isGetRequest ? 'no-store' : undefined,
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
        ...options.headers,
      },
    })
  } catch {
    throw {
      message: 'Nao foi possivel conectar ao servidor. Verifique se o backend esta em execucao.',
      status: 0,
    } satisfies ApiError
  }

  if (!res.ok) {
    let errorMessage = `Erro: ${res.status}`
    try {
      const errorData = await res.json()
      const normalizedError = stringifyApiError(errorData)
      if (normalizedError) {
        errorMessage = normalizedError
      }
    } catch {}
    const error: ApiError = {
      message: errorMessage,
      status: res.status,
    }
    throw error
  }

  const text = await res.text()
  if (!text) return {} as T
  return JSON.parse(text)
}

export const api = {
  get: <T>(url: string) => fetchAPI<T>(url),
  post: <T>(url: string, data: unknown) =>
    fetchAPI<T>(url, { method: 'POST', body: data instanceof FormData ? data : JSON.stringify(data) }),
  put: <T>(url: string, data: unknown) =>
    fetchAPI<T>(url, { method: 'PUT', body: data instanceof FormData ? data : JSON.stringify(data) }),
  patch: <T>(url: string, data: unknown) =>
    fetchAPI<T>(url, { method: 'PATCH', body: data instanceof FormData ? data : JSON.stringify(data) }),
  delete: <T>(url: string) => fetchAPI<T>(url, { method: 'DELETE' }),
}

// Auth helpers
export function setToken(token: string) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('token', token)
  }
}

export function getToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('token')
  }
  return null
}

export function removeToken() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('token')
  }
}
