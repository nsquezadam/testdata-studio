from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# ============================================================
# PROYECTOS
# ============================================================

class ProjectCreate(BaseModel):
    nombre: str = Field(
        min_length=2,
        max_length=120,
    )

    descripcion: str | None = Field(
        default=None,
        max_length=500,
    )


class ProjectUpdate(BaseModel):
    nombre: str = Field(
        min_length=2,
        max_length=120,
    )

    descripcion: str | None = Field(
        default=None,
        max_length=500,
    )


class ProjectStatusUpdate(BaseModel):
    estado: bool


class ProjectResponse(BaseModel):
    proyecto_id: int
    usuario_id: int
    nombre: str
    descripcion: str | None
    estado: bool
    fecha_creacion: datetime
    cantidad_modelos: int = 0


# ============================================================
# MODELOS
# ============================================================

class DataModelCreate(BaseModel):
    nombre: str = Field(
        min_length=2,
        max_length=120,
    )

    descripcion: str | None = Field(
        default=None,
        max_length=500,
    )


class DataModelUpdate(BaseModel):
    nombre: str = Field(
        min_length=2,
        max_length=120,
    )

    descripcion: str | None = Field(
        default=None,
        max_length=500,
    )


class DataModelStatusUpdate(BaseModel):
    estado: bool


class DataModelResponse(BaseModel):
    modelo_id: int
    proyecto_id: int
    nombre: str
    descripcion: str | None
    estado: bool
    fecha_creacion: datetime