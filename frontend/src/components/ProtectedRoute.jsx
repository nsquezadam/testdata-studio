import { useAuth } from '../auth/AuthContext'

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="center-message">Cargando sesión...</div>
  }

  if (!user) {
    return children({ authenticated: false })
  }

  return children({ authenticated: true })
}
