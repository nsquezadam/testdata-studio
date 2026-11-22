import { useEffect, useMemo, useRef, useState } from 'react'
import {
  createManualExecution,
  getExecutionCase,
  listExecutionCasesPage,
  validateExecutionCsv,
  importExecutionCsv,
} from '../api/execution'
import { getDashboardSummary } from '../api/dashboard'

/* ============================================================
   CREACIÓN 2026-11-20 - M04 / CP-08
   Vista Resultados y ejecución: consulta casos generados, muestra estado
   PENDIENTE y permite registrar manualmente el resultado observado.
   El sistema clasifica APROBADO/FALLIDO y permite BLOQUEADO.

   AJUSTE 2026-11-20 - UX CP-08
   - El formulario se cierra automáticamente después de guardar.
   - Confirmaciones y errores se muestran como avisos temporales.
   - Se incorpora confirmación visual antes de registrar la ejecución.
   - Se mejora la jerarquía visual de los botones Registrar/Revisar.
   Motivo: evitar formularios abiertos después de completar una acción y
   reemplazar confirmaciones poco visibles por una interacción consistente.


   ============================================================ */

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('es-CL')
}

// MODIFICACIÓN 2026-11-22 - M04 / Fecha de último registro
// fecha_registro procede de CURRENT_TIMESTAMP en PostgreSQL/Neon (sesión UTC).
// Es distinta de fecha_ejecucion, que proviene del formulario o del CSV.
// El timestamp de BD es WITHOUT TIME ZONE; se interpreta como UTC al mostrarlo.
function formatLastRegistration(value) {
  if (!value) return '—'
  const raw = String(value).trim()
  const iso = /(?:Z|[+-]\d{2}:\d{2})$/i.test(raw) ? raw : `${raw}Z`
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return raw
  return date.toLocaleString('es-CL', {
    dateStyle: 'short', timeStyle: 'short', timeZone: 'America/Santiago',
  })
}

