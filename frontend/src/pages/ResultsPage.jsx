/* ============================================================
   CREACIÓN 2026-11-20 - M04 / CP-08
   Pantalla de Resultados y ejecución.
   Permite consultar casos generados, visualizar el resultado esperado,
   registrar manualmente el resultado observado y obtener la clasificación
   APROBADO/FALLIDO/BLOQUEADO. Los casos sin ejecución se muestran PENDIENTE.
   ============================================================ */

import { useEffect, useMemo, useRef, useState } from 'react'
import { getProjects, getProjectModels } from '../api/projects'
import { createManualExecution, getExecutionCase, getExecutionCases } from '../api/execution'

const stateOptions = [
  { value: '', label: 'Todos' },
  { value: 'PENDIENTE', label: 'Pendiente' },
  { value: 'APROBADO', label: 'Aprobado' },
  { value: 'FALLIDO', label: 'Fallido' },
  { value: 'BLOQUEADO', label: 'Bloqueado' },
]

function formatDate(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('es-CL', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value))
}

function toLocalInputValue(date = new Date()) {
  const copy = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return copy.toISOString().slice(0, 16)
}

export default function ResultsPage() {
  const [projects, setProjects] = useState([])
  const [models, setModels] = useState([])
  const [selectedProjectId, setSelectedProjectId] = useState('')
  const [selectedModelId, setSelectedModelId] = useState('')
  const [stateFilter, setStateFilter] = useState('')
  const [cases, setCases] = useState([])
  const [selectedCase, setSelectedCase] = useState(null)
  const [result, setResult] = useState('')
  const [observation, setObservation] = useState('')
  const [executionDate, setExecutionDate] = useState(toLocalInputValue())
  const [blocked, setBlocked] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const formRef = useRef(null)

  const counts = useMemo(() => {
    const base = { PENDIENTE: 0, APROBADO: 0, FALLIDO: 0, BLOQUEADO: 0 }
    cases.forEach((item) => { base[item.estado] = (base[item.estado] || 0) + 1 })
    return base
  }, [cases])

  useEffect(() => { loadProjects() }, [])

  async function loadProjects() {
    setLoading(true); setError('')
    try {
      const data = (await getProjects()).filter((item) => item.estado)
      setProjects(data)
      const first = data[0]
      if (first) {
        setSelectedProjectId(String(first.proyecto_id))
        await loadModels(first.proyecto_id)
      } else {
        setModels([]); setCases([])
      }
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  async function loadModels(projectId) {
    setError(''); setSuccess(''); setSelectedCase(null)
    try {
      const data = (await getProjectModels(projectId)).filter((item) => item.estado)
      setModels(data)
      const first = data[0]
      const id = first ? String(first.modelo_id) : ''
      setSelectedModelId(id)
      if (first) await loadCases(first.modelo_id, stateFilter)
      else setCases([])
    } catch (err) { setError(err.message) }
  }

  async function loadCases(modelId = selectedModelId, filter = stateFilter) {
    if (!modelId) { setCases([]); return }
    try {
      const data = await getExecutionCases(Number(modelId), filter)
      setCases(data)
    } catch (err) { setError(err.message) }
  }

  async function handleProjectChange(event) {
    const id = event.target.value
    setSelectedProjectId(id); setSelectedModelId(''); setCases([]); setSelectedCase(null)
    if (id) await loadModels(Number(id))
  }

  async function handleModelChange(event) {
    const id = event.target.value
    setSelectedModelId(id); setSelectedCase(null)
    await loadCases(id, stateFilter)
  }

  async function handleStateChange(event) {
    const value = event.target.value
    setStateFilter(value)
    await loadCases(selectedModelId, value)
  }

  async function openCase(caseId) {
    setError(''); setSuccess('')
    try {
      const detail = await getExecutionCase(caseId)
      setSelectedCase(detail)
      setResult(detail.ultima_ejecucion?.resultado_obtenido || '')
      setObservation(detail.ultima_ejecucion?.observacion || '')
      setExecutionDate(detail.ultima_ejecucion?.fecha_ejecucion
        ? toLocalInputValue(new Date(detail.ultima_ejecucion.fecha_ejecucion))
        : toLocalInputValue())
      setBlocked(detail.estado === 'BLOQUEADO')
      requestAnimationFrame(() => formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
    } catch (err) { setError(err.message) }
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!selectedCase) return
    if (!blocked && !result.trim()) {
      setError('Ingresa el resultado obtenido o marca la ejecución como bloqueada.')
      return
    }
    setSaving(true); setError(''); setSuccess('')
    try {
      const updated = await createManualExecution(selectedCase.caso_prueba_id, {
        resultado_obtenido: blocked ? null : result.trim(),
        observacion: observation.trim() || null,
        fecha_ejecucion: executionDate ? new Date(executionDate).toISOString() : null,
        bloqueado: blocked,
      })
      setSelectedCase(updated)
      setSuccess(`Resultado registrado. Estado final: ${updated.estado}.`)
      await loadCases(selectedModelId, stateFilter)
    } catch (err) { setError(err.message) }
    finally { setSaving(false) }
  }

  if (loading) return <div className="generation-loading">Cargando resultados...</div>

  return (
    <section className="generation-page execution-page">
      <header className="generation-header">
        <div>
          <span className="eyebrow">RESULTADOS Y EJECUCIÓN</span>
          <h1>Resultados de pruebas</h1>
          <p>Registra el resultado observado después de utilizar los datos en un sistema externo y consulta su clasificación.</p>
        </div>
      </header>

      {error && <div className="generation-message error">{error}</div>}
      {success && <div className="generation-message success">{success}</div>}

      <article className="generation-context-card">
        <div className="generation-context-copy">
          <span className="eyebrow">CONTEXTO DE EJECUCIÓN</span>
          <h2>Selecciona proyecto y modelo</h2>
          <p>Los casos provienen de generaciones ya almacenadas.</p>
        </div>
        <div className="generation-selectors execution-selectors">
          <label>Proyecto
            <select value={selectedProjectId} onChange={handleProjectChange}>
              {projects.map((p) => <option key={p.proyecto_id} value={p.proyecto_id}>{p.nombre}</option>)}
            </select>
          </label>
          <label>Modelo
            <select value={selectedModelId} onChange={handleModelChange}>
              {models.map((m) => <option key={m.modelo_id} value={m.modelo_id}>{m.nombre}</option>)}
            </select>
          </label>
          <label>Estado
            <select value={stateFilter} onChange={handleStateChange}>
              {stateOptions.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </label>
        </div>
      </article>

      <section className="generation-summary execution-summary">
        <article className="generation-summary-card status"><span>Pendientes</span><strong>{counts.PENDIENTE}</strong><small>Sin ejecución registrada</small></article>
        <article className="generation-summary-card rules"><span>Aprobados</span><strong>{counts.APROBADO}</strong><small>Esperado y obtenido coinciden</small></article>
        <article className="generation-summary-card limits"><span>Fallidos</span><strong>{counts.FALLIDO}</strong><small>Resultado diferente al esperado</small></article>
        <article className="generation-summary-card fields"><span>Bloqueados</span><strong>{counts.BLOQUEADO}</strong><small>No fue posible completar la ejecución externa</small></article>
      </section>

      <article className="generation-results-card">
        <div className="generation-results-heading">
          <div><span className="eyebrow">CASOS DISPONIBLES</span><h2>Escenarios generados</h2><p>Selecciona un caso para registrar o revisar su ejecución.</p></div>
        </div>
        {cases.length === 0 ? <div className="generation-empty-state">No existen casos para los filtros seleccionados.</div> : (
          <div className="table-responsive">
            <table className="generation-table execution-table">
              <thead><tr><th>Caso</th><th>Generación</th><th>Escenario</th><th>Resultado esperado</th><th>Estado</th><th>Origen</th><th>Fecha</th><th>Acción</th></tr></thead>
              <tbody>{cases.map((item) => (
                <tr key={item.caso_prueba_id}>
                  <td>#{item.caso_prueba_id}</td><td>#{item.generacion_id}</td>
                  <td><span className={`scenario-pill ${item.tipo_escenario.toLowerCase()}`}>{item.tipo_escenario}</span></td>
                  <td>{item.resultado_esperado}</td>
                  <td><span className={`execution-state ${item.estado.toLowerCase()}`}>{item.estado}</span></td>
                  <td>{item.ultima_ejecucion?.origen_registro || '—'}</td>
                  <td>{formatDate(item.ultima_ejecucion?.fecha_ejecucion)}</td>
                  <td><button type="button" className="table-button view" onClick={() => openCase(item.caso_prueba_id)}>{item.estado === 'PENDIENTE' ? 'Registrar resultado' : 'Consultar / registrar'}</button></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </article>

      {selectedCase && (
        <article ref={formRef} className="generation-trace-card generation-scroll-target execution-detail-card">
          <div className="generation-trace-heading">
            <div><span className="eyebrow">REGISTRO MANUAL</span><h2>Caso #{selectedCase.caso_prueba_id}</h2><p className="generation-trace-subtitle">La prueba se ejecuta fuera de TestData Studio; aquí se registra el resultado observado.</p></div>
            <span className={`execution-state ${selectedCase.estado.toLowerCase()}`}>{selectedCase.estado}</span>
          </div>

          <div className="execution-context-grid">
            <section>
              <h3>Resultado esperado</h3>
              <div className="execution-expected-box">{selectedCase.resultado_esperado}</div>
              <h3>Datos utilizados</h3>
              <div className="generation-data-list">
                {selectedCase.datos.map((d) => <div key={d.campo_id} className="generation-data-row"><div><strong>{d.campo_nombre}</strong><small>{d.tipo_dato_codigo}</small></div><code>{d.valor_generado ?? 'NULL'}</code></div>)}
              </div>
            </section>

            <form className="execution-form" onSubmit={handleSubmit}>
              <label className="execution-blocked-option"><input type="checkbox" checked={blocked} onChange={(e) => setBlocked(e.target.checked)} /> La ejecución externa quedó bloqueada</label>
              <label>Resultado obtenido
                <textarea rows="4" value={result} onChange={(e) => setResult(e.target.value)} disabled={blocked} placeholder="Ej.: Aceptado, Rechazado o el resultado textual observado" />
                <small>El sistema compara el significado Aceptar/Rechazar cuando corresponde.</small>
              </label>
              <label>Observación
                <textarea rows="3" value={observation} onChange={(e) => setObservation(e.target.value)} placeholder="Contexto adicional de la ejecución" />
              </label>
              <label>Fecha de ejecución
                <input type="datetime-local" value={executionDate} onChange={(e) => setExecutionDate(e.target.value)} />
              </label>
              <button type="submit" className="primary-button" disabled={saving}>{saving ? 'Guardando...' : 'Guardar resultado'}</button>
            </form>
          </div>

          {selectedCase.ultima_ejecucion && (
            <div className="execution-last-result">
              <strong>Última ejecución registrada</strong>
              <span>Origen: {selectedCase.ultima_ejecucion.origen_registro}</span>
              <span>Resultado: {selectedCase.ultima_ejecucion.resultado_obtenido || 'Sin resultado'}</span>
              <span>Estado: {selectedCase.ultima_ejecucion.estado}</span>
              <span>Fecha: {formatDate(selectedCase.ultima_ejecucion.fecha_ejecucion)}</span>
              {selectedCase.ultima_ejecucion.observacion && <p>{selectedCase.ultima_ejecucion.observacion}</p>}
            </div>
          )}
        </article>
      )}
    </section>
  )
}
