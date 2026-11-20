from __future__ import annotations

# ============================================================
# CREACIÓN 2026-11-18 - M03 / CP-06
# Contratos REST del módulo Generación de Datos y Escenarios.
# Motivo: exponer selección de escenario/cantidad y devolver la
# trazabilidad completa regla -> escenario -> dato -> resultado esperado.
#
# MODIFICACIÓN 2026-11-19 - M03 / CP-06 - TRAZABILIDAD ENRIQUECIDA
# Se agregan campos y parámetros dentro de cada regla evaluada.
# Motivo: permitir comprobar desde el JSON qué configuración se evaluó,
# qué valores generados participaron y por qué la regla cumple/no cumple.
# ============================================================

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ScenarioType = Literal["VALIDO", "INVALIDO", "LIMITE"]


class GenerationCreate(BaseModel):
    modelo_id: int = Field(gt=0)
    cantidad_solicitada: int = Field(ge=1, le=100)
    tipo_escenario: ScenarioType


class GenerationReadinessResponse(BaseModel):
    modelo_id: int
    modelo_nombre: str
    proyecto_id: int
    proyecto_nombre: str
    campos_activos: int
    reglas_activas: int
    reglas_limite: int
    listo: bool
    observaciones: list[str]


class GeneratedDataResponse(BaseModel):
    dato_generado_id: int
    campo_id: int
    campo_nombre: str
    tipo_dato_codigo: str
    valor_generado: str | None


class RuleTraceFieldResponse(BaseModel):
    campo_id: int
    campo_nombre: str
    tipo_dato_codigo: str
    rol_campo: str
    valor_generado: str | None


class RuleTraceParameterResponse(BaseModel):
    parametro_id: int
    clave: str
    valor: str
    orden: int | None


class CaseRuleResponse(BaseModel):
    regla_id: int
    regla_nombre: str
    tipo_regla_codigo: str
    campos: list[RuleTraceFieldResponse]
    parametros: list[RuleTraceParameterResponse]
    cumple_esperado: bool
    detalle_esperado: str | None


class TestCaseResponse(BaseModel):
    caso_prueba_id: int
    tipo_escenario: ScenarioType
    resultado_esperado: str
    fecha_creacion: datetime
    regla_objetivo_id: int | None = None
    regla_objetivo_nombre: str | None = None
    datos: list[GeneratedDataResponse]
    reglas: list[CaseRuleResponse]


class GenerationResponse(BaseModel):
    generacion_id: int
    modelo_id: int
    modelo_nombre: str
    proyecto_id: int
    proyecto_nombre: str
    usuario_id: int
    cantidad_solicitada: int
    tipo_escenario: ScenarioType
    fecha_generacion: datetime
    estado: str
    casos: list[TestCaseResponse]


class GenerationListItem(BaseModel):
    generacion_id: int
    modelo_id: int
    modelo_nombre: str
    proyecto_id: int
    proyecto_nombre: str
    cantidad_solicitada: int
    tipo_escenario: ScenarioType
    fecha_generacion: datetime
    estado: str
    total_casos: int
