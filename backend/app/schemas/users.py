from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rol_id: int
    nombre: str
    descripcion: str | None = None
    estado: bool


class UserCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    apellido: str = Field(min_length=2, max_length=100)
    email: str = Field(
        min_length=5,
        max_length=150,
        pattern=EMAIL_PATTERN,
    )
    password: str = Field(min_length=8, max_length=200)
    rol_id: int = Field(gt=0)


class UserUpdate(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    apellido: str = Field(min_length=2, max_length=100)
    email: str = Field(
        min_length=5,
        max_length=150,
        pattern=EMAIL_PATTERN,
    )
    rol_id: int = Field(gt=0)

    # Si se deja null, conserva la contraseña actual.
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=200,
    )


class UserStatusUpdate(BaseModel):
    estado: bool


class UserResponse(BaseModel):
    usuario_id: int
    nombre: str
    apellido: str
    email: str
    rol_id: int
    rol: str
    estado: bool
    fecha_creacion: datetime