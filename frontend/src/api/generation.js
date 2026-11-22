import { apiDownload, apiFetch } from './client'

/* ============================================================
   CREACIÓN 2026-11-18 - M03 / CP-06
   Cliente REST para Generación de Datos y Escenarios.
   Motivo: implementar HU-05 / RF08-RF10 manteniendo JWT y control
   de sesión centralizados en apiFetch.

   MODIFICACIÓN 2026-11-20 - M03 / CP-07
   Se habilitan descargas CSV/JSON protegidas por JWT para HU-06 / RF11.

   AJUSTE 2026-11-20 - CP-07 V3
   El nombre del archivo se construye también en frontend usando el ID de generación
   para evitar nombres genéricos cuando el navegador no expone Content-Disposition.
   ============================================================ */

export function getGenerationReadiness(modeloId) {
  return apiFetch(`/models/${modeloId}/generation-readiness`)
}

export function createGeneration(payload) {
  return apiFetch('/generations', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getGenerations(modeloId = null, limit = 10) {
  const params = new URLSearchParams()
  if (modeloId) {
    params.set('modelo_id', String(modeloId))
  }
  params.set('limit', String(limit))
  return apiFetch(`/generations?${params.toString()}`)
}

export function getGeneration(generacionId) {
  return apiFetch(`/generations/${generacionId}`)
}

export function exportGeneration(generacionId, format) {
  const normalized = String(format).toLowerCase()
  if (!['csv', 'json'].includes(normalized)) {
    throw new Error('Formato de exportación no soportado.')
  }
  const filename = `testdata_generacion_${generacionId}.${normalized}`
  return apiDownload(`/generations/${generacionId}/export/${normalized}`, filename)
}
