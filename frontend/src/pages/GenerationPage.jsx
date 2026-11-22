/* ============================================================
   CREACIÓN 2026-11-18 - M03 / CP-06
   Pantalla F03 - Generación de Datos y Escenarios.
   Permite seleccionar proyecto/modelo, cantidad y escenario VALIDO,
   INVALIDO o LIMITE; muestra los casos generados y su trazabilidad.
   Motivo: implementar HU-05 / RF08-RF10.

   MODIFICACIÓN 2026-11-20 - M03 / CP-07 - EXPORTACIÓN
   Se habilitan CSV y JSON para una generación almacenada. Motivo:
   implementar HU-06 / RF11 sin modificar la generación ya aprobada.

   MODIFICACIÓN 2026-11-19 - M03 / CP-06 - TRAZABILIDAD ENRIQUECIDA
   Se muestran campos/roles, valores generados, parámetros y explicación
   de cada regla evaluada. Motivo: permitir corroborar visualmente la
   coherencia regla -> dato -> evaluación durante las pruebas y defensa.
   ============================================================ */

/* ============================================================
   MODIFICACIÓN 2026-11-19 - M03 / CP-06 - AJUSTES UX FRONTEND
   1) Se eliminan del texto visible identificadores internos como M03/RF10.
   2) Al consultar una generación o seleccionar "Ver trazabilidad", la vista
      se desplaza automáticamente al detalle correspondiente.
   3) La trazabilidad se reorganiza a ancho completo, con regla objetivo
      destacada y mayor jerarquía visual para campos, parámetros y resultado.
   Motivo: hacer la lectura más clara para uso operativo y presentación.
   ============================================================ */

import { useEffect, useMemo, useRef, useState } from 'react'

import {
  getProjects,
  getProjectModels,
} from '../api/projects'

import {
  createGeneration,
  getGeneration,
  getGenerationReadiness,
  getGenerations,
  exportGeneration,
} from '../api/generation'


const scenarioOptions = [
  {
    value: 'VALIDO',
    title: 'Válido',
    description: 'Los datos deben cumplir las reglas activas del modelo.',
  },
  {
    value: 'INVALIDO',
    title: 'Inválido',
    description: 'Cada caso incumple intencionalmente una regla objetivo.',
  },
  {
    value: 'LIMITE',
    title: 'Caso límite',
    description: 'Utiliza valores de frontera sin perder coherencia con las demás reglas.',
  },
]


function formatDate(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('es-CL', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value))
}


