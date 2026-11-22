import { useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import testDataCentrifuga from '../assets/Centrífuga_datos.png'



/*
2026-11-15
Se agrega un listener para detectar la expiración de la sesión.
Cuando se recibe el evento de sesión expirada, se elimina el token almacenado,
se limpia el usuario autenticado y se informa al usuario para volver a iniciar sesión.
*/
export default function LoginPage({ onSuccess }) {
  const {login, sessionMessage, setSessionMessage,} = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setMessage('')
    setSessionMessage('')

    // HU-01-CA05: campos obligatorios.
    if (!email.trim() || !password) {
      setMessage('Completa correo electrónico y contraseña.')
      return
    }

    setSubmitting(true)
    try {
      await login(email.trim(), password)
      onSuccess()
    } catch (error) {
      setMessage(error.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="login-shell">
      <section className="brand-panel">
        <h1>TestData Studio</h1>
        <p>Generación y seguimiento de datos de prueba basados en reglas de negocio.</p>
           <div className="brand-visual">
      <img
        src={testDataCentrifuga}
        alt="Proceso de generación de datos de prueba de TestData Studio"
      />
    </div>
        <div className="trace-card">
           <span>Regla</span><b>→</b><span>Escenario</span><b>→</b><span>Dato</span><b>→</b><span>Resultado</span>
        </div>
      </section>

      <section className="login-panel">
        <form className="login-card" onSubmit={handleSubmit} noValidate>
          <div>
            <span className="eyebrow">Acceso restringido</span>
            <h2>Iniciar sesión</h2>
            <p>Ingresa con una cuenta registrada en TestData Studio.</p>
          </div>

          <label>
            Correo electrónico
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
              placeholder="usuario@correo.cl"
            />
          </label>

          <label>
            Contraseña
            <div className="password-row">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                placeholder="••••••••"
              />
              <button
                type="button"
                className="ghost-button"
                onClick={() => setShowPassword((value) => !value)}
              >
                {showPassword ? 'Ocultar' : 'Ver'}
              </button>
            </div>
          </label>

          {(message || sessionMessage) && (<div className="validation-message" role="alert">{message || sessionMessage}</div>)}

          <button className="primary-button" type="submit" disabled={submitting}>
            {submitting ? 'Validando...' : 'Iniciar sesión'}
          </button>

          <small>TestData Studio · Ingeniería Informática</small>
        </form>
      </section>
    </main>
  )
}
