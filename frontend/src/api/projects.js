/*
2026-11-16
Se agrega cliente API para la gestión de proyectos y modelos.
Permite consultar, crear, modificar y cambiar el estado lógico
de proyectos y modelos asociados.
*/

import { apiFetch } from './client'


// ============================================================
// PROYECTOS
// ============================================================

export function getProjects() {
  return apiFetch('/projects')
}


export function createProject(payload) {
  return apiFetch('/projects', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}


export function updateProject(proyectoId, payload) {
  return apiFetch(`/projects/${proyectoId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}


export function changeProjectStatus(proyectoId, estado) {
  return apiFetch(`/projects/${proyectoId}/estado`, {
    method: 'PATCH',
    body: JSON.stringify({ estado }),
  })
}


// ============================================================
// MODELOS
// ============================================================

export function getProjectModels(proyectoId) {
  return apiFetch(`/projects/${proyectoId}/models`)
}


export function createModel(proyectoId, payload) {
  return apiFetch(`/projects/${proyectoId}/models`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}


export function updateModel(modeloId, payload) {
  return apiFetch(`/projects/models/${modeloId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}


export function changeModelStatus(modeloId, estado) {
  return apiFetch(`/projects/models/${modeloId}/estado`, {
    method: 'PATCH',
    body: JSON.stringify({ estado }),
  })
}