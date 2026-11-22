from __future__ import annotations

# ============================================================
# CREACIÓN 2026-11-18 - M03 / CP-06
# Motor determinístico de generación de escenarios para el MVP.
# Genera casos VALIDOS, INVALIDOS y LIMITE utilizando las seis reglas
# configurables de M02. No ejecuta pruebas sobre sistemas externos.
# Motivo: cumplir RF08, RF09 y RF10 manteniendo el alcance definido
# para TestData Studio y una generación reproducible para pruebas.
#
# MODIFICACIÓN 2026-11-19 - M03 / CP-06 - TRAZABILIDAD ENRIQUECIDA
# Se incorpora una descripción funcional de la evaluación de cada regla.
# Motivo: reemplazar mensajes genéricos por evidencia legible que relacione
# regla, campo(s), parámetros, valor(es) generados y resultado esperado.
#
# MODIFICACIÓN 2026-11-19 - M03 / CP-06 - AISLAMIENTO DE REGLA OBJETIVO
# Los escenarios INVALIDOS intentan incumplir únicamente la regla objetivo.
# Se reparan reglas relacionadas sin modificar los campos bloqueados por la
# regla objetivo y, cuando un REQUIRED deja el dato en NULL, las reglas que
# dependen de ese mismo valor se registran como NO APLICA para evitar falsos
# incumplimientos secundarios.
# Motivo: asegurar escenarios negativos controlados, coherentes y trazables.
# ============================================================

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import re

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

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


VALID_SCENARIOS = {"VALIDO", "INVALIDO", "LIMITE"}
ORDER_OPERATORS = {">", ">=", "<", "<="}
ACTION_TO_OPERATOR = {
    "EQUALS": "=",
    "NOT_EQUALS": "!=",
    "GREATER_THAN": ">",
    "GREATER_EQUAL": ">=",
    "LESS_THAN": "<",
    "LESS_EQUAL": "<=",
}


@dataclass(frozen=True)
class FieldConfig:
    campo_id: int
    nombre: str
    tipo: str
    orden: int | None


@dataclass(frozen=True)
class RuleConfig:
    regla_id: int
    nombre: str
    tipo: str
    fields: dict[str, FieldConfig]
    params: dict[str, str]


@dataclass(frozen=True)
class ModelConfiguration:
    model: DataModel
    project: Project
    fields: list[FieldConfig]
    rules: list[RuleConfig]


def _field_default(field: FieldConfig, index: int) -> str:
    tipo = field.tipo.upper()
    pos = index + 1
    if tipo == "INTEGER":
        return str(10 + pos)
    if tipo == "DECIMAL":
        return f"{10 + pos}.50"
    if tipo == "DATE":
        return (date(2026, 1, 1) + timedelta(days=index)).isoformat()
    if tipo == "BOOLEAN":
        return "true" if index % 2 == 0 else "false"
    if tipo == "EMAIL":
        return f"cliente{pos}@testdata.local"
    return f"dato_{pos}"


def _parse_value(value: str | None, tipo: str):
    if value is None:
        return None
    tipo = tipo.upper()
    if tipo == "INTEGER":
        return int(value)
    if tipo == "DECIMAL":
        return Decimal(value)
    if tipo == "DATE":
        return date.fromisoformat(value)
    if tipo == "BOOLEAN":
        return value.strip().lower() in {"true", "1", "si", "sí"}
    return value


def _serialize_value(value) -> str:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _step_value(value, tipo: str, step: int):
    tipo = tipo.upper()
    if tipo == "INTEGER":
        return int(value) + step
    if tipo == "DECIMAL":
        return Decimal(value) + Decimal(step)
    if tipo == "DATE":
        return value + timedelta(days=step)
    if tipo == "BOOLEAN":
        return not bool(value)
    return f"{value}_{'alt' if step > 0 else 'prev'}"


def _compare(left, operator: str, right) -> bool:
    if operator == "=":
        return left == right
    if operator == "!=":
        return left != right
    if operator == ">":
        return left > right
    if operator == ">=":
        return left >= right
    if operator == "<":
        return left < right
    if operator == "<=":
        return left <= right
    return False


