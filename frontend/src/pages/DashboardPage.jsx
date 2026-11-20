import { useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import UsersPage from './UsersPage'
import ProjectsPage from './ProjectsPage'
import CamposRulesPage from './CamposRulesPage'
import GenerationPage from './GenerationPage'

/* *************MODIFICACIONES********************
2026-11-15 Cambia Gestion de Usuarios  desahabilitado para el rol de Analista, y se habilita solo para Administrador.
2026-11-18 - M02
Se habilita el acceso a Campos y reglas para Analista/Tester y se integra
CamposRulesPage al Dashboard. Gestión de usuarios continúa exclusiva para
Administrador. Motivo: incorporación funcional de M02 al frontend.

2026-11-18 - M03 / CP-06
Se habilita Generación de datos para Analista/Tester e integra GenerationPage.
Motivo: implementar HU-05 / RF08-RF10. Exportación y resultados continúan
reservados para CP-07 y M04 respectivamente.
*/

/*
2026-11-19 - AJUSTE UX
Se retiran referencias visibles a módulos/documentación interna (por ejemplo M04).
Motivo: la interfaz debe comunicar estados funcionales al usuario y no códigos
de planificación o requerimientos técnicos.
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


  function goProjects() {
    if (!isAdmin) {
      setActiveView('projects')
    }
  }


  function goConfiguration() {
    if (!isAdmin) {
      setActiveView('configuration')
    }
  }


  function goGeneration() {
    if (!isAdmin) {
      setActiveView('generation')
    }
  }


  function getAnalystModuleConfig(module) {
    if (module === 'Proyectos y modelos') {
      return {
        enabled: true,
        active: activeView === 'projects',
        title: 'Gestión de proyectos y modelos',
        onClick: goProjects,
      }
    }

    if (module === 'Campos y reglas') {
      return {
        enabled: true,
        active: activeView === 'configuration',
        title: 'Configuración de campos y reglas de negocio',
        onClick: goConfiguration,
      }
    }

    if (module === 'Generación de datos') {
      return {
        enabled: true,
        active: activeView === 'generation',
        title: 'Generación de datos y escenarios de prueba',
        onClick: goGeneration,
      }
    }

    return {
      enabled: false,
      active: false,
      title: 'Se habilitará en la siguiente iteración',
      onClick: undefined,
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

            modules.map((module) => {
              const config =
                getAnalystModuleConfig(module)

              return (
                <button
                  type="button"
                  key={module}
                  className={
                    config.active
                      ? 'nav-item active'
                      : 'nav-item'
                  }
                  disabled={!config.enabled}
                  title={config.title}
                  onClick={config.onClick}
                >
                  {module}
                </button>
              )
            })

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

        ) : activeView === 'projects' && !isAdmin ? (

          <ProjectsPage />

        ) : activeView === 'configuration' && !isAdmin ? (

          <CamposRulesPage />

        ) : activeView === 'generation' && !isAdmin ? (

          <GenerationPage />

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
                <strong>—</strong>
                <small>
                  Consulta disponible en Generación de datos
                </small>
              </article>

              <article className="metric-card">
                <span>Aprobados</span>
                <strong>0</strong>
                <small>
                  Se actualizará al registrar ejecuciones
                </small>
              </article>

              <article className="metric-card">
                <span>Fallidos</span>
                <strong>0</strong>
                <small>
                  Se actualizará al registrar ejecuciones
                </small>
              </article>

              <article className="metric-card">
                <span>Pendientes</span>
                <strong>0</strong>
                <small>
                  Se actualizará al registrar ejecuciones
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
                        : module === 'Proyectos y modelos'
                          ? 'Crea y administra proyectos de prueba y sus modelos de datos asociados.'
                          : module === 'Campos y reglas'
                            ? 'Configura los campos del modelo y sus reglas de negocio.'
                            : module === 'Generación de datos'
                              ? 'Genera escenarios válidos, inválidos y límite con trazabilidad.'
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

                    {module === 'Proyectos y modelos' && (
                      <button
                        type="button"
                        className="module-link"
                        onClick={goProjects}
                      >
                        Abrir gestión →
                      </button>
                    )}

                    {module === 'Campos y reglas' && (
                      <button
                        type="button"
                        className="module-link"
                        onClick={goConfiguration}
                      >
                        Abrir configuración →
                      </button>
                    )}

                    {module === 'Generación de datos' && (
                      <button
                        type="button"
                        className="module-link"
                        onClick={goGeneration}
                      >
                        Abrir generación →
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