from __future__ import annotations

# ============================================================
# CREACIÓN 2026-11-20 - M04 / CP-10
# Endpoint de resumen del Dashboard.
# Motivo: implementar RF15 / HU-10 con información real de la base de datos.
# Cada caso se contabiliza según su última ejecución; si no posee ejecución,
# su estado se considera PENDIENTE.
#
# MODIFICACIÓN 2026-11-20 - CP-10 / DASHBOARD POR PERFIL
# El mismo endpoint adapta su alcance al rol autenticado:
# - Analista/Tester: indicadores operativos de sus propias generaciones/casos.
# - Administrador: indicadores globales de plataforma y resumen de ejecución.
# Motivo: separar responsabilidades sin duplicar endpoints ni componentes.
# ============================================================

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db import get_db
from app.models.execution import Execution
from app.models.generation import Generation, TestCase
from app.models.project import DataModel, Project
from app.models.user import User
from app.schemas.dashboard import DashboardSummary


router = APIRouter(prefix="/dashboard", tags=["Dashboard e indicadores"])


def _execution_counts(db: Session, user_id: int | None = None) -> tuple[int, dict[str, int]]:
    """Cuenta cada caso una sola vez, usando la última ejecución registrada."""

    latest_execution = (
        select(
            Execution.caso_prueba_id.label("caso_prueba_id"),
            func.max(Execution.ejecucion_id).label("ejecucion_id"),
        )
        .group_by(Execution.caso_prueba_id)
        .subquery()
    )

    query = (
        select(TestCase.caso_prueba_id, Execution.estado)
        .join(Generation, Generation.generacion_id == TestCase.generacion_id)
        .outerjoin(
            latest_execution,
            latest_execution.c.caso_prueba_id == TestCase.caso_prueba_id,
        )
        .outerjoin(
            Execution,
            Execution.ejecucion_id == latest_execution.c.ejecucion_id,
        )
    )

    if user_id is not None:
        query = query.where(Generation.usuario_id == user_id)

    rows = db.execute(query).all()

    counts = {
        "APROBADO": 0,
        "FALLIDO": 0,
        "BLOQUEADO": 0,
        "PENDIENTE": 0,
    }

    for _, execution_status in rows:
        status = execution_status or "PENDIENTE"
        counts[status] = counts.get(status, 0) + 1

    return len(rows), counts


@router.get(
    "/summary",
    response_model=DashboardSummary,
    response_model_exclude_none=True,
)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("Administrador", "Analista/Tester")),
):
    role_name = actor.rol.nombre
    is_admin = role_name == "Administrador"

    generation_query = select(func.count(Generation.generacion_id))
    if not is_admin:
        generation_query = generation_query.where(Generation.usuario_id == actor.usuario_id)

    total_generations = db.scalar(generation_query) or 0
    total_scenarios, counts = _execution_counts(
        db,
        user_id=None if is_admin else actor.usuario_id,
    )
    registered = total_scenarios - counts["PENDIENTE"]

    common = dict(
        tipo_dashboard="ADMINISTRATIVO" if is_admin else "OPERATIVO",
        total_generaciones=total_generations,
        total_escenarios=total_scenarios,
        ejecuciones_registradas=registered,
        aprobados=counts["APROBADO"],
        fallidos=counts["FALLIDO"],
        bloqueados=counts["BLOQUEADO"],
        pendientes=counts["PENDIENTE"],
    )

    if not is_admin:
        return DashboardSummary(**common)

    total_users = db.scalar(select(func.count(User.usuario_id))) or 0
    active_users = db.scalar(
        select(func.count(User.usuario_id)).where(User.estado.is_(True))
    ) or 0
    total_projects = db.scalar(select(func.count(Project.proyecto_id))) or 0
    active_projects = db.scalar(
        select(func.count(Project.proyecto_id)).where(Project.estado.is_(True))
    ) or 0
    total_models = db.scalar(select(func.count(DataModel.modelo_id))) or 0
    active_models = db.scalar(
        select(func.count(DataModel.modelo_id)).where(DataModel.estado.is_(True))
    ) or 0

    return DashboardSummary(
        **common,
        total_usuarios=total_users,
        usuarios_activos=active_users,
        usuarios_inactivos=total_users - active_users,
        total_proyectos=total_projects,
        proyectos_activos=active_projects,
        total_modelos=total_models,
        modelos_activos=active_models,
    )