def _model_configuration(db: Session, modelo_id: int) -> ModelConfiguration:
    model = db.scalar(select(DataModel).where(DataModel.modelo_id == modelo_id))
    if model is None:
        raise HTTPException(status_code=404, detail="Modelo no encontrado.")

    project = db.scalar(select(Project).where(Project.proyecto_id == model.proyecto_id))
    if project is None:
        raise HTTPException(status_code=404, detail="Proyecto asociado no encontrado.")
    if not project.estado:
        raise HTTPException(status_code=400, detail="El proyecto seleccionado se encuentra inactivo.")
    if not model.estado:
        raise HTTPException(status_code=400, detail="El modelo seleccionado se encuentra inactivo.")

    field_rows = db.execute(
        select(DataField, DataType)
        .join(DataType, DataType.tipo_dato_id == DataField.tipo_dato_id)
        .where(
            DataField.modelo_id == modelo_id,
            DataField.estado.is_(True),
            DataType.estado.is_(True),
        )
        .order_by(DataField.orden.is_(None), DataField.orden, DataField.campo_id)
    ).all()

    fields = [
        FieldConfig(
            campo_id=field.campo_id,
            nombre=field.nombre,
            tipo=data_type.codigo.upper(),
            orden=field.orden,
        )
        for field, data_type in field_rows
    ]
    field_map = {field.campo_id: field for field in fields}

    rule_rows = db.execute(
        select(BusinessRule, RuleType)
        .join(RuleType, RuleType.tipo_regla_id == BusinessRule.tipo_regla_id)
        .where(
            BusinessRule.modelo_id == modelo_id,
            BusinessRule.estado.is_(True),
            RuleType.estado.is_(True),
        )
        .order_by(BusinessRule.regla_id)
    ).all()

    rules: list[RuleConfig] = []
    for rule, rule_type in rule_rows:
        associations = db.scalars(
            select(RuleField)
            .where(RuleField.regla_id == rule.regla_id)
            .order_by(RuleField.campo_id)
        ).all()
        params = db.scalars(
            select(RuleParameter)
            .where(RuleParameter.regla_id == rule.regla_id)
            .order_by(
                RuleParameter.orden.is_(None),
                RuleParameter.orden,
                RuleParameter.parametro_id,
            )
        ).all()

        role_fields: dict[str, FieldConfig] = {}
        for association in associations:
            field = field_map.get(association.campo_id)
            if field is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"La regla '{rule.nombre}' utiliza un campo inactivo o no disponible. "
                        "Revise la configuración antes de generar."
                    ),
                )
            role_fields[association.rol_campo.upper()] = field

        rules.append(
            RuleConfig(
                regla_id=rule.regla_id,
                nombre=rule.nombre,
                tipo=rule_type.codigo.upper(),
                fields=role_fields,
                params={param.clave.strip().lower(): param.valor.strip() for param in params},
            )
        )

    return ModelConfiguration(model=model, project=project, fields=fields, rules=rules)


def readiness(db: Session, modelo_id: int) -> tuple[ModelConfiguration, list[str], int]:
    config = _model_configuration(db, modelo_id)
    issues: list[str] = []

    if not config.fields:
        issues.append("El modelo no posee campos activos disponibles para generar datos.")
    if not config.rules:
        issues.append("El modelo no posee reglas activas disponibles para generar escenarios.")

    # MODIFICACIÓN 2026-11-22 - M03 / CP-06
    # Detectar listas incompletas o heredadas antes de generar casos.
    # No se inventan valores ni se omiten reglas de negocio activas.
    invalid_list_ids: set[int] = set()
    for rule in config.rules:
        if rule.tipo == "ALLOWED_VALUES" and not any(
            value.strip() for value in rule.params.get("valores", "").split(",")
        ):
            invalid_list_ids.add(rule.regla_id)
            issues.append(
                f"La regla '{rule.nombre}' (ID {rule.regla_id}) no posee valores permitidos "
                "en el parámetro 'valores'. Edítela y guárdela nuevamente en Campos y reglas."
            )

    limit_count = sum(
        1 for rule in config.rules
        if rule.regla_id not in invalid_list_ids and _is_limit_capable(rule)
    )
    return config, issues, limit_count


def _is_limit_capable(rule: RuleConfig) -> bool:
    if rule.tipo in {"RANGE", "ALLOWED_VALUES"}:
        return True
    if rule.tipo == "FORMAT":
        return "longitud_min" in rule.params or "longitud_max" in rule.params
    if rule.tipo == "COMPARISON":
        return rule.params.get("operador") in {"=", ">", ">=", "<", "<="}
    if rule.tipo == "CONDITIONAL":
        return rule.params.get("accion", "").upper() in {
            "EQUALS",
            "GREATER_THAN",
            "GREATER_EQUAL",
            "LESS_THAN",
            "LESS_EQUAL",
            "ALLOWED_VALUES",
        }
    return False


def _principal(rule: RuleConfig) -> FieldConfig:
    field = rule.fields.get("PRINCIPAL")
    if field is None and len(rule.fields) == 1:
        field = next(iter(rule.fields.values()))
    if field is None:
        raise HTTPException(status_code=400, detail=f"La regla '{rule.nombre}' no posee campo PRINCIPAL.")
    return field


def _valid_text_for_format(rule: RuleConfig, field: FieldConfig, index: int) -> str:
    min_len = int(rule.params.get("longitud_min", "0"))
    max_len = int(rule.params.get("longitud_max", "0")) or None
    target_len = max(min_len, 6 if field.tipo != "EMAIL" else 18)
    if max_len is not None:
        target_len = min(target_len, max_len)

    candidates: list[str] = []
    if field.tipo == "EMAIL":
        candidates.extend([
            f"u{index + 1}@a.cl",
            f"cliente{index + 1}@test.cl",
            f"usuario{index + 1}@testdata.local",
        ])
    else:
        candidates.extend([
            "A" * max(1, target_len),
            "dato" + str(index + 1),
            "TEST" + str(index + 1),
            "1234567890",
        ])

    pattern = rule.params.get("patron")
    for candidate in candidates:
        if len(candidate) < min_len:
            candidate = candidate + ("A" * (min_len - len(candidate)))
        if max_len is not None and len(candidate) > max_len:
            candidate = candidate[:max_len]
        if field.tipo == "EMAIL" and "@" not in candidate:
            continue
        if pattern:
            try:
                if re.fullmatch(pattern, candidate) is None:
                    continue
            except re.error as exc:
                raise HTTPException(
                    status_code=400,
                    detail=f"La regla '{rule.nombre}' contiene un patrón inválido: {exc}.",
                ) from None
        return candidate

    raise HTTPException(
        status_code=400,
        detail=(
            f"No fue posible construir automáticamente un valor para el patrón de la regla "
            f"'{rule.nombre}'. Simplifique el patrón para el alcance del MVP."
        ),
    )


