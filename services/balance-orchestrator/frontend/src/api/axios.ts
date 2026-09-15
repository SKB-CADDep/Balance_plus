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

const oauthErrors: Record<string, string> = {
  gitlab_authorization_denied: 'Авторизация в GitLab была отменена',
  invalid_oauth_state: 'Сессия входа устарела. Попробуйте войти ещё раз',
  gitlab_access_denied: 'У вашей учётной записи GitLab нет доступа к Balance+',
  gitlab_oauth_failed: 'GitLab не смог завершить авторизацию',
  user_store_unavailable: 'Сервис пользователей временно недоступен',
}

export interface OAuthCallbackResult {
  handled: boolean
  authenticated: boolean
  error?: string
}

const clearOAuthParameters = () => {
  const url = new URL(window.location.href)
  url.searchParams.delete('auth_code')
  url.searchParams.delete('auth_error')
  window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`)
}

export const completeGitLabLogin = async (): Promise<OAuthCallbackResult> => {
  const params = new URLSearchParams(window.location.search)
  const error = params.get('auth_error')
  const code = params.get('auth_code')
  if (!error && !code) return { handled: false, authenticated: false }

  clearOAuthParameters()
  if (error) {
    return {
      handled: true,
      authenticated: false,
      error: oauthErrors[error] || 'Не удалось войти через GitLab',
    }
  }

  try {
    const response = await authClient.post<TokenPair>('/auth/gitlab/exchange', { code })
    storeTokens(response.data)
    return { handled: true, authenticated: true }
  } catch {
    clearSession()
    return {
      handled: true,
      authenticated: false,
      error: 'Код входа недействителен или уже использован',
    }
  }
}

export const login = () => {
  window.location.assign('/auth/gitlab/login')
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
