import axios, { type InternalAxiosRequestConfig } from 'axios'

import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  isAccessTokenUsable,
  storeTokens,
  type TokenPair,
} from '../auth/session'


interface RetryableRequest extends InternalAxiosRequestConfig {
  _authRetry?: boolean
}

const authClient = axios.create()
const apiClient = axios.create()
let refreshPromise: Promise<string | null> | null = null

const notifySignedOut = () => window.dispatchEvent(new CustomEvent('auth:signed-out'))
const isOrchestratorRequest = (url?: string) =>
  url === '/api/v1' || Boolean(url?.startsWith('/api/v1/'))

export const refreshAccessToken = (): Promise<string | null> => {
  if (refreshPromise) return refreshPromise

  refreshPromise = (async () => {
    const refreshToken = getRefreshToken()
    if (!refreshToken) return null

    try {
      const response = await authClient.post<TokenPair>('/auth/refresh', {
        refresh_token: refreshToken,
      })
      storeTokens(response.data)
      return response.data.access_token
    } catch {
      clearSession()
      return null
    } finally {
      refreshPromise = null
    }
  })()

  return refreshPromise
}

export const ensureAuthenticated = async () => {
  if (isAccessTokenUsable(getAccessToken())) return true
  return Boolean(await refreshAccessToken())
}

export const login = async (username: string, password: string) => {
  const form = new URLSearchParams({ username, password })
  const response = await authClient.post<TokenPair>('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  storeTokens(response.data)
}

export const logout = async () => {
  const refreshToken = getRefreshToken()
  if (refreshToken) {
    try {
      await authClient.post('/auth/logout', { refresh_token: refreshToken })
    } catch {
      // Local sign-out must still complete if Auth Service is unavailable.
    }
  }
  clearSession()
  notifySignedOut()
}

apiClient.interceptors.request.use((config) => {
  const accessToken = getAccessToken()
  if (accessToken && isOrchestratorRequest(config.url)) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const request = error.config as RetryableRequest | undefined
    const challenge = error.response?.headers?.['www-authenticate']
    const isBearerChallenge =
      isOrchestratorRequest(request?.url) &&
      error.response?.status === 401 &&
      typeof challenge === 'string' &&
      challenge.toLowerCase() === 'bearer'

    if (isBearerChallenge && request?._authRetry) {
      clearSession()
      notifySignedOut()
      return Promise.reject(error)
    }

    if (
      !isBearerChallenge ||
      !request ||
      request._authRetry
    ) {
      return Promise.reject(error)
    }

    request._authRetry = true
    const accessToken = await refreshAccessToken()
    if (!accessToken) {
      notifySignedOut()
      return Promise.reject(error)
    }

    request.headers.Authorization = `Bearer ${accessToken}`
    return apiClient.request(request)
  },
)

export default apiClient