def _apply_comparison(values: dict[int, str | None], rule: RuleConfig, valid: bool, limit: bool = False) -> None:
    principal = rule.fields.get("PRINCIPAL")
    reference = rule.fields.get("REFERENCIA")
    if principal is None or reference is None:
        raise HTTPException(status_code=400, detail=f"La regla '{rule.nombre}' no posee PRINCIPAL/REFERENCIA.")

    operator = rule.params.get("operador", "=")
    right = _parse_value(values[reference.campo_id], reference.tipo)

    if operator == "=":
        left = right if valid else _step_value(right, principal.tipo, 1)
    elif operator == "!=":
        left = _step_value(right, principal.tipo, 1) if valid else right
    elif operator in {">", ">="}:
        if valid:
            left = right if operator == ">=" and limit else _step_value(right, principal.tipo, 1)
        else:
            left = right if operator == ">" else _step_value(right, principal.tipo, -1)
    elif operator in {"<", "<="}:
        if valid:
            left = right if operator == "<=" and limit else _step_value(right, principal.tipo, -1)
        else:
            left = right if operator == "<" else _step_value(right, principal.tipo, 1)
    else:
        raise HTTPException(status_code=400, detail=f"Operador no soportado en la regla '{rule.nombre}'.")

    values[principal.campo_id] = _serialize_value(left)


def _apply_action(values: dict[int, str | None], rule: RuleConfig, valid: bool, limit: bool = False) -> None:
    principal = rule.fields.get("PRINCIPAL")
    if principal is None:
        raise HTTPException(status_code=400, detail=f"La regla '{rule.nombre}' no posee campo PRINCIPAL.")

    action = rule.params.get("accion", "").upper()
    action_value = rule.params.get("accion_valor")

    if action == "REQUIRED":
        values[principal.campo_id] = _field_default(principal, 0) if valid else None
        return

    if action == "ALLOWED_VALUES":
        allowed = [x.strip() for x in rule.params.get("accion_valores", "").split(",") if x.strip()]
        if not allowed:
            raise HTTPException(status_code=400, detail=f"La regla '{rule.nombre}' no posee valores de consecuencia.")
        values[principal.campo_id] = (allowed[-1] if limit else allowed[0]) if valid else "__FUERA_DE_LISTA__"
        return

    if action not in ACTION_TO_OPERATOR or action_value is None:
        raise HTTPException(status_code=400, detail=f"La consecuencia de '{rule.nombre}' no está completa.")

    operator = ACTION_TO_OPERATOR[action]
    boundary = _parse_value(action_value, principal.tipo)
    if operator == "=":
        result = boundary if valid else _step_value(boundary, principal.tipo, 1)
    elif operator == "!=":
        result = _step_value(boundary, principal.tipo, 1) if valid else boundary
    elif operator in {">", ">="}:
        result = (
            boundary if valid and operator == ">=" and limit
            else _step_value(boundary, principal.tipo, 1) if valid
            else boundary if operator == ">"
            else _step_value(boundary, principal.tipo, -1)
        )
    else:  # < / <=
        result = (
            boundary if valid and operator == "<=" and limit
            else _step_value(boundary, principal.tipo, -1) if valid
            else boundary if operator == "<"
            else _step_value(boundary, principal.tipo, 1)
        )
    values[principal.campo_id] = _serialize_value(result)


def _activate_condition(values: dict[int, str | None], rule: RuleConfig) -> None:
    condition = rule.fields.get("CONDICION")
    if condition is None:
        raise HTTPException(status_code=400, detail=f"La regla '{rule.nombre}' no posee campo CONDICION.")
    condition_value = rule.params.get("condicion_valor")
    operator = rule.params.get("condicion_operador", "=")
    if condition_value is None:
        raise HTTPException(status_code=400, detail=f"La regla '{rule.nombre}' no posee valor de condición.")

    boundary = _parse_value(condition_value, condition.tipo)
    if operator in {"=", ">=", "<="}:
        result = boundary
    elif operator == "!=":
        result = _step_value(boundary, condition.tipo, 1)
    elif operator == ">":
        result = _step_value(boundary, condition.tipo, 1)
    elif operator == "<":
        result = _step_value(boundary, condition.tipo, -1)
    else:
        result = boundary
    values[condition.campo_id] = _serialize_value(result)


