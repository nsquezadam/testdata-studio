from __future__ import annotations

# ============================================================
# CREACIÓN 2026-11-18 - M03 / CP-06
# Endpoints REST para generar, consultar y revisar trazabilidad de
# escenarios VALIDOS, INVALIDOS y LIMITE.
# Motivo: implementar HU-05 / RF08-RF10 sin incluir aún exportación
# CSV/JSON, la cual corresponde a CP-07 / RF11.
#
# MODIFICACIÓN 2026-11-19 - M03 / CP-06 - TRAZABILIDAD ENRIQUECIDA
# Cada regla evaluada devuelve campos, roles, valores generados, parámetros
# y una explicación funcional de su evaluación. Motivo: permitir validar
# coherencia sin depender únicamente del indicador cumple_esperado.
#
# MODIFICACIÓN 2026-11-19 - M03 / CP-06 - AISLAMIENTO DE REGLA OBJETIVO
# La respuesta conserva detalle_esperado persistido cuando existe.
# Motivo: no perder las marcas de regla objetivo y NO APLICA generadas por
# el motor al aislar escenarios INVALIDOS con reglas dependientes.
#
# MODIFICACIÓN 2026-11-20 - M03 / CP-07 - EXPORTACIÓN CSV Y JSON
# Se agregan descargas autenticadas de la data de prueba de una generación.
# Motivo: implementar HU-06 / RF11 permitiendo utilizar los datos generados
# en un sistema externo. Los archivos exportan caso_prueba_id + campos
# dinámicos del modelo; la trazabilidad detallada permanece en TestData Studio.
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import csv
import io
import json

from app.api.deps import require_roles
from app.db import get_db
from app.models.configuration import (
    BusinessRule,
    DataField,
    DataType,
    RuleField,
    RuleParameter,
    RuleType,
)
from app.models.generation import CaseRule, GeneratedData, Generation, TestCase
from app.models.project import DataModel, Project
from app.models.user import User
from app.schemas.generation import (
    CaseRuleResponse,
    GeneratedDataResponse,
    GenerationCreate,
    GenerationListItem,
    GenerationReadinessResponse,
    GenerationResponse,
    RuleTraceFieldResponse,
    RuleTraceParameterResponse,
    TestCaseResponse,
)
from app.services.generation_engine import (
    FieldConfig,
    RuleConfig,
    describe_rule_evaluation,
    generate,
    readiness,
)


router = APIRouter(tags=["Generación de datos y escenarios"])


