import { useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import UsersPage from './UsersPage'

/* *************MODIFICACIONES********************
2026-11-15 Cambia Gestion de Usuarios  desahabilitado para el rol de Analista, y se habilita solo para Administrador.
*/
const analystModules = [
  'Proyectos y modelos',
  'Campos y reglas',
  'Generación de datos',
  'Resultados y ejecución',
]


export default function DashboardPage({ onLogout }) {
  const { user, logout } = useAuth()

  const [activeView, setActiveView] =
    useState('dashboard')


  const isAdmin =
    user?.rol === 'Administrador'


  const modules = isAdmin
    ? ['Gestión de usuarios']
    : analystModules


  function handleLogout() {
    logout()
    onLogout()
  }


  function goDashboard() {
    setActiveView('dashboard')
  }


  function goUsers() {
    if (isAdmin) {
      setActiveView('users')
    }
  }


  return (
    <div className="app-shell">

      <aside className="sidebar">

        <div>
          <span className="eyebrow sidebar-eyebrow">
            TestData Studio
          </span>

          <h2>Panel principal</h2>
        </div>


        <nav>

          <button
            type="button"
            className={
              activeView === 'dashboard'
                ? 'nav-item active'
                : 'nav-item'
            }
            onClick={goDashboard}
          >
            Dashboard
          </button>


          {isAdmin ? (
            <button
              type="button"
              className={
                activeView === 'users'
                  ? 'nav-item active'
                  : 'nav-item'
              }
              onClick={goUsers}
            >
              Gestión de usuarios
            </button>
          ) : (
            modules.map((module) => (
              <button
                type="button"
                className="nav-item"
                key={module}
                disabled
                title="Se habilitará en la siguiente iteración"
              >
                {module}
              </button>
            ))
          )}

        </nav>


        <button
          type="button"
          className="logout-button"
          onClick={handleLogout}
        >
          Cerrar sesión
        </button>

      </aside>


      <main className="dashboard-content">

        {activeView === 'users' && isAdmin ? (

          <UsersPage currentUser={user} />

        ) : (

          <>
            <header className="topbar">

              <div>
                <span className="eyebrow">
                  Sesión activa
                </span>

                <h1>
                  Hola, {user?.nombre}
                </h1>
              </div>


              <div className="profile-chip">
                <strong>
                  {user?.nombre} {user?.apellido}
                </strong>

                <span>
                  {user?.rol}
                </span>
              </div>

            </header>


            <section className="role-banner">

              <div>

                <h2>
                  Perfil: {user?.rol}
                </h2>

                <p>
                  {isAdmin
                    ? 'Tienes acceso a las funciones administrativas del MVP.'
                    : 'Tienes acceso al flujo operativo de preparación y seguimiento de pruebas.'}
                </p>

              </div>

              <span className="status-badge">
                Activo
              </span>

            </section>


            <section className="metric-grid">

              <article className="metric-card">
                <span>Escenarios</span>
                <strong>0</strong>
                <small>
                  Se habilitará con M03
                </small>
              </article>


              <article className="metric-card">
                <span>Aprobados</span>
                <strong>0</strong>
                <small>
                  Se habilitará con M04
                </small>
              </article>


              <article className="metric-card">
                <span>Fallidos</span>
                <strong>0</strong>
                <small>
                  Se habilitará con M04
                </small>
              </article>


              <article className="metric-card">
                <span>Pendientes</span>
                <strong>0</strong>
                <small>
                  Se habilitará con M04
                </small>
              </article>

            </section>


            <section className="module-section">

              <h2>
                Funciones disponibles para tu perfil
              </h2>


              <div className="module-grid">

                {modules.map((module) => (

                  <article
                    className="module-card"
                    key={module}
                  >

                    <h3>{module}</h3>

                    <p>
                      {module === 'Gestión de usuarios'
                        ? 'Administra usuarios, perfiles y estados de acceso.'
                        : 'Funcionalidad planificada para la siguiente iteración de desarrollo.'}
                    </p>

                    {module === 'Gestión de usuarios' && (
                      <button
                        type="button"
                        className="module-link"
                        onClick={goUsers}
                      >
                        Abrir gestión →
                      </button>
                    )}

                  </article>

                ))}

              </div>

            </section>

          </>

        )}

      </main>

    </div>
  )
}