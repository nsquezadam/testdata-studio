from __future__ import annotations

# ============================================================
# CREACIÓN 2026-11-20 - M04 / CP-10
# Esquema de indicadores básicos del Dashboard.
# Motivo: implementar HU-10 / RF15 sin crear tablas adicionales.
# Los indicadores se calculan a partir de generaciones, casos y la última
# ejecución registrada para cada caso de prueba.
#
# MODIFICACIÓN 2026-11-20 - CP-10 / DASHBOARD POR PERFIL
# Se incorpora tipo_dashboard y métricas administrativas opcionales.
# Motivo: diferenciar la vista global del Administrador de la vista operativa
# del Analista/Tester sin duplicar endpoints ni lógica de conteo.
# ============================================================

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    tipo_dashboard: str
    total_generaciones: int
    total_escenarios: int
    ejecuciones_registradas: int
    aprobados: int
    fallidos: int
    bloqueados: int
    pendientes: int

    # Solo se informan para el perfil Administrador.
    total_usuarios: int | None = None
    usuarios_activos: int | None = None
    usuarios_inactivos: int | None = None
    total_proyectos: int | None = None
    proyectos_activos: int | None = None
    total_modelos: int | None = None
    modelos_activos: int | None = None