def _apply_rule_valid(values: dict[int, str | None], rule: RuleConfig, index: int) -> None:
    principal = _principal(rule)

    if rule.tipo == "REQUIRED":
        if values.get(principal.campo_id) in {None, ""}:
            values[principal.campo_id] = _field_default(principal, index)
        return

    if rule.tipo == "RANGE":
        minimum = _parse_value(rule.params["min"], principal.tipo)
        maximum = _parse_value(rule.params["max"], principal.tipo)
        if principal.tipo == "DATE":
            value = minimum + (maximum - minimum) / 2
        elif principal.tipo == "INTEGER":
            value = (minimum + maximum) // 2
        else:
            value = (minimum + maximum) / 2
        values[principal.campo_id] = _serialize_value(value)
        return

    if rule.tipo == "ALLOWED_VALUES":
        allowed = [x.strip() for x in rule.params["valores"].split(",") if x.strip()]
        values[principal.campo_id] = allowed[index % len(allowed)]
        return

    if rule.tipo == "FORMAT":
        values[principal.campo_id] = _valid_text_for_format(rule, principal, index)
        return

    if rule.tipo == "COMPARISON":
        _apply_comparison(values, rule, valid=True)
        return

    if rule.tipo == "CONDITIONAL":
        _activate_condition(values, rule)
        _apply_action(values, rule, valid=True)
        return


def _apply_rule_invalid(values: dict[int, str | None], rule: RuleConfig, index: int) -> None:
    principal = _principal(rule)

    if rule.tipo == "REQUIRED":
        values[principal.campo_id] = None
        return

    if rule.tipo == "RANGE":
        minimum = _parse_value(rule.params["min"], principal.tipo)
        maximum = _parse_value(rule.params["max"], principal.tipo)
        boundary = minimum if index % 2 == 0 else maximum
        step = -1 if index % 2 == 0 else 1
        values[principal.campo_id] = _serialize_value(_step_value(boundary, principal.tipo, step))
        return

    if rule.tipo == "ALLOWED_VALUES":
        allowed = {x.strip() for x in rule.params["valores"].split(",") if x.strip()}
        candidate = "__INVALIDO__"
        while candidate in allowed:
            candidate += "X"
        values[principal.campo_id] = candidate
        return

    if rule.tipo == "FORMAT":
        minimum = int(rule.params.get("longitud_min", "0"))
        maximum = int(rule.params.get("longitud_max", "0")) if rule.params.get("longitud_max") else None
        if minimum > 0:
            values[principal.campo_id] = "X" * max(0, minimum - 1)
        elif maximum is not None:
            values[principal.campo_id] = "X" * (maximum + 1)
        else:
            pattern = rule.params.get("patron", "")
            candidate = "###INVALIDO###"
            try:
                if pattern and re.fullmatch(pattern, candidate):
                    candidate = "@@@"
            except re.error:
                pass
            values[principal.campo_id] = candidate
        return

    if rule.tipo == "COMPARISON":
        _apply_comparison(values, rule, valid=False)
        return

    if rule.tipo == "CONDITIONAL":
        _activate_condition(values, rule)
        _apply_action(values, rule, valid=False)
        return


def _rule_field_ids(rule: RuleConfig) -> set[int]:
    """Retorna los campos que participan en una regla."""
    return {field.campo_id for field in rule.fields.values()}


def _deactivate_condition(values: dict[int, str | None], rule: RuleConfig) -> None:
    """Fuerza la condición de una regla CONDITIONAL a FALSE.

    Se usa al aislar un escenario inválido: si la regla condicional no es la
    regla objetivo, desactivar su condición evita introducir un segundo
    incumplimiento sin tocar el campo que está siendo probado.
    """
    condition = rule.fields.get("CONDICION")
    if condition is None:
        raise HTTPException(status_code=400, detail=f"La regla '{rule.nombre}' no posee campo CONDICION.")

    condition_value = rule.params.get("condicion_valor")
    operator = rule.params.get("condicion_operador", "=")
    if condition_value is None:
        raise HTTPException(status_code=400, detail=f"La regla '{rule.nombre}' no posee valor de condición.")

    boundary = _parse_value(condition_value, condition.tipo)
    if operator == "=":
        result = _step_value(boundary, condition.tipo, 1)
    elif operator == "!=":
        result = boundary
    elif operator == ">":
        result = boundary
    elif operator == ">=":
        result = _step_value(boundary, condition.tipo, -1)
    elif operator == "<":
        result = boundary
    elif operator == "<=":
        result = _step_value(boundary, condition.tipo, 1)
    else:
        raise HTTPException(status_code=400, detail=f"Operador condicional no soportado en '{rule.nombre}'.")

    values[condition.campo_id] = _serialize_value(result)


def _repair_comparison_without_locked_fields(
    values: dict[int, str | None],
    rule: RuleConfig,
    locked_fields: set[int],
) -> bool:
    """Intenta cumplir una COMPARISON sin alterar campos de la regla objetivo."""
    principal = rule.fields.get("PRINCIPAL")
    reference = rule.fields.get("REFERENCIA")
    if principal is None or reference is None:
        return False

    principal_locked = principal.campo_id in locked_fields
    reference_locked = reference.campo_id in locked_fields
    if principal_locked and reference_locked:
        return False

    candidate = values.copy()
    operator = rule.params.get("operador", "=")

    try:
        if not principal_locked:
            # La función existente modifica solo PRINCIPAL y conserva REFERENCIA.
            _apply_comparison(candidate, rule, valid=True)
        else:
            # PRINCIPAL corresponde al dato mutado por la regla objetivo.
            # Ajustamos REFERENCIA para conservar la comparación.
            left = _parse_value(candidate.get(principal.campo_id), principal.tipo)
            if left is None:
                return False

            if operator == "=":
                right = left
            elif operator == "!=":
                right = _step_value(left, reference.tipo, 1)
            elif operator == ">":
                right = _step_value(left, reference.tipo, -1)
            elif operator == ">=":
                right = left
            elif operator == "<":
                right = _step_value(left, reference.tipo, 1)
            elif operator == "<=":
                right = left
            else:
                return False
            candidate[reference.campo_id] = _serialize_value(right)
    except (ValueError, TypeError, InvalidOperation):
        return False

    if evaluate_rule(candidate, rule):
        values.clear()
        values.update(candidate)
        return True
    return False


