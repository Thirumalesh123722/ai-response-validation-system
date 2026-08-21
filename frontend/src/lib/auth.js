const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const ACCESS_TOKEN_KEY = 'veritas_access_token'
const REFRESH_TOKEN_KEY = 'veritas_refresh_token'

// Refresh tokens are long-lived and sensitive, so localStorage is a
// pragmatic tradeoff for a fast-moving early product — an httpOnly cookie
// set by the backend is more secure against XSS and worth migrating to
// before handling real customer data at scale.
export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}
export function setTokens(access, refresh) {
  localStorage.setItem(ACCESS_TOKEN_KEY, access)
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
}
export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

async function parseErrorDetail(res) {
  try {
    const body = await res.json()
    return body.detail || res.statusText
  } catch {
    return res.statusText
  }
}

export async function signup({ organizationName, fullName, email, password }) {
  const res = await fetch(`${BASE_URL}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ organization_name: organizationName, full_name: fullName, email, password }),
  })
  if (!res.ok) throw new Error(await parseErrorDetail(res))
  const data = await res.json()
  setTokens(data.access_token, data.refresh_token)
  return data
}

export async function login({ email, password }) {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) throw new Error(await parseErrorDetail(res))
  const data = await res.json()
  setTokens(data.access_token, data.refresh_token)
  return data
}

export async function logout() {
  const refresh = getRefreshToken()
  clearTokens()
  if (refresh) {
    try {
      await fetch(`${BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refresh }),
      })
    } catch {
      // best-effort; tokens are already cleared client-side
    }
  }
}

async function tryRefresh() {
  const refresh = getRefreshToken()
  if (!refresh) return false
  try {
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    })
    if (!res.ok) {
      clearTokens()
      return false
    }
    const data = await res.json()
    setTokens(data.access_token, data.refresh_token)
    return true
  } catch {
    return false
  }
}

/** Authenticated fetch: attaches the access token, and if the server says
 * it's expired (401), refreshes once and retries automatically — the rest
 * of the app never has to think about token expiry. */
export async function authFetch(path, options = {}) {
  const doFetch = () => {
    const token = getAccessToken()
    return fetch(`${BASE_URL}${path}`, {
      ...options,
      headers: {
        ...(options.headers || {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })
  }

  let res
  try {
    res = await doFetch()
  } catch (err) {
    throw new Error(
      `Could not reach the backend at ${BASE_URL}${path}. Is it running? Original error: ${err.message}`
    )
  }

  if (res.status === 401) {
    const refreshed = await tryRefresh()
    if (refreshed) {
      res = await doFetch()
    }
  }
  return res
}
