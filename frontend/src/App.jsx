import { useState } from 'react'
import { AuthProvider, useAuth } from './auth/AuthContext'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import './styles.css'

function AppContent() {
  const { user, loading } = useAuth()
  const [, forceRender] = useState(0)

  if (loading) {
    return <div className="center-message">Cargando TestData Studio...</div>
  }

  if (!user) {
    return <LoginPage onSuccess={() => forceRender((v) => v + 1)} />
  }

  return <DashboardPage onLogout={() => forceRender((v) => v + 1)} />
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}