def _repair_non_target_rule(
    values: dict[int, str | None],
    rule: RuleConfig,
    locked_fields: set[int],
    index: int,
) -> bool:
    """Intenta volver válida una regla secundaria sin tocar la regla objetivo."""
    candidate = values.copy()
    principal = _principal(rule)

    try:
        if rule.tipo in {"REQUIRED", "RANGE", "ALLOWED_VALUES", "FORMAT"}:
            if principal.campo_id in locked_fields:
                return False
            _apply_rule_valid(candidate, rule, index)

        elif rule.tipo == "COMPARISON":
            return _repair_comparison_without_locked_fields(values, rule, locked_fields)

        elif rule.tipo == "CONDITIONAL":
            condition = rule.fields.get("CONDICION")
            if condition is None:
                return False

            # Preferimos desactivar la condición si su campo no pertenece a la
            # regla objetivo. Es la forma menos invasiva de mantener coherencia.
            if condition.campo_id not in locked_fields:
                _deactivate_condition(candidate, rule)
            elif principal.campo_id not in locked_fields:
                # Si la condición está bloqueada y activa, hacemos cumplir la consecuencia.
                _apply_action(candidate, rule, valid=True)
            else:
                return False
        else:
            return False
    except (ValueError, TypeError, InvalidOperation, re.error, HTTPException):
        return False

    # Nunca se permite que una reparación modifique un campo bloqueado.
    if any(candidate.get(field_id) != values.get(field_id) for field_id in locked_fields):
        return False

    if evaluate_rule(candidate, rule):
        values.clear()
        values.update(candidate)
        return True
    return False


def _is_non_applicable_due_required_target(
    values: dict[int, str | None],
    target: RuleConfig,
    rule: RuleConfig,
) -> bool:
    """Detecta una regla que no puede evaluarse porque REQUIRED dejó NULL.

    Ejemplo: id_cliente posee REQUIRED y RANGE. Para probar REQUIRED se genera
    NULL; RANGE no debe contarse como un segundo incumplimiento porque no existe
    un valor sobre el cual evaluar el rango.
    """
    if target.tipo != "REQUIRED":
        return False

    target_principal = _principal(target)
    if values.get(target_principal.campo_id) is not None:
        return False

    return target_principal.campo_id in _rule_field_ids(rule)


def _stabilize_invalid_case(
    values: dict[int, str | None],
    config: ModelConfiguration,
    target: RuleConfig,
    index: int,
) -> set[int]:
    """Aísla el incumplimiento del escenario INVALIDO en su regla objetivo.

    Devuelve los IDs de reglas secundarias consideradas NO APLICA. Las demás
    reglas deben quedar válidas; si no es posible, generate() rechazará el caso
    en vez de persistir un escenario ambiguo.
    """
    locked_fields = _rule_field_ids(target)
    non_applicable: set[int] = set()

    # Se realizan varias pasadas porque reparar una relación puede afectar otra
    # regla que comparte el mismo campo. El número de reglas limita el ciclo.
    for _ in range(max(1, len(config.rules) * 2)):
        changed = False
        for rule in config.rules:
            if rule.regla_id == target.regla_id:
                continue
            if evaluate_rule(values, rule):
                continue
            if _is_non_applicable_due_required_target(values, target, rule):
                non_applicable.add(rule.regla_id)
                continue
            if _repair_non_target_rule(values, rule, locked_fields, index):
                changed = True
        if not changed:
            break

    return non_applicable


def _apply_rule_limit(values: dict[int, str | None], rule: RuleConfig, index: int) -> None:
    principal = _principal(rule)

    if rule.tipo == "RANGE":
        value = rule.params["min"] if index % 2 == 0 else rule.params["max"]
        values[principal.campo_id] = value
        return

    if rule.tipo == "ALLOWED_VALUES":
        allowed = [x.strip() for x in rule.params["valores"].split(",") if x.strip()]
        values[principal.campo_id] = allowed[0] if index % 2 == 0 else allowed[-1]
        return

    if rule.tipo == "FORMAT":
        minimum = int(rule.params.get("longitud_min", "0"))
        maximum = int(rule.params.get("longitud_max", "0")) if rule.params.get("longitud_max") else None
        target = minimum if index % 2 == 0 and minimum > 0 else maximum
        if target is None:
            values[principal.campo_id] = _valid_text_for_format(rule, principal, index)
        elif principal.tipo == "EMAIL":
            # Para EMAIL se prioriza conservar formato válido; si el límite es demasiado
            # pequeño para un correo mínimo, la configuración no es generable.
            candidates = [f"a@b.cl", f"u{index + 1}@a.cl", f"x{index + 1}@test.cl"]
            candidate = next((c for c in candidates if len(c) == target), None)
            if candidate is None:
                values[principal.campo_id] = _valid_text_for_format(rule, principal, index)
            else:
                values[principal.campo_id] = candidate
        else:
            values[principal.campo_id] = "L" * max(0, target)
        return

    if rule.tipo == "COMPARISON":
        _apply_comparison(values, rule, valid=True, limit=True)
        return

    if rule.tipo == "CONDITIONAL":
        _activate_condition(values, rule)
        _apply_action(values, rule, valid=True, limit=True)
        return

    raise HTTPException(status_code=400, detail=f"La regla '{rule.nombre}' no define un caso límite utilizable.")


