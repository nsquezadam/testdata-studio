import { apiFetch } from './client'

/* ============================================================
   CREACIÓN 2026-11-19 - M03 / CP-06
   Cliente REST para Generación de Datos y Escenarios.
   Motivo: implementar HU-05 / RF08-RF10 manteniendo JWT y control
   de sesión centralizados en apiFetch. Exportación queda para CP-07.
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