def _load_generation_context(db: Session, generacion_id: int):
    row = db.execute(
        select(Generation, DataModel, Project)
        .join(DataModel, DataModel.modelo_id == Generation.modelo_id)
        .join(Project, Project.proyecto_id == DataModel.proyecto_id)
        .where(Generation.generacion_id == generacion_id)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Generación no encontrada.")
    return row


def _generation_response(db: Session, generacion_id: int) -> GenerationResponse:
    generation, model, project = _load_generation_context(db, generacion_id)

    cases = db.scalars(
        select(TestCase)
        .where(TestCase.generacion_id == generacion_id)
        .order_by(TestCase.caso_prueba_id)
    ).all()

    # ============================================================
    # OPTIMIZACIÓN 2026-11-21 - JM-01 / RNF03
    # Se elimina el patrón N+1 de consultas al construir la respuesta de una
    # generación. Antes se consultaban datos/reglas por cada caso y además
    # campos/parámetros por cada regla, lo que multiplicaba los viajes a Neon.
    # Ahora la trazabilidad completa se carga en consultas agrupadas y se
    # organiza en memoria. No cambia el JSON expuesto por la API.
    # ============================================================
    case_ids = [case.caso_prueba_id for case in cases]

    data_by_case: dict[int, list[tuple[GeneratedData, DataField, DataType]]] = {
        case_id: [] for case_id in case_ids
    }
    rules_by_case: dict[int, list[tuple[CaseRule, BusinessRule, RuleType]]] = {
        case_id: [] for case_id in case_ids
    }

    if case_ids:
        all_data_rows = db.execute(
            select(GeneratedData, DataField, DataType)
            .join(DataField, DataField.campo_id == GeneratedData.campo_id)
            .join(DataType, DataType.tipo_dato_id == DataField.tipo_dato_id)
            .where(GeneratedData.caso_prueba_id.in_(case_ids))
            .order_by(
                GeneratedData.caso_prueba_id,
                DataField.orden.is_(None),
                DataField.orden,
                DataField.campo_id,
            )
        ).all()
        for data, field, data_type in all_data_rows:
            data_by_case[data.caso_prueba_id].append((data, field, data_type))

        all_rule_rows = db.execute(
            select(CaseRule, BusinessRule, RuleType)
            .join(BusinessRule, BusinessRule.regla_id == CaseRule.regla_id)
            .join(RuleType, RuleType.tipo_regla_id == BusinessRule.tipo_regla_id)
            .where(CaseRule.caso_prueba_id.in_(case_ids))
            .order_by(CaseRule.caso_prueba_id, BusinessRule.regla_id)
        ).all()
        for trace, rule, rule_type in all_rule_rows:
            rules_by_case[trace.caso_prueba_id].append((trace, rule, rule_type))
    else:
        all_rule_rows = []

    rule_ids = sorted({rule.regla_id for _, rule, _ in all_rule_rows})
    fields_by_rule: dict[int, list[tuple[RuleField, DataField, DataType]]] = {
        rule_id: [] for rule_id in rule_ids
    }
    params_by_rule: dict[int, list[RuleParameter]] = {
        rule_id: [] for rule_id in rule_ids
    }

    if rule_ids:
        all_rule_field_rows = db.execute(
            select(RuleField, DataField, DataType)
            .join(DataField, DataField.campo_id == RuleField.campo_id)
            .join(DataType, DataType.tipo_dato_id == DataField.tipo_dato_id)
            .where(RuleField.regla_id.in_(rule_ids))
            .order_by(RuleField.regla_id, RuleField.rol_campo, DataField.campo_id)
        ).all()
        for association, field, data_type in all_rule_field_rows:
            fields_by_rule[association.regla_id].append((association, field, data_type))

        all_params = db.scalars(
            select(RuleParameter)
            .where(RuleParameter.regla_id.in_(rule_ids))
            .order_by(
                RuleParameter.regla_id,
                RuleParameter.orden.is_(None),
                RuleParameter.orden,
                RuleParameter.parametro_id,
            )
        ).all()
        for param in all_params:
            params_by_rule[param.regla_id].append(param)

    case_responses: list[TestCaseResponse] = []
    for case in cases:
        data_rows = data_by_case[case.caso_prueba_id]
        rule_rows = rules_by_case[case.caso_prueba_id]

        generated_values = {
            field.campo_id: data.valor_generado
            for data, field, _ in data_rows
        }

        target_id = None
        target_name = None
        for trace, rule, _ in rule_rows:
            if (trace.detalle_esperado or "").startswith("Regla objetivo"):
                target_id = rule.regla_id
                target_name = rule.nombre
                break

        enriched_rules: list[CaseRuleResponse] = []
        for trace, rule, rule_type in rule_rows:
            rule_field_rows = fields_by_rule.get(rule.regla_id, [])
            rule_params = params_by_rule.get(rule.regla_id, [])

            config_fields: dict[str, FieldConfig] = {}
            trace_fields: list[RuleTraceFieldResponse] = []
            for association, field, data_type in rule_field_rows:
                role = association.rol_campo.upper()
                config_fields[role] = FieldConfig(
                    campo_id=field.campo_id,
                    nombre=field.nombre,
                    tipo=data_type.codigo.upper(),
                    orden=field.orden,
                )
                trace_fields.append(
                    RuleTraceFieldResponse(
                        campo_id=field.campo_id,
                        campo_nombre=field.nombre,
                        tipo_dato_codigo=data_type.codigo,
                        rol_campo=role,
                        valor_generado=generated_values.get(field.campo_id),
                    )
                )

            config = RuleConfig(
                regla_id=rule.regla_id,
                nombre=rule.nombre,
                tipo=rule_type.codigo.upper(),
                fields=config_fields,
                params={
                    param.clave.strip().lower(): param.valor.strip()
                    for param in rule_params
                },
            )

            enriched_rules.append(
                CaseRuleResponse(
                    regla_id=rule.regla_id,
                    regla_nombre=rule.nombre,
                    tipo_regla_codigo=rule_type.codigo,
                    campos=trace_fields,
                    parametros=[
                        RuleTraceParameterResponse(
                            parametro_id=param.parametro_id,
                            clave=param.clave,
                            valor=param.valor,
                            orden=param.orden,
                        )
                        for param in rule_params
                    ],
                    cumple_esperado=trace.cumple_esperado,
                    detalle_esperado=(
                        trace.detalle_esperado
                        or describe_rule_evaluation(
                            generated_values,
                            config,
                            trace.cumple_esperado,
                        )
                    ),
                )
            )

        case_responses.append(
            TestCaseResponse(
                caso_prueba_id=case.caso_prueba_id,
                tipo_escenario=case.tipo_escenario,
                resultado_esperado=case.resultado_esperado,
                fecha_creacion=case.fecha_creacion,
                regla_objetivo_id=target_id,
                regla_objetivo_nombre=target_name,
                datos=[
                    GeneratedDataResponse(
                        dato_generado_id=data.dato_generado_id,
                        campo_id=field.campo_id,
                        campo_nombre=field.nombre,
                        tipo_dato_codigo=data_type.codigo,
                        valor_generado=data.valor_generado,
                    )
                    for data, field, data_type in data_rows
                ],
                reglas=enriched_rules,
            )
        )

    scenario = cases[0].tipo_escenario if cases else "VALIDO"
    return GenerationResponse(
        generacion_id=generation.generacion_id,
        modelo_id=model.modelo_id,
        modelo_nombre=model.nombre,
        proyecto_id=project.proyecto_id,
        proyecto_nombre=project.nombre,
        usuario_id=generation.usuario_id,
        cantidad_solicitada=generation.cantidad_solicitada,
        tipo_escenario=scenario,
        fecha_generacion=generation.fecha_generacion,
        estado=generation.estado,
        casos=case_responses,
    )


def _owned_generation_response(
    db: Session,
    generacion_id: int,
    analyst: User,
) -> GenerationResponse:
    """Obtiene una generación del analista y valida que tenga registros exportables."""
    generation = db.scalar(
        select(Generation).where(Generation.generacion_id == generacion_id)
    )
    if generation is None:
        raise HTTPException(status_code=404, detail="Generación no encontrada.")
    if generation.usuario_id != analyst.usuario_id:
        raise HTTPException(
            status_code=403,
            detail="No posee permisos para exportar esta generación.",
        )

    detail = _generation_response(db, generacion_id)
    if not detail.casos:
        raise HTTPException(
            status_code=409,
            detail="La generación no contiene registros disponibles para exportar.",
        )
    return detail


def _coerce_export_value(value: str | None, data_type: str) -> object:
    """Convierte el valor persistido al tipo lógico del campo para exportación JSON."""
    if value is None:
        return None

    code = (data_type or "").upper()
    text = str(value)

    try:
        if code == "INTEGER":
            return int(text)
        if code == "DECIMAL":
            return float(text)
        if code == "BOOLEAN":
            lowered = text.strip().lower()
            if lowered == "true":
                return True
            if lowered == "false":
                return False
    except (TypeError, ValueError):
        # Si un valor histórico no puede convertirse, se conserva como texto
        # para no impedir la exportación de una generación ya almacenada.
        return text

    return text


def _export_rows(detail: GenerationResponse) -> tuple[list[str], list[dict[str, object]]]:
    """Construye data de prueba: caso_prueba_id + campos dinámicos del modelo."""
    field_names: list[str] = []
    seen: set[str] = set()
    for case in detail.casos:
        for item in case.datos:
            if item.campo_nombre not in seen:
                seen.add(item.campo_nombre)
                field_names.append(item.campo_nombre)

    rows: list[dict[str, object]] = []
    for case in detail.casos:
        values = {
            item.campo_nombre: _coerce_export_value(
                item.valor_generado,
                item.tipo_dato_codigo,
            )
            for item in case.datos
        }
        row: dict[str, object] = {"caso_prueba_id": case.caso_prueba_id}
        for field_name in field_names:
            row[field_name] = values.get(field_name)
        rows.append(row)

    return field_names, rows


@router.get(
    "/models/{modelo_id}/generation-readiness",
    response_model=GenerationReadinessResponse,
)
def generation_readiness(
    modelo_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Analista/Tester")),
):
    config, issues, limit_count = readiness(db, modelo_id)
    return GenerationReadinessResponse(
        modelo_id=config.model.modelo_id,
        modelo_nombre=config.model.nombre,
        proyecto_id=config.project.proyecto_id,
        proyecto_nombre=config.project.nombre,
        campos_activos=len(config.fields),
        reglas_activas=len(config.rules),
        reglas_limite=limit_count,
        listo=not issues,
        observaciones=issues,
    )


@router.post(
    "/generations",
    response_model=GenerationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_generation(
    payload: GenerationCreate,
    db: Session = Depends(get_db),
    analyst: User = Depends(require_roles("Analista/Tester")),
):
    try:
        generation = generate(
            db=db,
            modelo_id=payload.modelo_id,
            usuario_id=analyst.usuario_id,
            cantidad=payload.cantidad_solicitada,
            scenario=payload.tipo_escenario,
        )
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

    return _generation_response(db, generation.generacion_id)


@router.get("/generations", response_model=list[GenerationListItem])
def list_generations(
    modelo_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    analyst: User = Depends(require_roles("Analista/Tester")),
):
    statement = (
        select(
            Generation,
            DataModel,
            Project,
            TestCase.tipo_escenario,
            func.count(TestCase.caso_prueba_id).label("total_casos"),
        )
        .join(DataModel, DataModel.modelo_id == Generation.modelo_id)
        .join(Project, Project.proyecto_id == DataModel.proyecto_id)
        .join(TestCase, TestCase.generacion_id == Generation.generacion_id)
        .where(Generation.usuario_id == analyst.usuario_id)
        .group_by(
            Generation.generacion_id,
            DataModel.modelo_id,
            Project.proyecto_id,
            TestCase.tipo_escenario,
        )
        .order_by(Generation.generacion_id.desc())
        .limit(limit)
    )
    if modelo_id is not None:
        statement = statement.where(Generation.modelo_id == modelo_id)

    rows = db.execute(statement).all()
    return [
        GenerationListItem(
            generacion_id=generation.generacion_id,
            modelo_id=model.modelo_id,
            modelo_nombre=model.nombre,
            proyecto_id=project.proyecto_id,
            proyecto_nombre=project.nombre,
            cantidad_solicitada=generation.cantidad_solicitada,
            tipo_escenario=scenario,
            fecha_generacion=generation.fecha_generacion,
            estado=generation.estado,
            total_casos=total_cases,
        )
        for generation, model, project, scenario, total_cases in rows
    ]


@router.get("/generations/{generacion_id}/export/csv")
def export_generation_csv(
    generacion_id: int,
    db: Session = Depends(get_db),
    analyst: User = Depends(require_roles("Analista/Tester")),
):
    detail = _owned_generation_response(db, generacion_id, analyst)
    field_names, rows = _export_rows(detail)

    output = io.StringIO(newline="")
    headers = ["caso_prueba_id", *field_names]
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()

    # CSV se orienta a interoperabilidad: booleanos en minúscula y NULL vacío.
    for row in rows:
        csv_row = {
            key: (
                "true" if value is True
                else "false" if value is False
                else value
            )
            for key, value in row.items()
        }
        writer.writerow(csv_row)

    # BOM UTF-8 para facilitar apertura directa en Excel sin perder acentos.
    content = "\ufeff" + output.getvalue()
    filename = f"testdata_generacion_{generacion_id}.csv"
    return Response(
        content=content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/generations/{generacion_id}/export/json")
def export_generation_json(
    generacion_id: int,
    db: Session = Depends(get_db),
    analyst: User = Depends(require_roles("Analista/Tester")),
):
    detail = _owned_generation_response(db, generacion_id, analyst)
    _, rows = _export_rows(detail)

    # JSON se entrega como arreglo directo para facilitar su consumo por otro sistema.
    payload = rows
    filename = f"testdata_generacion_{generacion_id}.json"
    return Response(
        content=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/generations/{generacion_id}", response_model=GenerationResponse)
def get_generation(
    generacion_id: int,
    db: Session = Depends(get_db),
    analyst: User = Depends(require_roles("Analista/Tester")),
):
    generation = db.scalar(
        select(Generation).where(Generation.generacion_id == generacion_id)
    )
    if generation is None:
        raise HTTPException(status_code=404, detail="Generación no encontrada.")
    if generation.usuario_id != analyst.usuario_id:
        raise HTTPException(status_code=403, detail="No posee permisos para consultar esta generación.")
    return _generation_response(db, generacion_id)