def _evaluate_action(values: dict[int, str | None], rule: RuleConfig) -> bool:
    principal = rule.fields.get("PRINCIPAL")
    if principal is None:
        return False
    value = values.get(principal.campo_id)
    action = rule.params.get("accion", "").upper()

    if action == "REQUIRED":
        return value is not None and str(value).strip() != ""
    if action == "ALLOWED_VALUES":
        allowed = {x.strip() for x in rule.params.get("accion_valores", "").split(",") if x.strip()}
        return value in allowed

    operator = ACTION_TO_OPERATOR.get(action)
    expected = rule.params.get("accion_valor")
    if operator is None or expected is None or value is None:
        return False
    return _compare(
        _parse_value(value, principal.tipo),
        operator,
        _parse_value(expected, principal.tipo),
    )


def evaluate_rule(values: dict[int, str | None], rule: RuleConfig) -> bool:
    principal = _principal(rule)
    value = values.get(principal.campo_id)

    try:
        if rule.tipo == "REQUIRED":
            return value is not None and str(value).strip() != ""

        if rule.tipo == "RANGE":
            if value is None:
                return False
            current = _parse_value(value, principal.tipo)
            return (
                _parse_value(rule.params["min"], principal.tipo)
                <= current
                <= _parse_value(rule.params["max"], principal.tipo)
            )

        if rule.tipo == "ALLOWED_VALUES":
            allowed = {x.strip() for x in rule.params["valores"].split(",") if x.strip()}
            return value in allowed

        if rule.tipo == "FORMAT":
            if value is None:
                return False
            text_value = str(value)
            minimum = int(rule.params.get("longitud_min", "0"))
            maximum = int(rule.params.get("longitud_max", "0")) if rule.params.get("longitud_max") else None
            if len(text_value) < minimum:
                return False
            if maximum is not None and len(text_value) > maximum:
                return False
            pattern = rule.params.get("patron")
            if pattern and re.fullmatch(pattern, text_value) is None:
                return False
            return True

        if rule.tipo == "COMPARISON":
            reference = rule.fields.get("REFERENCIA")
            if reference is None or value is None or values.get(reference.campo_id) is None:
                return False
            return _compare(
                _parse_value(value, principal.tipo),
                rule.params.get("operador", "="),
                _parse_value(values[reference.campo_id], reference.tipo),
            )

        if rule.tipo == "CONDITIONAL":
            condition = rule.fields.get("CONDICION")
            if condition is None or values.get(condition.campo_id) is None:
                return False
            condition_true = _compare(
                _parse_value(values[condition.campo_id], condition.tipo),
                rule.params.get("condicion_operador", "="),
                _parse_value(rule.params.get("condicion_valor"), condition.tipo),
            )
            return True if not condition_true else _evaluate_action(values, rule)
    except (ValueError, TypeError, InvalidOperation, re.error):
        return False

    return False


