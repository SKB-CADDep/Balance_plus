const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}

interface JwtPayload {
  exp?: number
  type?: string
}

export const getAccessToken = () => window.localStorage.getItem(ACCESS_TOKEN_KEY)
export const getRefreshToken = () => window.localStorage.getItem(REFRESH_TOKEN_KEY)

export const storeTokens = (tokens: TokenPair) => {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token)
  window.localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
}

export const clearSession = () => {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY)
  window.localStorage.removeItem(REFRESH_TOKEN_KEY)
}

const decodePayload = (token: string): JwtPayload | null => {
  try {
    const encodedPayload = token.split('.')[1]
    if (!encodedPayload) return null
    const normalized = encodedPayload.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=')
    return JSON.parse(window.atob(padded)) as JwtPayload
  } catch {
    return null
  }
}

export const isAccessTokenUsable = (token: string | null, clockSkewSeconds = 30) => {
  if (!token) return false
  const payload = decodePayload(token)
  if (!payload?.exp || payload.type !== 'access') return false
  return payload.exp > Math.floor(Date.now() / 1000) + clockSkewSeconds
}
