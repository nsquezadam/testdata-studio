import { apiFetch } from './client'

export function getUsers() {
  return apiFetch('/users')
}

export function getRoles() {
  return apiFetch('/users/roles')
}

export function createUser(payload) {
  return apiFetch('/users', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateUser(usuarioId, payload) {
  return apiFetch(`/users/${usuarioId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function updateUserStatus(usuarioId, estado) {
  return apiFetch(`/users/${usuarioId}/estado`, {
    method: 'PATCH',
    body: JSON.stringify({ estado }),
  })
}