function localDateTimeValue() {
  const now = new Date()
  const pad = (value) => String(value).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`
}

function statusClass(status) {
  return `execution-status ${String(status || 'PENDIENTE').toLowerCase()}`
}

function emptyForm() {
  return {
    resultado_obtenido: 'Aceptado',
    bloqueado: false,
    observacion: '',
    fecha_ejecucion: localDateTimeValue(),
  }
}

function ConfirmationDialog({ open, selected, form, saving, onCancel, onConfirm }) {
  if (!open || !selected) return null

  return (
    <div className="execution-modal-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget && !saving) onCancel()
    }}>
      <section className="execution-confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="execution-confirm-title">
        <div className="execution-confirm-icon" aria-hidden="true">✓</div>
        <div className="execution-confirm-heading">
          <span className="eyebrow">Confirmar registro</span>
          <h3 id="execution-confirm-title">¿Registrar el resultado del caso #{selected.caso_prueba_id}?</h3>
          <p>Revisa la información antes de guardarla. El estado final será calculado por TestData Studio.</p>
        </div>

        <div className="execution-confirm-summary">
          <div>
            <span>Resultado esperado</span>
            <strong>{selected.resultado_esperado}</strong>
          </div>
          <div>
            <span>Resultado observado</span>
            <strong>{form.bloqueado ? 'Ejecución bloqueada' : form.resultado_obtenido}</strong>
          </div>
          <div>
            <span>Fecha de ejecución</span>
            <strong>{formatDate(form.fecha_ejecucion)}</strong>
          </div>
          {form.observacion && (
            <div className="wide">
              <span>Observación</span>
              <strong>{form.observacion}</strong>
            </div>
          )}
        </div>

        <div className="execution-confirm-actions">
          <button type="button" className="execution-secondary-button" onClick={onCancel} disabled={saving}>
            Volver al formulario
          </button>
          <button type="button" className="execution-confirm-button" onClick={onConfirm} disabled={saving}>
            {saving ? 'Registrando…' : 'Confirmar registro'}
          </button>
        </div>
      </section>
    </div>
  )
}


function ImportConfirmationDialog({ open, preview, saving, onCancel, onConfirm }) {
  if (!open || !preview) return null

  return (
    <div className="execution-modal-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget && !saving) onCancel()
    }}>
      <section className="execution-confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="csv-confirm-title">
        <div className="execution-confirm-icon csv" aria-hidden="true">⇧</div>
        <div className="execution-confirm-heading">
          <span className="eyebrow">Confirmar importación CSV</span>
          <h3 id="csv-confirm-title">¿Importar {preview.filas_validas} fila(s) válida(s)?</h3>
          <p>TestData Studio volverá a validar el archivo antes de guardar y calculará el estado de cada ejecución.</p>
        </div>

        <div className="execution-confirm-summary">
          <div>
            <span>Archivo</span>
            <strong>{preview.archivo_nombre}</strong>
          </div>
          <div>
            <span>Filas válidas</span>
            <strong>{preview.filas_validas}</strong>
          </div>
          <div>
            <span>Filas con error</span>
            <strong>{preview.filas_invalidas}</strong>
          </div>
          {preview.filas_invalidas > 0 && (
            <div className="wide warning">
              <span>Importación parcial</span>
              <strong>Las filas con error serán omitidas y no se guardarán.</strong>
            </div>
          )}
        </div>

        <div className="execution-confirm-actions">
          <button type="button" className="execution-secondary-button" onClick={onCancel} disabled={saving}>
            Volver a la vista previa
          </button>
          <button type="button" className="execution-confirm-button" onClick={onConfirm} disabled={saving}>
            {saving ? 'Importando…' : 'Confirmar importación'}
          </button>
        </div>
      </section>
    </div>
  )
}

export default function ExecutionPage() {
  const [cases, setCases] = useState([])
  const [summary, setSummary] = useState(null)
  const [options, setOptions] = useState([])
  const [page, setPage] = useState(1)
  const [pagination, setPagination] = useState(null)
  const [listError, setListError] = useState('')
  const [summaryError, setSummaryError] = useState('')
  const [refreshVersion, setRefreshVersion] = useState(0)
  const pageSize = 50
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [confirmOpen, setConfirmOpen] = useState(false)

  // CREACIÓN 2026-11-20 - M04 / CP-09
  // Estados de carga, validación previa y confirmación de importación CSV.
  const [importOpen, setImportOpen] = useState(false)
  const [importFile, setImportFile] = useState(null)
  const [importPreview, setImportPreview] = useState(null)
  const [importLoading, setImportLoading] = useState(false)
  const [importSaving, setImportSaving] = useState(false)
  const [importConfirmOpen, setImportConfirmOpen] = useState(false)

  const [projectFilter, setProjectFilter] = useState('')
  const [modelFilter, setModelFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [originFilter, setOriginFilter] = useState('')

  const [form, setForm] = useState(emptyForm)
  const detailRef = useRef(null)
  const importRef = useRef(null)

  // MODIFICACIÓN 2026-11-21 - M04 / CP-08 / CP-10
  // Resumen global del Tester independiente de los filtros/paginación de la tabla.
  // Una recarga tras guardar manualmente o importar CSV refresca ambos bloques.
  useEffect(() => {
    let active = true
    setSummary(null)
    setSummaryError('')
    getDashboardSummary()
      .then((data) => { if (active) setSummary(data) })
      .catch((err) => { if (active) setSummaryError(err.message) })
    return () => { active = false }
  }, [refreshVersion])

  useEffect(() => {
    let active = true
    setLoading(true)
    setListError('')
    setCases([])
    setPagination(null)
    listExecutionCasesPage({
      proyecto_id: projectFilter,
      modelo_id: modelFilter,
      estado: statusFilter,
      origen_registro: originFilter,
      page,
      page_size: pageSize,
    })
      .then((data) => {
        if (!active) return
        setCases(data.items)
        setOptions(data.opciones)
        setPagination(data)
        if (data.page !== page) setPage(data.page)
      })
      .catch((err) => { if (active) setListError(err.message) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [projectFilter, modelFilter, statusFilter, originFilter, page, pageSize, refreshVersion])

  function refreshResults() {
    setRefreshVersion((current) => current + 1)
  }

  async function openCase(caseId, shouldScroll = true) {
    setDetailLoading(true)
    setError('')
    setMessage('')
    setConfirmOpen(false)
    try {
      const data = await getExecutionCase(caseId)
      setSelected(data)
      setForm({
        resultado_obtenido: data.resultado_obtenido || 'Aceptado',
        bloqueado: data.estado === 'BLOQUEADO',
        observacion: data.observacion || '',
        fecha_ejecucion: localDateTimeValue(),
      })
      if (shouldScroll) {
        window.setTimeout(() => {
          detailRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }, 80)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setDetailLoading(false)
    }
  }

  /* AJUSTE 2026-11-20: avisos temporales para no dejar mensajes persistentes. */
  useEffect(() => {
    if (!message) return undefined
    const timer = window.setTimeout(() => setMessage(''), 4200)
    return () => window.clearTimeout(timer)
  }, [message])

  useEffect(() => {
    if (!error) return undefined
    const timer = window.setTimeout(() => setError(''), 6500)
    return () => window.clearTimeout(timer)
  }, [error])

  const projects = useMemo(() => {
    const map = new Map(options.map((item) => [item.proyecto_id, item.proyecto_nombre]))
    return [...map.entries()].map(([id, name]) => ({ id, name }))
  }, [options])

  const models = useMemo(() => {
    const map = new Map(options
      .filter((item) => !projectFilter || String(item.proyecto_id) === projectFilter)
      .map((item) => [item.modelo_id, item.modelo_nombre]))
    return [...map.entries()].map(([id, name]) => ({ id, name }))
  }, [options, projectFilter])

  const metrics = {
    total: summary?.total_escenarios ?? '—',
    pending: summary?.pendientes ?? '—',
    approved: summary?.aprobados ?? '—',
    failed: summary?.fallidos ?? '—',
    blocked: summary?.bloqueados ?? '—',
  }

  function resetImport() {
    if (importLoading || importSaving) return
    setImportOpen(false)
    setImportFile(null)
    setImportPreview(null)
    setImportConfirmOpen(false)
  }

  function openImportPanel() {
    setSelected(null)
    setConfirmOpen(false)
    setImportOpen(true)
    setError('')
    setMessage('')
    window.setTimeout(() => {
      importRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 80)
  }

  function downloadCsvTemplate() {
    const header = 'caso_prueba_id,resultado_obtenido,bloqueado,observacion,fecha_ejecucion\n'
    const blob = new Blob([header], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'plantilla_resultados_testdata.csv'
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  }

  async function validateCsv() {
    if (!importFile) {
      setError('Selecciona un archivo CSV antes de validar.')
      return
    }
    setImportLoading(true)
    setError('')
    setMessage('')
    setImportPreview(null)
    try {
      const preview = await validateExecutionCsv(importFile)
      setImportPreview(preview)
      if (preview.estructura_valida) {
        setMessage(`Archivo validado: ${preview.filas_validas} fila(s) válida(s) y ${preview.filas_invalidas} con observaciones.`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setImportLoading(false)
    }
  }

  async function confirmCsvImport() {
    if (!importFile || !importPreview || importPreview.filas_validas === 0) return
    setImportSaving(true)
    setError('')
    setMessage('')
    try {
      const result = await importExecutionCsv(importFile)
      setImportConfirmOpen(false)
      setImportOpen(false)
      setImportFile(null)
      setImportPreview(null)
      refreshResults()
      setMessage(`Importación completada: ${result.importadas} ejecución(es) registrada(s) desde CSV${result.omitidas ? `; ${result.omitidas} fila(s) omitida(s)` : ''}.`)
    } catch (err) {
      setImportConfirmOpen(false)
      setError(err.message)
    } finally {
      setImportSaving(false)
    }
  }

  function requestExecution(event) {
    event.preventDefault()
    if (!selected) return
    setError('')
    setConfirmOpen(true)
  }

  async function confirmExecution() {
    if (!selected) return

    setSaving(true)
    setError('')
    setMessage('')

    try {
      const payload = {
        resultado_obtenido: form.bloqueado ? null : form.resultado_obtenido,
        bloqueado: form.bloqueado,
        observacion: form.observacion,
        fecha_ejecucion: form.fecha_ejecucion,
      }
      const saved = await createManualExecution(selected.caso_prueba_id, payload)
      const savedCaseId = selected.caso_prueba_id

      /* AJUSTE 2026-11-20: cerrar formulario tras guardar correctamente. */
      setConfirmOpen(false)
      setSelected(null)
      setForm(emptyForm())
      refreshResults()
      setMessage(`Caso #${savedCaseId}: ejecución #${saved.ejecucion_id} registrada correctamente. Estado final: ${saved.estado}.`)
    } catch (err) {
      setConfirmOpen(false)
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  function closeForm() {
    if (saving) return
    setConfirmOpen(false)
    setSelected(null)
    setForm(emptyForm())
  }

  return (
    <div className="execution-page">
      <header className="page-heading execution-page-heading">
        <div>
          <span className="eyebrow">Resultados y ejecución</span>
          <h1>Registro de resultados de prueba</h1>
          <p>
            Registra resultados manualmente o importa múltiples ejecuciones mediante CSV conservando su trazabilidad.
          </p>
        </div>
        <button type="button" className="execution-import-main-button" onClick={openImportPanel}>
          <span aria-hidden="true">⇧</span>
          Importar resultados CSV
        </button>
      </header>

      <div className="execution-toast-stack" aria-live="polite" aria-atomic="true">
        {message && (
          <div className="execution-toast success" role="status">
            <span className="execution-toast-icon">✓</span>
            <div><strong>Registro completado</strong><p>{message}</p></div>
            <button type="button" onClick={() => setMessage('')} aria-label="Cerrar aviso">×</button>
          </div>
        )}
        {error && (
          <div className="execution-toast error" role="alert">
            <span className="execution-toast-icon">!</span>
            <div><strong>No fue posible completar la operación</strong><p>{error}</p></div>
            <button type="button" onClick={() => setError('')} aria-label="Cerrar aviso">×</button>
          </div>
        )}
      </div>


      {importOpen && (
        <section ref={importRef} className="execution-card execution-import-card execution-scroll-target">
          <div className="execution-section-heading execution-import-heading">
            <div>
              <span className="eyebrow">Importación masiva</span>
              <h2>Resultados mediante CSV</h2>
              <p>Valida el archivo antes de guardar. El estado final se calcula automáticamente a partir del resultado esperado.</p>
            </div>
            <button type="button" className="execution-close-detail" onClick={resetImport} aria-label="Cerrar importación">×</button>
          </div>

          <div className="execution-import-schema">
            <div>
              <strong>Estructura requerida</strong>
              <code>caso_prueba_id, resultado_obtenido, bloqueado, observacion, fecha_ejecucion</code>
            </div>
            <button type="button" className="execution-template-button" onClick={downloadCsvTemplate}>
              Descargar plantilla CSV
            </button>
          </div>

          <div className="execution-import-controls">
            <label className="execution-file-picker">
              <span>Archivo CSV</span>
              <input
                type="file"
                accept=".csv,text/csv"
                onChange={(event) => {
                  setImportFile(event.target.files?.[0] || null)
                  setImportPreview(null)
                }}
              />
              <small>{importFile ? importFile.name : 'Selecciona el archivo con los resultados ejecutados externamente.'}</small>
            </label>
            <button type="button" className="execution-validate-button" onClick={validateCsv} disabled={!importFile || importLoading || importSaving}>
              {importLoading ? 'Validando…' : 'Validar archivo'}
            </button>
          </div>

          {importPreview && (
            <div className="execution-import-preview">
              <div className="execution-import-summary">
                <article><span>Total filas</span><strong>{importPreview.total_filas}</strong></article>
                <article className="valid"><span>Válidas</span><strong>{importPreview.filas_validas}</strong></article>
                <article className={importPreview.filas_invalidas ? 'invalid' : ''}><span>Con error</span><strong>{importPreview.filas_invalidas}</strong></article>
              </div>

              {!importPreview.estructura_valida ? (
                <div className="execution-import-general-errors">
                  <strong>La estructura del archivo debe corregirse antes de importar.</strong>
                  {importPreview.errores_generales.map((item) => <p key={item}>{item}</p>)}
                </div>
              ) : (
                <>
                  <div className="execution-table-wrap execution-import-table-wrap">
                    <table className="execution-table execution-import-table">
                      <thead>
                        <tr>
                          <th>Fila</th>
                          <th>Caso</th>
                          <th>Resultado</th>
                          <th>Bloqueado</th>
                          <th>Fecha</th>
                          <th>Estado previsto</th>
                          <th>Validación</th>
                        </tr>
                      </thead>
                      <tbody>
                        {importPreview.filas.map((row) => (
                          <tr key={`${row.fila}-${row.caso_prueba_id || 'x'}`} className={row.valida ? '' : 'execution-import-row-error'}>
                            <td>{row.fila}</td>
                            <td>{row.caso_prueba_id ? `#${row.caso_prueba_id}` : '—'}</td>
                            <td>{row.resultado_obtenido || '—'}</td>
                            <td>{row.bloqueado ? 'Sí' : 'No'}</td>
                            <td>{formatDate(row.fecha_ejecucion)}</td>
                            <td>{row.estado_calculado ? <span className={statusClass(row.estado_calculado)}>{row.estado_calculado}</span> : '—'}</td>
                            <td>
                              {row.valida ? (
                                <span className="execution-import-ok">Lista para importar</span>
                              ) : (
                                <div className="execution-import-errors">{row.errores.map((item) => <span key={item}>{item}</span>)}</div>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="execution-import-actions">
                    <div>
                      {importPreview.filas_invalidas > 0 && <span>Las filas con error serán omitidas.</span>}
                    </div>
                    <button
                      type="button"
                      className="execution-confirm-button"
                      disabled={importPreview.filas_validas === 0 || importSaving}
                      onClick={() => setImportConfirmOpen(true)}
                    >
                      Confirmar importación ({importPreview.filas_validas})
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </section>
      )}

      <div className="execution-summary-caption">
        <span>Resumen de todos tus casos generados (sin aplicar los filtros de la tabla).</span>
        <button type="button" className="execution-secondary-button" onClick={refreshResults} disabled={loading || saving || importSaving}>Actualizar</button>
      </div>
      {summaryError && <p role="alert">No fue posible consultar los indicadores: {summaryError}</p>}
      <section className="execution-metrics">
        <article><span>Casos</span><strong>{metrics.total}</strong><small>Generados y disponibles</small></article>
        <article><span>Pendientes</span><strong>{metrics.pending}</strong><small>Sin ejecución registrada</small></article>
        <article><span>Aprobados</span><strong>{metrics.approved}</strong><small>Esperado = obtenido</small></article>
        <article><span>Fallidos</span><strong>{metrics.failed}</strong><small>Esperado ≠ obtenido</small></article>
        <article><span>Bloqueados</span><strong>{metrics.blocked}</strong><small>No pudieron ejecutarse</small></article>
      </section>

      <section className="execution-card">
        <div className="execution-section-heading">
          <div>
            <span className="eyebrow">Consulta</span>
            <h2>Casos disponibles</h2>
          </div>
        </div>

        <div className="execution-filters">
          <label>
            Proyecto
            <select
              value={projectFilter}
              onChange={(event) => {
                setProjectFilter(event.target.value)
                setModelFilter('')
                setPage(1)
              }}
            >
              <option value="">Todos</option>
              {projects.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </label>

          <label>
            Modelo
            <select value={modelFilter} onChange={(event) => { setModelFilter(event.target.value); setPage(1) }}>
              <option value="">Todos</option>
              {models.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </label>

          <label>
            Estado
            <select value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setPage(1) }}>
              <option value="">Todos</option>
              <option value="PENDIENTE">Pendiente</option>
              <option value="APROBADO">Aprobado</option>
              <option value="FALLIDO">Fallido</option>
              <option value="BLOQUEADO">Bloqueado</option>
            </select>
          </label>

          <label>
            Origen
            <select value={originFilter} onChange={(event) => { setOriginFilter(event.target.value); setPage(1) }}>
              <option value="">Todos</option>
              <option value="MANUAL">Manual</option>
              <option value="CSV">CSV</option>
            </select>
          </label>
        </div>

        {loading ? (
          <div className="generation-loading">Cargando casos…</div>
        ) : listError ? (
          <div className="generation-empty-state" role="alert">No fue posible consultar los casos: {listError}</div>
        ) : cases.length === 0 ? (
          <div className="generation-empty-state">No existen casos para los filtros seleccionados.</div>
        ) : (
          <div className="execution-table-wrap">
            <table className="execution-table">
              <thead>
                <tr>
                  <th>Caso</th>
                  <th>Proyecto / Modelo</th>
                  <th>Escenario</th>
                  <th>Esperado</th>
                  <th>Obtenido</th>
                  <th>Estado</th>
                  <th>Origen</th>
                  <th>Fechas</th>
                  <th>Acción</th>
                </tr>
              </thead>
              <tbody>
                {cases.map((item) => (
                  <tr key={item.caso_prueba_id}>
                    <td><strong>#{item.caso_prueba_id}</strong></td>
                    <td><strong>{item.proyecto_nombre}</strong><small>{item.modelo_nombre}</small></td>
                    <td>{item.tipo_escenario}</td>
                    <td className="execution-long-cell">{item.resultado_esperado}</td>
                    <td>{item.resultado_obtenido || '—'}</td>
                    <td><span className={statusClass(item.estado)}>{item.estado}</span></td>
                    <td>{item.origen_registro || '—'}</td>
                    <td className="execution-date-cell">
                      {item.fecha_registro ? (
                        <>
                          <strong>Último registro: {formatLastRegistration(item.fecha_registro)}</strong>
                          <small>Fecha ejecución: {formatDate(item.fecha_ejecucion)}</small>
                        </>
                      ) : '—'}
                    </td>
                    <td>
                      <button
                        type="button"
                        className={`execution-action-button ${item.estado === 'PENDIENTE' ? 'register' : 'review'}`}
                        onClick={() => openCase(item.caso_prueba_id)}
                      >
                        <span className="execution-action-symbol" aria-hidden="true">{item.estado === 'PENDIENTE' ? '+' : '→'}</span>
                        <span>{item.estado === 'PENDIENTE' ? 'Registrar' : 'Revisar'}</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {!loading && !listError && pagination && (
          <div className="execution-pagination" aria-label="Paginación de casos">
            <span aria-live="polite">
              {pagination.total === 0 ? '0 casos' : `Mostrando ${(pagination.page - 1) * pagination.page_size + 1}–${(pagination.page - 1) * pagination.page_size + cases.length} de ${pagination.total} casos`}
            </span>
            <div className="execution-pagination-actions">
              <button type="button" className="execution-secondary-button" disabled={pagination.page <= 1} onClick={() => setPage(pagination.page - 1)}>Anterior</button>
              <span>Página {pagination.page} de {Math.max(1, pagination.total_pages)}</span>
              <button type="button" className="execution-secondary-button" disabled={pagination.page >= pagination.total_pages} onClick={() => setPage(pagination.page + 1)}>Siguiente</button>
            </div>
          </div>
        )}
      </section>

      {(selected || detailLoading) && (
        <section ref={detailRef} className="execution-card execution-scroll-target">
          {detailLoading && !selected ? (
            <div className="generation-loading">Cargando detalle…</div>
          ) : selected && (
            <>
              <div className="execution-section-heading execution-detail-heading">
                <div>
                  <span className="eyebrow">Detalle del caso</span>
                  <h2>Caso #{selected.caso_prueba_id}</h2>
                  <p>{selected.proyecto_nombre} · {selected.modelo_nombre} · Generación #{selected.generacion_id}</p>
                </div>
                <div className="execution-detail-heading-actions">
                  <span className={statusClass(selected.estado)}>{selected.estado}</span>
                  <button type="button" className="execution-close-detail" onClick={closeForm} aria-label="Cerrar formulario">×</button>
                </div>
              </div>

              <div className="execution-detail-grid">
                <div>
                  <h3>Datos utilizados</h3>
                  <div className="execution-data-grid">
                    {selected.datos.map((item) => (
                      <div className="execution-data-item" key={item.campo_id}>
                        <div><strong>{item.campo_nombre}</strong><small>{item.tipo_dato_codigo}</small></div>
                        <code>{item.valor_generado ?? 'NULL'}</code>
                      </div>
                    ))}
                  </div>

                  <div className="execution-expected-box">
                    <span>Resultado esperado</span>
                    <strong>{selected.resultado_esperado}</strong>
                  </div>
                </div>

                <form className="execution-form" onSubmit={requestExecution}>
                  <div>
                    <span className="eyebrow">Registro manual</span>
                    <h3>Resultado observado</h3>
                    <p>La clasificación se calcula automáticamente al guardar.</p>
                  </div>

                  <label className="execution-block-toggle">
                    <input
                      type="checkbox"
                      checked={form.bloqueado}
                      onChange={(event) => setForm((current) => ({ ...current, bloqueado: event.target.checked }))}
                    />
                    La ejecución externa no pudo completarse (Bloqueado)
                  </label>

                  {!form.bloqueado && (
                    <label>
                      Resultado obtenido
                      <select
                        value={form.resultado_obtenido}
                        onChange={(event) => setForm((current) => ({ ...current, resultado_obtenido: event.target.value }))}
                        required
                      >
                        <option value="Aceptado">Aceptado</option>
                        <option value="Rechazado">Rechazado</option>
                      </select>
                    </label>
                  )}

                  <label>
                    Fecha de ejecución
                    <input
                      type="datetime-local"
                      value={form.fecha_ejecucion}
                      onChange={(event) => setForm((current) => ({ ...current, fecha_ejecucion: event.target.value }))}
                      required
                    />
                  </label>

                  <label>
                    Observación {form.bloqueado ? '*' : '(opcional)'}
                    <textarea
                      rows="4"
                      value={form.observacion}
                      onChange={(event) => setForm((current) => ({ ...current, observacion: event.target.value }))}
                      required={form.bloqueado}
                      placeholder={form.bloqueado ? 'Indica por qué no fue posible ejecutar la prueba.' : 'Agrega contexto de la ejecución si corresponde.'}
                    />
                  </label>

                  <div className="execution-form-actions">
                    <button type="button" className="execution-secondary-button" onClick={closeForm} disabled={saving}>
                      Cancelar
                    </button>
                    <button type="submit" className="execution-save-button" disabled={saving}>
                      <span aria-hidden="true">✓</span>
                      <span>{saving ? 'Guardando…' : 'Registrar ejecución'}</span>
                    </button>
                  </div>

                  {selected.ejecucion_id && (
                    <div className="execution-last-result">
                      <strong>Última ejecución registrada</strong>
                      <span>#{selected.ejecucion_id} · {selected.origen_registro}</span>
                      <span>Último registro: {formatLastRegistration(selected.fecha_registro)}</span>
                      <span>Fecha de ejecución: {formatDate(selected.fecha_ejecucion)}</span>
                      <span>Resultado: {selected.resultado_obtenido || '—'}</span>
                    </div>
                  )}
                </form>
              </div>
            </>
          )}
        </section>
      )}

      <ConfirmationDialog
        open={confirmOpen}
        selected={selected}
        form={form}
        saving={saving}
        onCancel={() => !saving && setConfirmOpen(false)}
        onConfirm={confirmExecution}
      />

      <ImportConfirmationDialog
        open={importConfirmOpen}
        preview={importPreview}
        saving={importSaving}
        onCancel={() => !importSaving && setImportConfirmOpen(false)}
        onConfirm={confirmCsvImport}
      />
    </div>
  )
}
