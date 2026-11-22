import { apiFetch } from './client'

/* ============================================================
   CREACIÓN 2026-11-20 - M04 / CP-10
   Cliente REST de indicadores del Dashboard.
   Motivo: mostrar valores reales de escenarios y estados de ejecución.
   ============================================================ */

export function getDashboardSummary() {
  return apiFetch('/dashboard/summary')
}
