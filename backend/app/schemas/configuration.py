# ============================================================
# MODIFICACIÓN 2026-11-18 - INC-03 / CATÁLOGOS M02
# Se separan las respuestas de catálogo de tipos de dato y tipos de regla
# para devolver sus identificadores reales: tipo_dato_id y tipo_regla_id.
# Motivo: el frontend esperaba esos nombres y el formato genérico "id"
# provocaba key indefinida en React y tipo_dato_id nulo al crear campos.
# Se conserva CatalogResponse temporalmente por compatibilidad interna.
# ============================================================

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CatalogResponse(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str | None
    estado: bool


class DataTypeCatalogResponse(BaseModel):
    tipo_dato_id: int
    codigo: str
    nombre: str
    descripcion: str | None
    estado: bool


class RuleTypeCatalogResponse(BaseModel):
    tipo_regla_id: int
    codigo: str
    nombre: str
    descripcion: str | None
    estado: bool


class DataFieldCreate(BaseModel):
    tipo_dato_id: int = Field(gt=0)
    nombre: str = Field(min_length=2, max_length=100)
    descripcion: str | None = Field(default=None, max_length=250)
    orden: int | None = Field(default=None, ge=1)


class DataFieldUpdate(DataFieldCreate):
    pass


class DataFieldStatusUpdate(BaseModel):
    estado: bool


class DataFieldResponse(BaseModel):
    campo_id: int
    modelo_id: int
    tipo_dato_id: int
    tipo_dato_codigo: str
    tipo_dato_nombre: str
    nombre: str
    descripcion: str | None
    orden: int | None
    estado: bool


class RuleFieldInput(BaseModel):
    campo_id: int = Field(gt=0)
    rol_campo: str = Field(min_length=2, max_length=30)


class RuleParameterInput(BaseModel):
    clave: str = Field(min_length=1, max_length=50)
    valor: str = Field(min_length=1, max_length=500)
    orden: int | None = Field(default=None, ge=1)


class BusinessRuleCreate(BaseModel):
    tipo_regla_id: int = Field(gt=0)
    nombre: str = Field(min_length=2, max_length=150)
    descripcion: str | None = Field(default=None, max_length=500)
    campos: list[RuleFieldInput] = Field(min_length=1)
    parametros: list[RuleParameterInput] = Field(default_factory=list)


class BusinessRuleUpdate(BusinessRuleCreate):
    pass


class BusinessRuleStatusUpdate(BaseModel):
    estado: bool


class RuleFieldResponse(BaseModel):
    campo_id: int
    campo_nombre: str
    tipo_dato_codigo: str
    rol_campo: str


class RuleParameterResponse(BaseModel):
    parametro_id: int
    clave: str
    valor: str
    orden: int | None


class BusinessRuleResponse(BaseModel):
    regla_id: int
    modelo_id: int
    tipo_regla_id: int
    tipo_regla_codigo: str
    tipo_regla_nombre: str
    nombre: str
    descripcion: str | None
    estado: bool
    fecha_creacion: datetime
    campos: list[RuleFieldResponse]
    parametros: list[RuleParameterResponse]
