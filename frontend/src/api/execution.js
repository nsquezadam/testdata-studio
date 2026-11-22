import { apiFetch } from './client'

/* ============================================================
   CREACIÓN 2026-11-20 - M04 / CP-08
   Cliente REST para consulta de casos y registro manual de resultados.
   Motivo: implementar HU-07 / RF12 desde la interfaz del Analista/Tester.
   ============================================================ */

export function listExecutionCases() {
  return apiFetch('/execution-cases')
}

// MODIFICACIÓN 2026-11-21 - M04: consulta paginada y filtros en servidor.
export function listExecutionCasesPage(filters = {}) {
  const query = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== '' && value != null) query.set(key, String(value))
  })
  return apiFetch(`/execution-cases/page?${query.toString()}`)
}

export function getExecutionCase(caseId) {
  return apiFetch(`/execution-cases/${caseId}`)
}

export function createManualExecution(caseId, payload) {
  return apiFetch(`/execution-cases/${caseId}/executions`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/* ============================================================
   CREACIÓN 2026-11-20 - M04 / CP-09
   Validación previa e importación de resultados mediante CSV.
   El mismo archivo se revalida en backend al confirmar la importación.
   ============================================================ */
export function validateExecutionCsv(file) {
  const formData = new FormData()
  formData.append('file', file)
  return apiFetch('/execution-imports/csv/validate', {
    method: 'POST',
    body: formData,
  })
}

export function importExecutionCsv(file) {
  const formData = new FormData()
  formData.append('file', file)
  return apiFetch('/execution-imports/csv/import', {
    method: 'POST',
    body: formData,
  })
}