def describe_rule_evaluation(
    values: dict[int, str | None],
    rule: RuleConfig,
    fulfilled: bool,
) -> str:
    """Devuelve una explicación legible de la evaluación realizada.

    Esta función no reemplaza evaluate_rule(): usa la misma configuración
    para construir trazabilidad comprensible para Swagger, frontend y
    evidencias de CP-06.
    """
    principal = _principal(rule)
    principal_value = values.get(principal.campo_id)
    result_text = "Cumple" if fulfilled else "No cumple"

    if rule.tipo == "REQUIRED":
        shown = "NULL" if principal_value is None else repr(str(principal_value))
        return (
            f"{result_text}: el campo '{principal.nombre}' tiene valor {shown}; "
            "la regla exige que exista un valor informado."
        )

    if rule.tipo == "RANGE":
        minimum = rule.params.get("min", "?")
        maximum = rule.params.get("max", "?")
        shown = "NULL" if principal_value is None else str(principal_value)
        relation = "se encuentra" if fulfilled else "no se encuentra"
        return (
            f"{result_text}: {principal.nombre}={shown} {relation} dentro del rango "
            f"permitido [{minimum}, {maximum}]."
        )

    if rule.tipo == "ALLOWED_VALUES":
        allowed = rule.params.get("valores", "")
        shown = "NULL" if principal_value is None else str(principal_value)
        relation = "pertenece" if fulfilled else "no pertenece"
        return (
            f"{result_text}: {principal.nombre}={shown} {relation} a los valores "
            f"permitidos [{allowed}]."
        )

    if rule.tipo == "FORMAT":
        shown = "NULL" if principal_value is None else str(principal_value)
        constraints: list[str] = []
        if "longitud_min" in rule.params:
            constraints.append(f"longitud mínima {rule.params['longitud_min']}")
        if "longitud_max" in rule.params:
            constraints.append(f"longitud máxima {rule.params['longitud_max']}")
        if "patron" in rule.params:
            constraints.append(f"patrón {rule.params['patron']}")
        configured = ", ".join(constraints) or "formato configurado"
        actual_length = len(str(principal_value)) if principal_value is not None else 0
        return (
            f"{result_text}: {principal.nombre}={shown} tiene longitud {actual_length} "
            f"y se evaluó contra {configured}."
        )

    if rule.tipo == "COMPARISON":
        reference = rule.fields.get("REFERENCIA")
        operator = rule.params.get("operador", "=")
        if reference is None:
            return f"{result_text}: la comparación no posee campo REFERENCIA configurado."
        reference_value = values.get(reference.campo_id)
        return (
            f"{result_text}: {principal.nombre}={principal_value!s} {operator} "
            f"{reference.nombre}={reference_value!s}."
        )

    if rule.tipo == "CONDITIONAL":
        condition = rule.fields.get("CONDICION")
        if condition is None:
            return f"{result_text}: la regla condicional no posee campo CONDICION configurado."

        condition_value = values.get(condition.campo_id)
        condition_operator = rule.params.get("condicion_operador", "=")
        expected_condition = rule.params.get("condicion_valor", "?")

        try:
            condition_true = (
                condition_value is not None
                and _compare(
                    _parse_value(condition_value, condition.tipo),
                    condition_operator,
                    _parse_value(expected_condition, condition.tipo),
                )
            )
        except (ValueError, TypeError, InvalidOperation):
            condition_true = False

        action = rule.params.get("accion", "?").upper()
        if action == "REQUIRED":
            consequence = f"{principal.nombre} debe estar informado"
        elif action == "ALLOWED_VALUES":
            consequence = (
                f"{principal.nombre} debe pertenecer a "
                f"[{rule.params.get('accion_valores', '')}]"
            )
        else:
            operator = ACTION_TO_OPERATOR.get(action, action)
            consequence = (
                f"{principal.nombre} {operator} "
                f"{rule.params.get('accion_valor', '?')}"
            )

        if condition_true:
            return (
                f"{result_text}: SI {condition.nombre}={condition_value!s} "
                f"{condition_operator} {expected_condition}, ENTONCES {consequence}. "
                f"Valor generado de {principal.nombre}={principal_value!s}."
            )

        return (
            f"{result_text}: la condición SI {condition.nombre}={condition_value!s} "
            f"{condition_operator} {expected_condition} no se activa; por lo tanto la "
            "consecuencia no es exigible para este caso."
        )

    return f"{result_text}: regla '{rule.nombre}' evaluada con la configuración activa."


def _build_case_values(
    config: ModelConfiguration,
    scenario: str,
    case_index: int,
) -> tuple[dict[int, str | None], RuleConfig | None, set[int]]:
    values = {field.campo_id: _field_default(field, case_index) for field in config.fields}

    # La base de todos los escenarios se construye intentando satisfacer todas
    # las reglas. Después INVALIDO/LIMITE modifica una regla objetivo concreta.
    for rule in config.rules:
        _apply_rule_valid(values, rule, case_index)

    target: RuleConfig | None = None
    non_applicable: set[int] = set()
    if scenario == "INVALIDO":
        target = config.rules[case_index % len(config.rules)]
        _apply_rule_invalid(values, target, case_index)
        non_applicable = _stabilize_invalid_case(values, config, target, case_index)
    elif scenario == "LIMITE":
        limit_rules = [rule for rule in config.rules if _is_limit_capable(rule)]
        if not limit_rules:
            raise HTTPException(
                status_code=400,
                detail=(
                    "El modelo no posee reglas con límites utilizables. "
                    "Configure Rango, Formato/longitud, Valores permitidos, "
                    "Comparación o una Condicional con consecuencia comparable."
                ),
            )

        # MODIFICACIÓN 2026-11-18 - M03 / CP-06
        # Un mismo campo puede participar en varias reglas (ej. Rango + Conditional).
        # Para un caso LIMITE se prueban las reglas candidatas en rotación y se elige
        # una frontera que siga siendo coherente con el resto de reglas activas.
        # Así evitamos producir un "límite" que en realidad sería un escenario inválido.
        ordered = limit_rules[case_index % len(limit_rules):] + limit_rules[:case_index % len(limit_rules)]
        for candidate in ordered:
            candidate_values = values.copy()
            _apply_rule_limit(candidate_values, candidate, case_index)
            if all(evaluate_rule(candidate_values, rule) for rule in config.rules):
                values = candidate_values
                target = candidate
                break

        if target is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Las reglas activas no permiten construir un caso límite que mantenga "
                    "coherencia con el resto de la configuración."
                ),
            )

    return values, target, non_applicable


