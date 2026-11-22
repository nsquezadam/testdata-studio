import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import UsersPage from './UsersPage'
import ProjectsPage from './ProjectsPage'
import CamposRulesPage from './CamposRulesPage'
import GenerationPage from './GenerationPage'
import ExecutionPage from './ExecutionPage'
import { getDashboardSummary } from '../api/dashboard'

/* *************MODIFICACIONES********************
2026-11-15 Cambia Gestion de Usuarios  desahabilitado para el rol de Analista, y se habilita solo para Administrador.
2026-11-18 - M02
Se habilita el acceso a Campos y reglas para Analista/Tester y se integra
CamposRulesPage al Dashboard. Gestión de usuarios continúa exclusiva para
Administrador. Motivo: incorporación funcional de M02 al frontend.

2026-11-18 - M03 / CP-06
Se habilita Generación de datos para Analista/Tester e integra GenerationPage.
Motivo: implementar HU-05 / RF08-RF10.

2026-11-20 - M04 / CP-08
Se habilita Resultados y ejecución para Analista/Tester e integra ExecutionPage.
Motivo: registrar resultados externos y clasificarlos sin ejecutar pruebas desde la plataforma.

2026-11-20 - M04 / CP-10
Se conectan los indicadores del Dashboard con datos reales del backend.
Motivo: cerrar HU-10 / RF15 mostrando escenarios y estados de ejecución.

2026-11-20 - M04 / CP-10 - DASHBOARD POR PERFIL
Se diferencia la vista del Administrador de la del Analista/Tester.
Motivo: el Administrador requiere indicadores globales de gestión, mientras
que el Analista/Tester necesita indicadores operativos de sus pruebas.
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

  const [dashboardSummary, setDashboardSummary] = useState(null)
  const [dashboardLoading, setDashboardLoading] = useState(false)
  const [dashboardError, setDashboardError] = useState('')

  const isAdmin =
    user?.rol === 'Administrador'

  useEffect(() => {
    if (activeView === 'dashboard') {
      loadDashboardSummary()
    }
  }, [activeView, isAdmin])

  const modules = isAdmin
    ? ['Gestión de usuarios']
    : analystModules


  async function loadDashboardSummary() {
    setDashboardLoading(true)
    setDashboardError('')

    try {
      const data = await getDashboardSummary()
      setDashboardSummary(data)
    } catch (err) {
      setDashboardError(err.message)
    } finally {
      setDashboardLoading(false)
    }
  }


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

  function goExecution() {
    if (!isAdmin) {
      setActiveView('execution')
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

    if (module === 'Resultados y ejecución') {
      return {
        enabled: true,
        active: activeView === 'execution',
        title: 'Registro y seguimiento de resultados de ejecución externa',
        onClick: goExecution,
      }
    }

    return {
      enabled: false,
      active: false,
      title: 'Funcionalidad no disponible',
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

        ) : activeView === 'execution' && !isAdmin ? (

          <ExecutionPage />

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


            {isAdmin ? (
              <section className="dashboard-summary-section">
                <div className="dashboard-summary-heading">
                  <div>
                    <span className="eyebrow">Resumen administrativo</span>
                    <h2>Estado general de la plataforma</h2>
                    <p>
                      Indicadores globales de usuarios, proyectos, modelos y actividad de pruebas.
                    </p>
                  </div>

                  <button
                    type="button"
                    className="dashboard-refresh-button"
                    onClick={loadDashboardSummary}
                    disabled={dashboardLoading}
                  >
                    {dashboardLoading ? 'Actualizando…' : 'Actualizar indicadores'}
                  </button>
                </div>

                {dashboardError && (
                  <div className="dashboard-metrics-error">
                    {dashboardError}
                  </div>
                )}

                <div className="metric-grid metric-grid-four">
                  <article className="metric-card admin-users">
                    <span>Usuarios registrados</span>
                    <strong>{dashboardLoading && !dashboardSummary ? '…' : dashboardSummary?.total_usuarios ?? 0}</strong>
                    <small>
                      {dashboardSummary?.usuarios_activos ?? 0} activos · {dashboardSummary?.usuarios_inactivos ?? 0} inactivos
                    </small>
                  </article>

                  <article className="metric-card admin-projects">
                    <span>Proyectos</span>
                    <strong>{dashboardLoading && !dashboardSummary ? '…' : dashboardSummary?.total_proyectos ?? 0}</strong>
                    <small>{dashboardSummary?.proyectos_activos ?? 0} proyectos activos</small>
                  </article>

                  <article className="metric-card admin-models">
                    <span>Modelos</span>
                    <strong>{dashboardLoading && !dashboardSummary ? '…' : dashboardSummary?.total_modelos ?? 0}</strong>
                    <small>{dashboardSummary?.modelos_activos ?? 0} modelos activos</small>
                  </article>

                  <article className="metric-card scenarios">
                    <span>Casos generados</span>
                    <strong>{dashboardLoading && !dashboardSummary ? '…' : dashboardSummary?.total_escenarios ?? 0}</strong>
                    <small>{dashboardSummary?.total_generaciones ?? 0} generaciones registradas</small>
                  </article>
                </div>

                <div className="dashboard-subsummary">
                  <div>
                    <span className="eyebrow">Seguimiento global</span>
                    <h3>Estado de las ejecuciones</h3>
                  </div>
                  <p>Se considera únicamente la última ejecución registrada para cada caso.</p>
                </div>

                <div className="metric-grid metric-grid-four">
                  <article className="metric-card approved">
                    <span>Aprobados</span>
                    <strong>{dashboardSummary?.aprobados ?? 0}</strong>
                    <small>Resultado coincide con lo esperado</small>
                  </article>

                  <article className="metric-card failed">
                    <span>Fallidos</span>
                    <strong>{dashboardSummary?.fallidos ?? 0}</strong>
                    <small>Resultado diferente al esperado</small>
                  </article>

                  <article className="metric-card blocked">
                    <span>Bloqueados</span>
                    <strong>{dashboardSummary?.bloqueados ?? 0}</strong>
                    <small>Ejecución externa no completada</small>
                  </article>

                  <article className="metric-card pending">
                    <span>Pendientes</span>
                    <strong>{dashboardSummary?.pendientes ?? 0}</strong>
                    <small>Casos aún sin ejecución registrada</small>
                  </article>
                </div>
              </section>
            ) : (
              <section className="dashboard-summary-section">
                <div className="dashboard-summary-heading">
                  <div>
                    <span className="eyebrow">Resumen de pruebas</span>
                    <h2>Indicadores operativos</h2>
                    <p>
                      Los valores consideran tus generaciones y la última ejecución registrada para cada caso.
                    </p>
                  </div>

                  <button
                    type="button"
                    className="dashboard-refresh-button"
                    onClick={loadDashboardSummary}
                    disabled={dashboardLoading}
                  >
                    {dashboardLoading ? 'Actualizando…' : 'Actualizar indicadores'}
                  </button>
                </div>

                {dashboardError && (
                  <div className="dashboard-metrics-error">
                    {dashboardError}
                  </div>
                )}

                <div className="metric-grid metric-grid-five">
                  <article className="metric-card scenarios">
                    <span>Escenarios generados</span>
                    <strong>{dashboardLoading && !dashboardSummary ? '…' : dashboardSummary?.total_escenarios ?? 0}</strong>
                    <small>
                      {dashboardSummary?.total_generaciones ?? 0} generaciones registradas
                    </small>
                  </article>

                  <article className="metric-card approved">
                    <span>Aprobados</span>
                    <strong>{dashboardLoading && !dashboardSummary ? '…' : dashboardSummary?.aprobados ?? 0}</strong>
                    <small>Resultado observado coincide con lo esperado</small>
                  </article>

                  <article className="metric-card failed">
                    <span>Fallidos</span>
                    <strong>{dashboardLoading && !dashboardSummary ? '…' : dashboardSummary?.fallidos ?? 0}</strong>
                    <small>Resultado observado diferente al esperado</small>
                  </article>

                  <article className="metric-card blocked">
                    <span>Bloqueados</span>
                    <strong>{dashboardLoading && !dashboardSummary ? '…' : dashboardSummary?.bloqueados ?? 0}</strong>
                    <small>No fue posible completar la ejecución externa</small>
                  </article>

                  <article className="metric-card pending">
                    <span>Pendientes</span>
                    <strong>{dashboardLoading && !dashboardSummary ? '…' : dashboardSummary?.pendientes ?? 0}</strong>
                    <small>Aún no poseen una ejecución registrada</small>
                  </article>
                </div>

                {!dashboardLoading && dashboardSummary?.total_escenarios === 0 && (
                  <div className="dashboard-empty-summary">
                    Aún no existen escenarios generados. Los indicadores se actualizarán al crear datos de prueba.
                  </div>
                )}
              </section>
            )}



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
                              : module === 'Resultados y ejecución'
                                ? 'Registra resultados observados y consulta el estado de cada caso.'
                                : 'Funcionalidad no disponible.'}
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

                    {module === 'Resultados y ejecución' && (
                      <button
                        type="button"
                        className="module-link"
                        onClick={goExecution}
                      >
                        Abrir resultados →
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