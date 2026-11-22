from __future__ import annotations

# ============================================================
# CREACIÓN 2026-11-20 - M04 / CP-08
# Endpoints para consultar casos pendientes/ejecutados y registrar manualmente
# el resultado observado en un sistema externo.
# Motivo: implementar HU-07 / RF12 y la clasificación esperada/obtenida de RF14.
# ============================================================

import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db import get_db
from app.models.configuration import DataField, DataType
from app.models.execution import Execution
from app.models.generation import GeneratedData, Generation, TestCase
from app.models.project import DataModel, Project
from app.models.user import User
from app.schemas.execution import (
    ExecutionCaseDetail,
    ExecutionCaseListItem,
    ExecutionCasePage,
    ExecutionFilterOption,
    ExecutionCreate,
    ExecutionDataItem,
    ExecutionResponse,
)


router = APIRouter(tags=["Resultados y ejecución"])


def _normalize_semantic_result(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = re.sub(r"\s+", " ", normalized.strip().lower())

    accepted = ("aceptar", "aceptado", "aceptada", "aprobado", "aprobada", "ok", "exito", "exitoso")
    rejected = ("rechazar", "rechazado", "rechazada", "denegado", "denegada", "error")
    if normalized.startswith(accepted):
        return "ACEPTAR"
    if normalized.startswith(rejected):
        return "RECHAZAR"
    return normalized


def _classify(expected: str, observed: str | None, blocked: bool) -> str:
    if blocked:
        return "BLOQUEADO"
    expected_value = _normalize_semantic_result(expected)
    observed_value = _normalize_semantic_result(observed)
    return "APROBADO" if expected_value == observed_value else "FALLIDO"


def _latest_execution_subquery(db: Session, case_id: int) -> Execution | None:
    return db.scalar(
        select(Execution)
        .where(Execution.caso_prueba_id == case_id)
        .order_by(Execution.ejecucion_id.desc())
        .limit(1)
    )


def _owned_case_context(db: Session, case_id: int, analyst: User):
    row = db.execute(
        select(TestCase, Generation, DataModel, Project)
        .join(Generation, Generation.generacion_id == TestCase.generacion_id)
        .join(DataModel, DataModel.modelo_id == Generation.modelo_id)
        .join(Project, Project.proyecto_id == DataModel.proyecto_id)
        .where(TestCase.caso_prueba_id == case_id)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Caso de prueba no encontrado.")
    case, generation, model, project = row
    if generation.usuario_id != analyst.usuario_id:
        raise HTTPException(status_code=403, detail="No posee permisos para consultar este caso.")
    return case, generation, model, project


def _to_list_item(case, generation, model, project, latest: Execution | None):
    return ExecutionCaseListItem(
        caso_prueba_id=case.caso_prueba_id,
        generacion_id=generation.generacion_id,
        proyecto_id=project.proyecto_id,
        proyecto_nombre=project.nombre,
        modelo_id=model.modelo_id,
        modelo_nombre=model.nombre,
        tipo_escenario=case.tipo_escenario,
        resultado_esperado=case.resultado_esperado,
        estado=latest.estado if latest else "PENDIENTE",
        origen_registro=latest.origen_registro if latest else None,
        resultado_obtenido=latest.resultado_obtenido if latest else None,
        fecha_ejecucion=latest.fecha_ejecucion if latest else None,
        fecha_registro=latest.fecha_registro if latest else None,
        ejecucion_id=latest.ejecucion_id if latest else None,
    )


# MODIFICACIÓN 2026-11-21 - M04 / CP-08 / CP-10
# Filtra por la última ejecución ANTES de paginar; mantiene el alcance por usuario.
# El LEFT JOIN conserva los casos pendientes y evita una consulta por cada caso.
def _execution_case_query(user_id: int):
    latest = (
        select(
            Execution.caso_prueba_id,
            func.max(Execution.ejecucion_id).label("ejecucion_id"),
        )
        .group_by(Execution.caso_prueba_id)
        .subquery()
    )
    return (
        select(TestCase, Generation, DataModel, Project, Execution)
        .join(Generation, Generation.generacion_id == TestCase.generacion_id)
        .join(DataModel, DataModel.modelo_id == Generation.modelo_id)
        .join(Project, Project.proyecto_id == DataModel.proyecto_id)
        .outerjoin(latest, latest.c.caso_prueba_id == TestCase.caso_prueba_id)
        .outerjoin(Execution, Execution.ejecucion_id == latest.c.ejecucion_id)
        .where(Generation.usuario_id == user_id)
    )


def _apply_execution_filters(statement, proyecto_id, modelo_id, estado, origen_registro):
    if proyecto_id is not None:
        statement = statement.where(Project.proyecto_id == proyecto_id)
    if modelo_id is not None:
        statement = statement.where(Generation.modelo_id == modelo_id)
    if estado:
        requested_status = estado.upper()
        if requested_status not in {"PENDIENTE", "APROBADO", "FALLIDO", "BLOQUEADO"}:
            raise HTTPException(status_code=422, detail="Estado de ejecución no válido.")
        statement = statement.where(func.coalesce(Execution.estado, "PENDIENTE") == requested_status)
    if origen_registro:
        origin = origen_registro.upper()
        if origin not in {"MANUAL", "CSV"}:
            raise HTTPException(status_code=422, detail="Origen de registro no válido.")
        statement = statement.where(Execution.origen_registro == origin)
    return statement


@router.get("/execution-cases", response_model=list[ExecutionCaseListItem])
def list_execution_cases(
    modelo_id: int | None = Query(default=None, gt=0),
    estado: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    analyst: User = Depends(require_roles("Analista/Tester")),
):
    # Se conserva el contrato anterior (lista) para compatibilidad.
    statement = _apply_execution_filters(
        _execution_case_query(analyst.usuario_id), None, modelo_id, estado, None
    )
    rows = db.execute(statement.order_by(TestCase.caso_prueba_id.desc()).limit(limit)).all()
    return [_to_list_item(*row) for row in rows]


# Debe declararse antes de /execution-cases/{caso_prueba_id}.
@router.get("/execution-cases/page", response_model=ExecutionCasePage)
def list_execution_cases_page(
    proyecto_id: int | None = Query(default=None, gt=0),
    modelo_id: int | None = Query(default=None, gt=0),
    estado: str | None = Query(default=None),
    origen_registro: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    analyst: User = Depends(require_roles("Analista/Tester")),
):
    statement = _apply_execution_filters(
        _execution_case_query(analyst.usuario_id), proyecto_id, modelo_id, estado, origen_registro
    )
    total = db.scalar(select(func.count()).select_from(statement.with_only_columns(TestCase.caso_prueba_id).subquery())) or 0
    total_pages = (total + page_size - 1) // page_size
    # Si un registro cambia de estado y desaparece de la última página,
    # se devuelve la última página disponible en lugar de una página vacía.
    page = min(page, max(1, total_pages))
    rows = db.execute(
        statement.order_by(TestCase.caso_prueba_id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    # Las opciones se obtienen del universo del usuario, no de una página filtrada.
    options = db.execute(
        select(Project.proyecto_id, Project.nombre, DataModel.modelo_id, DataModel.nombre)
        .select_from(TestCase)
        .join(Generation, Generation.generacion_id == TestCase.generacion_id)
        .join(DataModel, DataModel.modelo_id == Generation.modelo_id)
        .join(Project, Project.proyecto_id == DataModel.proyecto_id)
        .where(Generation.usuario_id == analyst.usuario_id)
        .distinct()
        .order_by(Project.nombre, DataModel.nombre, Project.proyecto_id, DataModel.modelo_id)
    ).all()
    return ExecutionCasePage(
        items=[_to_list_item(*row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        opciones=[ExecutionFilterOption(
            proyecto_id=project_id, proyecto_nombre=project_name,
            modelo_id=model_id, modelo_nombre=model_name,
        ) for project_id, project_name, model_id, model_name in options],
    )


@router.get("/execution-cases/{caso_prueba_id}", response_model=ExecutionCaseDetail)
def get_execution_case(
    caso_prueba_id: int,
    db: Session = Depends(get_db),
    analyst: User = Depends(require_roles("Analista/Tester")),
):
    case, generation, model, project = _owned_case_context(db, caso_prueba_id, analyst)
    latest = _latest_execution_subquery(db, caso_prueba_id)

    data_rows = db.execute(
        select(GeneratedData, DataField, DataType)
        .join(DataField, DataField.campo_id == GeneratedData.campo_id)
        .join(DataType, DataType.tipo_dato_id == DataField.tipo_dato_id)
        .where(GeneratedData.caso_prueba_id == caso_prueba_id)
        .order_by(DataField.orden.is_(None), DataField.orden, DataField.campo_id)
    ).all()

    base = _to_list_item(case, generation, model, project, latest).model_dump()
    return ExecutionCaseDetail(
        **base,
        datos=[
            ExecutionDataItem(
                campo_id=field.campo_id,
                campo_nombre=field.nombre,
                tipo_dato_codigo=data_type.codigo,
                valor_generado=data.valor_generado,
            )
            for data, field, data_type in data_rows
        ],
        observacion=latest.observacion if latest else None,
    )


@router.post(
    "/execution-cases/{caso_prueba_id}/executions",
    response_model=ExecutionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_manual_execution(
    caso_prueba_id: int,
    payload: ExecutionCreate,
    db: Session = Depends(get_db),
    analyst: User = Depends(require_roles("Analista/Tester")),
):
    case, _, _, _ = _owned_case_context(db, caso_prueba_id, analyst)

    observed = (payload.resultado_obtenido or "").strip() or None
    note = (payload.observacion or "").strip() or None
    final_status = _classify(case.resultado_esperado, observed, payload.bloqueado)

    execution = Execution(
        caso_prueba_id=case.caso_prueba_id,
        usuario_id=analyst.usuario_id,
        origen_registro="MANUAL",
        resultado_obtenido=observed,
        estado=final_status,
        observacion=note,
        fecha_ejecucion=payload.fecha_ejecucion,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    return ExecutionResponse(
        ejecucion_id=execution.ejecucion_id,
        caso_prueba_id=execution.caso_prueba_id,
        usuario_id=execution.usuario_id,
        origen_registro=execution.origen_registro,
        resultado_obtenido=execution.resultado_obtenido,
        estado=execution.estado,
        observacion=execution.observacion,
        fecha_ejecucion=execution.fecha_ejecucion,
        fecha_registro=execution.fecha_registro,
    )


@router.get("/executions/{ejecucion_id}", response_model=ExecutionResponse)
def get_execution(
    ejecucion_id: int,
    db: Session = Depends(get_db),
    analyst: User = Depends(require_roles("Analista/Tester")),
):
    execution = db.scalar(select(Execution).where(Execution.ejecucion_id == ejecucion_id))
    if execution is None:
        raise HTTPException(status_code=404, detail="Ejecución no encontrada.")
    _owned_case_context(db, execution.caso_prueba_id, analyst)
    return ExecutionResponse(
        ejecucion_id=execution.ejecucion_id,
        caso_prueba_id=execution.caso_prueba_id,
        usuario_id=execution.usuario_id,
        origen_registro=execution.origen_registro,
        resultado_obtenido=execution.resultado_obtenido,
        estado=execution.estado,
        observacion=execution.observacion,
        fecha_ejecucion=execution.fecha_ejecucion,
        fecha_registro=execution.fecha_registro,
    )
