import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'

import { apiFetch } from '../api/client'

/*
2026-11-15 Se Agrega un listener para el manejo de la inactividad de la sesion 
*/

const AuthContext = createContext(null)


export function AuthProvider({ children }) {

  const [user, setUser] = useState(null)

  const [loading, setLoading] =
    useState(true)

  const [sessionMessage, setSessionMessage] =
    useState('')


  useEffect(() => {

    const token =
      localStorage.getItem('tds_token')

    if (!token) {
      setLoading(false)
      return
    }


    apiFetch('/auth/me')
      .then(setUser)

      .catch(() => {
        localStorage.removeItem('tds_token')
        setUser(null)
      })

      .finally(() =>
        setLoading(false)
      )

  }, [])


  useEffect(() => {

    function handleSessionExpired() {

      localStorage.removeItem('tds_token')

      setUser(null)

      setSessionMessage(
        'Tu sesión ha expirado. Inicia sesión nuevamente.'
      )
    }


    window.addEventListener(
      'tds:session-expired',
      handleSessionExpired
    )


    return () => {

      window.removeEventListener(
        'tds:session-expired',
        handleSessionExpired
      )
    }

  }, [])


  async function login(email, password) {

    const data = await apiFetch(
      '/auth/login',
      {
        method: 'POST',

        body: JSON.stringify({
          email,
          password,
        }),
      }
    )


    localStorage.setItem(
      'tds_token',
      data.access_token
    )


    setSessionMessage('')

    setUser(data.user)

    return data.user
  }


  function logout() {

    localStorage.removeItem('tds_token')

    setUser(null)

    setSessionMessage('')
  }


  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      logout,
      sessionMessage,
      setSessionMessage,
    }),
    [
      user,
      loading,
      sessionMessage,
    ]
  )


  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}


export function useAuth() {
  return useContext(AuthContext)
}