export default function GenerationPage() {
  const [projects, setProjects] = useState([])
  const [models, setModels] = useState([])
  const [selectedProjectId, setSelectedProjectId] = useState('')
  const [selectedModelId, setSelectedModelId] = useState('')

  const [readiness, setReadiness] = useState(null)
  const [history, setHistory] = useState([])
  const [generation, setGeneration] = useState(null)
  const [selectedCaseId, setSelectedCaseId] = useState(null)

  const [scenario, setScenario] = useState('VALIDO')
  const [quantity, setQuantity] = useState(3)

  const [loading, setLoading] = useState(true)
  const [loadingModel, setLoadingModel] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [loadingGeneration, setLoadingGeneration] = useState(false)
  const [exporting, setExporting] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const resultsRef = useRef(null)
  const traceRef = useRef(null)


  const selectedProject = useMemo(
    () => projects.find(
      (project) => String(project.proyecto_id) === String(selectedProjectId)
    ) || null,
    [projects, selectedProjectId]
  )

  const selectedModel = useMemo(
    () => models.find(
      (model) => String(model.modelo_id) === String(selectedModelId)
    ) || null,
    [models, selectedModelId]
  )

  const selectedCase = useMemo(
    () => generation?.casos?.find(
      (item) => item.caso_prueba_id === selectedCaseId
    ) || generation?.casos?.[0] || null,
    [generation, selectedCaseId]
  )


  useEffect(() => {
    loadProjects()
  }, [])


  async function loadProjects() {
    setLoading(true)
    setError('')

    try {
      const data = await getProjects()
      const activeProjects = data.filter((project) => project.estado)
      setProjects(activeProjects)

      const first = activeProjects[0] || null
      if (first) {
        setSelectedProjectId(String(first.proyecto_id))
        await loadModels(first.proyecto_id)
      } else {
        setModels([])
        setSelectedProjectId('')
        setSelectedModelId('')
      }
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }


  async function loadModels(projectId) {
    setLoadingModel(true)
    setError('')
    setSuccess('')
    setGeneration(null)
    setSelectedCaseId(null)

    try {
      const data = await getProjectModels(projectId)
      const activeModels = data.filter((model) => model.estado)
      setModels(activeModels)

      const first = activeModels[0] || null
      const firstId = first ? String(first.modelo_id) : ''
      setSelectedModelId(firstId)

      if (first) {
        await loadModelContext(first.modelo_id)
      } else {
        setReadiness(null)
        setHistory([])
      }
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoadingModel(false)
    }
  }


  async function loadModelContext(modelId) {
    setLoadingModel(true)
    setError('')
    setSuccess('')
    setGeneration(null)
    setSelectedCaseId(null)

    try {
      const [readinessData, historyData] = await Promise.all([
        getGenerationReadiness(modelId),
        getGenerations(modelId, 10),
      ])
      setReadiness(readinessData)
      setHistory(historyData)
    } catch (requestError) {
      setReadiness(null)
      setHistory([])
      setError(requestError.message)
    } finally {
      setLoadingModel(false)
    }
  }


  async function handleProjectChange(event) {
    const projectId = event.target.value
    setSelectedProjectId(projectId)
    setSelectedModelId('')
    setReadiness(null)
    setHistory([])

    if (projectId) {
      await loadModels(Number(projectId))
    } else {
      setModels([])
    }
  }


  async function handleModelChange(event) {
    const modelId = event.target.value
    setSelectedModelId(modelId)

    if (modelId) {
      await loadModelContext(Number(modelId))
    } else {
      setReadiness(null)
      setHistory([])
      setGeneration(null)
    }
  }


  function scrollToResults() {
    requestAnimationFrame(() => {
      resultsRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      })
    })
  }


  function openTrace(caseId) {
    setSelectedCaseId(caseId)
    requestAnimationFrame(() => {
      traceRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      })
    })
  }


  async function handleGenerate(event) {
    event.preventDefault()
    setError('')
    setSuccess('')

    const modelId = Number(selectedModelId)
    const requested = Number(quantity)

    if (!modelId) {
      setError('Selecciona un modelo antes de generar datos.')
      return
    }

    if (!Number.isInteger(requested) || requested < 1 || requested > 100) {
      setError('La cantidad debe ser un número entero entre 1 y 100.')
      return
    }

    if (!readiness?.listo) {
      setError(
        readiness?.observaciones?.join(' ') ||
        'El modelo no se encuentra listo para generar escenarios.'
      )
      return
    }

    if (scenario === 'LIMITE' && readiness.reglas_limite < 1) {
      setError('El modelo no posee reglas que permitan construir un caso límite.')
      return
    }

    setGenerating(true)

    try {
      const result = await createGeneration({
        modelo_id: modelId,
        cantidad_solicitada: requested,
        tipo_escenario: scenario,
      })

      setGeneration(result)
      setSelectedCaseId(result.casos?.[0]?.caso_prueba_id || null)
      setSuccess(
        `Generación #${result.generacion_id} completada: ${result.casos.length} escenario(s) creado(s).`
      )
      setHistory(await getGenerations(modelId, 10))
      scrollToResults()
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setGenerating(false)
    }
  }


  async function handleExport(format) {
    if (!generation?.generacion_id) {
      setError('Selecciona una generación antes de exportar.')
      return
    }

    setError('')
    setSuccess('')
    setExporting(format)

    try {
      const filename = await exportGeneration(generation.generacion_id, format)
      setSuccess(`Archivo ${format.toUpperCase()} generado correctamente: ${filename}`)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setExporting('')
    }
  }


  async function handleOpenGeneration(generationId) {
    setLoadingGeneration(true)
    setError('')
    setSuccess('')

    try {
      const detail = await getGeneration(generationId)
      setGeneration(detail)
      setSelectedCaseId(detail.casos?.[0]?.caso_prueba_id || null)
      scrollToResults()
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoadingGeneration(false)
    }
  }


  if (loading) {
    return <div className="generation-loading">Cargando módulo de generación...</div>
  }


  return (
    <section className="generation-page">
      <header className="generation-header">
        <div>
          <span className="eyebrow">GENERACIÓN DE DATOS</span>
          <h1>Generación de datos de prueba</h1>
          <p>
            Genera escenarios válidos, inválidos o límite a partir de los campos y
            reglas activas configuradas en el modelo.
          </p>
        </div>
      </header>

      {error && (
        <div className="generation-message error">{error}</div>
      )}

      {success && (
        <div className="generation-message success">{success}</div>
      )}

      <article className="generation-context-card">
        <div className="generation-context-copy">
          <span className="eyebrow">CONTEXTO DE GENERACIÓN</span>
          <h2>Selecciona proyecto y modelo</h2>
          <p>Solo se muestran proyectos y modelos activos.</p>
        </div>

        <div className="generation-selectors">
          <label>
            Proyecto
            <select
              value={selectedProjectId}
              onChange={handleProjectChange}
            >
              {projects.length === 0 && (
                <option value="">Sin proyectos activos</option>
              )}
              {projects.map((project) => (
                <option
                  key={project.proyecto_id}
                  value={project.proyecto_id}
                >
                  {project.nombre}
                </option>
              ))}
            </select>
          </label>

          <label>
            Modelo
            <select
              value={selectedModelId}
              onChange={handleModelChange}
              disabled={!selectedProjectId || loadingModel}
            >
              {models.length === 0 && (
                <option value="">Sin modelos activos</option>
              )}
              {models.map((model) => (
                <option
                  key={model.modelo_id}
                  value={model.modelo_id}
                >
                  {model.nombre}
                </option>
              ))}
            </select>
          </label>
        </div>
      </article>

      <section className="generation-summary">
        <article className="generation-summary-card fields">
          <span>Campos activos</span>
          <strong>{readiness?.campos_activos ?? 0}</strong>
          <small>Datos disponibles para construir cada caso</small>
        </article>

        <article className="generation-summary-card rules">
          <span>Reglas activas</span>
          <strong>{readiness?.reglas_activas ?? 0}</strong>
          <small>Reglas evaluadas durante la generación</small>
        </article>

        <article className="generation-summary-card limits">
          <span>Reglas con límite</span>
          <strong>{readiness?.reglas_limite ?? 0}</strong>
          <small>Disponibles para escenario LIMITE</small>
        </article>

        <article className="generation-summary-card status">
          <span>Estado del modelo</span>
          <strong className="generation-summary-name">
            {readiness?.listo ? 'Listo' : 'Pendiente'}
          </strong>
          <small>
            {readiness?.listo
              ? 'Configuración suficiente para generar'
              : 'Revisa campos y reglas activas'}
          </small>
        </article>
      </section>

      {readiness && !readiness.listo && (
        <div className="generation-readiness-warning">
          <strong>Configuración incompleta:</strong>{' '}
          {readiness.observaciones.join(' ')}
        </div>
      )}

      <article className="generation-form-card">
        <div className="generation-form-heading">
          <div>
            <span className="eyebrow">NUEVA GENERACIÓN</span>
            <h2>Define el escenario a construir</h2>
          </div>
          <div className="generation-model-reference">
            <small>Modelo</small>
            <strong>{selectedModel?.nombre || 'Sin selección'}</strong>
          </div>
        </div>

        <form className="generation-form" onSubmit={handleGenerate}>
          <div className="generation-scenario-options">
            {scenarioOptions.map((option) => (
              <label
                key={option.value}
                className={
                  scenario === option.value
                    ? 'generation-scenario-card active'
                    : 'generation-scenario-card'
                }
              >
                <input
                  type="radio"
                  name="scenario"
                  value={option.value}
                  checked={scenario === option.value}
                  onChange={(event) => setScenario(event.target.value)}
                />
                <span>{option.title}</span>
                <small>{option.description}</small>
              </label>
            ))}
          </div>

          <div className="generation-controls">
            <label>
              Cantidad de registros
              <input
                type="number"
                min="1"
                max="100"
                step="1"
                value={quantity}
                onChange={(event) => setQuantity(event.target.value)}
                required
              />
              <small>Máximo 100 registros por generación.</small>
            </label>

            <button
              type="submit"
              className="primary-button"
              disabled={generating || loadingModel || !readiness?.listo}
            >
              {generating ? 'Generando...' : 'Generar escenarios'}
            </button>
          </div>
        </form>
      </article>

      {generation && (
        <article ref={resultsRef} className="generation-results-card generation-scroll-target">
          <div className="generation-results-heading">
            <div>
              <span className="eyebrow">RESULTADO DE LA GENERACIÓN</span>
              <h2>Generación #{generation.generacion_id}</h2>
              <p>
                {generation.proyecto_nombre} · {generation.modelo_nombre} ·{' '}
                {formatDate(generation.fecha_generacion)}
              </p>
            </div>

            <div className="generation-result-actions">
              <span className="generation-status-badge">{generation.estado}</span>
              <button
                type="button"
                className="secondary-button"
                disabled={Boolean(exporting)}
                onClick={() => handleExport('csv')}
              >
                {exporting === 'csv' ? 'Exportando...' : 'Exportar CSV'}
              </button>
              <button
                type="button"
                className="secondary-button"
                disabled={Boolean(exporting)}
                onClick={() => handleExport('json')}
              >
                {exporting === 'json' ? 'Exportando...' : 'Exportar JSON'}
              </button>
            </div>
          </div>

          <div className="table-responsive">
            <table className="generation-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Escenario</th>
                  <th>Regla objetivo</th>
                  <th>Resultado esperado</th>
                  <th>Datos</th>
                  <th>Acción</th>
                </tr>
              </thead>
              <tbody>
                {generation.casos.map((testCase) => (
                  <tr key={testCase.caso_prueba_id}>
                    <td>{testCase.caso_prueba_id}</td>
                    <td>
                      <span className={`scenario-pill ${testCase.tipo_escenario.toLowerCase()}`}>
                        {testCase.tipo_escenario}
                      </span>
                    </td>
                    <td>{testCase.regla_objetivo_nombre || 'Todas las reglas'}</td>
                    <td>{testCase.resultado_esperado}</td>
                    <td>{testCase.datos.length}</td>
                    <td>
                      <button
                        type="button"
                        className="table-button view"
                        onClick={() => openTrace(testCase.caso_prueba_id)}
                      >
                        Ver trazabilidad
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>
      )}

      {selectedCase && (
        <article
          ref={traceRef}
          className="generation-trace-card generation-scroll-target"
        >
          <div className="generation-trace-heading">
            <div>
              <span className="eyebrow">DETALLE DEL ESCENARIO</span>
              <h2>Trazabilidad del caso #{selectedCase.caso_prueba_id}</h2>
              <p className="generation-trace-subtitle">
                Revisa los datos generados y cómo fue evaluada cada regla de negocio.
              </p>
            </div>
            <div className="generation-trace-summary">
              <span className={`scenario-pill ${selectedCase.tipo_escenario.toLowerCase()}`}>
                {selectedCase.tipo_escenario}
              </span>
              <span className="trace-objective-label">
                <small>Regla objetivo</small>
                <strong>{selectedCase.regla_objetivo_nombre || 'Todas las reglas'}</strong>
              </span>
            </div>
          </div>

          <div className="generation-trace-grid">
            <section>
              <h3>Datos generados</h3>
              <div className="generation-data-list">
                {selectedCase.datos.map((data) => (
                  <div key={data.dato_generado_id} className="generation-data-row">
                    <div>
                      <strong>{data.campo_nombre}</strong>
                      <small>{data.tipo_dato_codigo}</small>
                    </div>
                    <code>{data.valor_generado ?? 'NULL'}</code>
                  </div>
                ))}
              </div>
            </section>

            <section>
              <h3>Reglas evaluadas</h3>
              <div className="generation-rule-list">
                {selectedCase.reglas.map((rule) => (
                  <div
                    key={rule.regla_id}
                    className={
                      `generation-rule-row generation-rule-trace-row${
                        rule.regla_id === selectedCase.regla_objetivo_id
                          ? ' objective'
                          : ''
                      }`
                    }
                  >
                    <div className="generation-rule-trace-header">
                      <div>
                        <strong>{rule.regla_nombre}</strong>
                        <small>{rule.tipo_regla_codigo}</small>
                      </div>
                      <span className={rule.cumple_esperado ? 'trace-ok' : 'trace-fail'}>
                        {rule.cumple_esperado ? 'Cumple' : 'No cumple'}
                      </span>
                    </div>

                    {rule.campos?.length > 0 && (
                      <div className="generation-rule-trace-section">
                        <b>Campos evaluados</b>
                        <div className="generation-rule-trace-chips">
                          {rule.campos.map((field) => (
                            <span
                              key={`${rule.regla_id}-${field.campo_id}-${field.rol_campo}`}
                              className="generation-rule-trace-chip field"
                            >
                              {field.campo_nombre}
                              <small>{field.rol_campo}</small>
                              <code>{field.valor_generado ?? 'NULL'}</code>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {rule.parametros?.length > 0 && (
                      <div className="generation-rule-trace-section">
                        <b>Parámetros configurados</b>
                        <div className="generation-rule-trace-chips">
                          {rule.parametros.map((parameter) => (
                            <span
                              key={parameter.parametro_id}
                              className="generation-rule-trace-chip parameter"
                            >
                              {parameter.clave}
                              <code>{parameter.valor}</code>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <p className="generation-rule-trace-detail">
                      {rule.detalle_esperado || 'Sin detalle adicional.'}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <div className="generation-expected-result">
            <strong>Resultado esperado</strong>
            <p>{selectedCase.resultado_esperado}</p>
          </div>
        </article>
      )}

      <article className="generation-history-card">
        <div className="generation-history-heading">
          <div>
            <span className="eyebrow">HISTORIAL</span>
            <h2>Generaciones recientes del modelo</h2>
          </div>
          {loadingGeneration && <small>Cargando detalle...</small>}
        </div>

        {history.length === 0 ? (
          <div className="generation-empty-state">
            Todavía no existen generaciones para este modelo.
          </div>
        ) : (
          <div className="table-responsive">
            <table className="generation-table">
              <thead>
                <tr>
                  <th>Generación</th>
                  <th>Tipo</th>
                  <th>Casos</th>
                  <th>Estado</th>
                  <th>Fecha</th>
                  <th>Acción</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => (
                  <tr key={item.generacion_id}>
                    <td>#{item.generacion_id}</td>
                    <td>{item.tipo_escenario}</td>
                    <td>{item.total_casos}</td>
                    <td>{item.estado}</td>
                    <td>{formatDate(item.fecha_generacion)}</td>
                    <td>
                      <button
                        type="button"
                        className="table-button view"
                        onClick={() => handleOpenGeneration(item.generacion_id)}
                      >
                        Consultar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </section>
  )
}
