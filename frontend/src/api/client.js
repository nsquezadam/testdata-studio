const API_URL =  import.meta.env.VITE_API_URL ||  'http://localhost:8000/api'

/*
2026-11-15
Se modifica la función apiFetch para controlar respuestas 401 Unauthorized.
Se diferencia entre un error de autenticación durante el login y una sesión expirada,
permitiendo eliminar el token y notificar al contexto de autenticación cuando corresponda.
*/

export async function apiFetch(path, options = {}) {
  const token = localStorage.getItem('tds_token')

  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(
    `${API_URL}${path}`,
    {
      ...options,
      headers,
    }
  )

  let body = null

  try {
    body = await response.json()
  } catch {
    body = null
  }

  if (!response.ok) {

    if (
      response.status === 401 &&
      path !== '/auth/login'
    ) {
      localStorage.removeItem('tds_token')

      window.dispatchEvent(
        new CustomEvent('tds:session-expired')
      )
    }

    const error = new Error(
      body?.detail ||
      'No fue posible completar la operación.'
    )

    error.status = response.status

    throw error
  }

  return body
}