def generate(
    db: Session,
    modelo_id: int,
    usuario_id: int,
    cantidad: int,
    scenario: str,
) -> Generation:
    scenario = scenario.upper()
    if scenario not in VALID_SCENARIOS:
        raise HTTPException(status_code=400, detail="Tipo de escenario no soportado.")
    if cantidad < 1 or cantidad > 100:
        raise HTTPException(status_code=400, detail="La cantidad debe estar entre 1 y 100 registros.")

    config, issues, _ = readiness(db, modelo_id)
    if issues:
        raise HTTPException(status_code=400, detail=" ".join(issues))

    generation = Generation(
        modelo_id=modelo_id,
        usuario_id=usuario_id,
        cantidad_solicitada=cantidad,
        estado="PENDIENTE",
    )
    db.add(generation)
    db.flush()

    # ============================================================
    # OPTIMIZACIÓN 2026-11-21 - JM-01 / RNF03
    # Los casos se construyen primero en memoria y luego se persisten por lotes.
    # Motivo: evitar un db.flush() por cada caso, que con PostgreSQL/Neon remoto
    # agregaba una latencia de red repetitiva y hacía que 100 registros excedieran
    # el tiempo objetivo definido para RNF03. La lógica de reglas no cambia.
    # ============================================================
    prepared_cases: list[tuple[TestCase, dict[int, str | None], RuleConfig | None, set[int], dict[int, bool]]] = []

    for index in range(cantidad):
        values, target, non_applicable = _build_case_values(config, scenario, index)
        evaluations = {rule.regla_id: evaluate_rule(values, rule) for rule in config.rules}

        # MODIFICACIÓN 2026-11-19 - CP-06 - AISLAMIENTO DE REGLA OBJETIVO
        # Una regla secundaria que depende del NULL generado para incumplir un
        # REQUIRED se considera NO APLICA. Se conserva cumple_esperado=True por
        # compatibilidad con el modelo actual (boolean NOT NULL), mientras el
        # detalle_esperado deja explícito que la regla no fue evaluable.
        for rule_id in non_applicable:
            evaluations[rule_id] = True

        if scenario in {"VALIDO", "LIMITE"} and not all(evaluations.values()):
            failed = [rule.nombre for rule in config.rules if not evaluations[rule.regla_id]]
            raise HTTPException(
                status_code=400,
                detail=(
                    "La configuración activa contiene reglas incompatibles para generar un escenario "
                    f"{scenario.lower()}: {', '.join(failed)}."
                ),
            )

        if scenario == "INVALIDO" and target is not None and evaluations.get(target.regla_id, True):
            raise HTTPException(
                status_code=400,
                detail=f"No fue posible incumplir la regla objetivo '{target.nombre}'. Revise su configuración.",
            )

        if scenario == "INVALIDO" and target is not None:
            secondary_failures = [
                rule.nombre
                for rule in config.rules
                if rule.regla_id != target.regla_id
                and rule.regla_id not in non_applicable
                and not evaluations[rule.regla_id]
            ]
            if secondary_failures:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"No fue posible aislar la regla objetivo '{target.nombre}'. "
                        "También se incumplen: " + ", ".join(secondary_failures) + "."
                    ),
                )

        if scenario == "INVALIDO" and target is not None:
            expected = f"Rechazar: se incumple intencionalmente la regla '{target.nombre}'."
        elif scenario == "LIMITE" and target is not None:
            expected = f"Aceptar: se utiliza un valor límite asociado a la regla '{target.nombre}'."
        else:
            expected = "Aceptar: los datos cumplen las reglas activas del modelo."

        test_case = TestCase(
            generacion_id=generation.generacion_id,
            tipo_escenario=scenario,
            resultado_esperado=expected,
        )
        prepared_cases.append((test_case, values, target, non_applicable, evaluations))

    # Un solo flush obtiene los IDs de todos los casos. SQLAlchemy puede agrupar
    # las inserciones en PostgreSQL, reduciendo los viajes de ida y vuelta a Neon.
    db.add_all([item[0] for item in prepared_cases])
    db.flush()

    generated_rows: list[GeneratedData] = []
    case_rule_rows: list[CaseRule] = []

    for test_case, values, target, non_applicable, evaluations in prepared_cases:
        for field in config.fields:
            generated_rows.append(
                GeneratedData(
                    caso_prueba_id=test_case.caso_prueba_id,
                    campo_id=field.campo_id,
                    valor_generado=values.get(field.campo_id),
                )
            )

        for rule in config.rules:
            fulfilled = evaluations[rule.regla_id]
            evaluation_detail = describe_rule_evaluation(values, rule, fulfilled)
            if rule.regla_id in non_applicable and target is not None:
                target_principal = _principal(target)
                detail = (
                    "No aplica: la regla depende del campo "
                    f"'{target_principal.nombre}', que fue dejado sin valor para "
                    f"incumplir intencionalmente la regla objetivo '{target.nombre}'."
                )
            elif target is not None and target.regla_id == rule.regla_id:
                detail = (
                    f"Regla objetivo del escenario {scenario}. "
                    f"{evaluation_detail}"
                )
            else:
                detail = evaluation_detail

            case_rule_rows.append(
                CaseRule(
                    caso_prueba_id=test_case.caso_prueba_id,
                    regla_id=rule.regla_id,
                    cumple_esperado=fulfilled,
                    detalle_esperado=detail,
                )
            )

    db.add_all(generated_rows)
    db.add_all(case_rule_rows)
    generation.estado = "COMPLETADA"
    # El commit de la ruta realizará el flush final en un único bloque.
    return generation
