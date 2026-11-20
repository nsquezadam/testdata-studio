import { apiFetch } from './client'

/*
2026-11-18 - M02 / INC-02 / INC-03
Cliente API para Campos y reglas.
Se mantienen las rutas relativas a VITE_API_URL (que ya contiene /api).
Motivo: centralizar las llamadas de M02 y conservar JWT/manejo de sesión
mediante apiFetch. No se duplica la validación de negocio del backend.
INC-03: los catálogos deben exponer tipo_dato_id y tipo_regla_id; la página
normaliza también el formato transitorio id para compatibilidad.
*/

// ============================================================
// CATÁLOGOS
// ============================================================

export function getDataTypes() {
  return apiFetch('/data-types')
}

export function getRuleTypes() {
  return apiFetch('/rule-types')
}


// ============================================================
// CAMPOS
// ============================================================

export function getFieldsByModel(modeloId) {
  return apiFetch(`/models/${modeloId}/fields`)
}

export function createField(modeloId, payload) {
  return apiFetch(`/models/${modeloId}/fields`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateField(campoId, payload) {
  return apiFetch(`/fields/${campoId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function changeFieldStatus(campoId, estado) {
  return apiFetch(`/fields/${campoId}/estado`, {
    method: 'PATCH',
    body: JSON.stringify({ estado }),
  })
}


// ============================================================
// REGLAS
// ============================================================

export function getRulesByModel(modeloId) {
  return apiFetch(`/models/${modeloId}/rules`)
}

export function createRule(modeloId, payload) {
  return apiFetch(`/models/${modeloId}/rules`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateRule(reglaId, payload) {
  return apiFetch(`/rules/${reglaId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function changeRuleStatus(reglaId, estado) {
  return apiFetch(`/rules/${reglaId}/estado`, {
    method: 'PATCH',
    body: JSON.stringify({ estado }),
  })
}
