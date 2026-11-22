const API_URL =  import.meta.env.VITE_API_URL ||  'http://localhost:8000/api'

/*
2026-11-15
Se modifica la función apiFetch para controlar respuestas 401 Unauthorized.
Se diferencia entre un error de autenticación durante el login y una sesión expirada,
permitiendo eliminar el token y notificar al contexto de autenticación cuando corresponda.
*/

export async function apiFetch(path, options = {}) {
  const token = localStorage.getItem('tds_token')

  // MODIFICACIÓN 2026-11-20 - M04 / CP-09
  // Si el body es FormData no se fuerza Content-Type: el navegador debe agregar
  // automáticamente el boundary multipart para la carga de archivos CSV.
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
  const headers = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
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

/*
2026-11-20 - M03 / CP-07
Se agrega apiDownload para descargar archivos protegidos por JWT sin duplicar
la lógica de expiración de sesión. Se utiliza en exportación CSV/JSON (RF11).

AJUSTE 2026-11-20 - CP-07 V3
Se incorpora fallbackFilename porque Content-Disposition puede no estar visible
para JavaScript en una petición CORS. El nombre ya no queda como testdata_export.
*/
export async function apiDownload(path, fallbackFilename = 'testdata_export') {
  const token = localStorage.getItem('tds_token')
  const headers = {}

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(`${API_URL}${path}`, { headers })

  if (!response.ok) {
    let detail = null
    try {
      const body = await response.json()
      detail = body?.detail
    } catch {
      detail = null
    }

    if (response.status === 401) {
      localStorage.removeItem('tds_token')
      window.dispatchEvent(new CustomEvent('tds:session-expired'))
    }

    const error = new Error(detail || 'No fue posible descargar el archivo.')
    error.status = response.status
    throw error
  }

  const blob = await response.blob()
  const disposition = response.headers.get('Content-Disposition') || ''
  const match = disposition.match(/filename="?([^";]+)"?/i)
  const filename = match?.[1] || fallbackFilename

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)

  return filename
}
