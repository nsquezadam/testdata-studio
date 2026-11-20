from __future__ import annotations

# ============================================================
# MODIFICACIÓN 2026-11-18 - INC-02
# Se agrega la restricción lógica (modelo_id, orden) única para CAMPO.
# Además se mantienen alias de compatibilidad con la nomenclatura usada
# en una versión anterior de M02 (FieldDefinition / Rule), evitando que
# una actualización parcial de archivos impida iniciar el backend.
# ============================================================

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


PK_TYPE = BigInteger().with_variant(Integer, "sqlite")


class DataType(Base):
    __tablename__ = "tipo_dato"

    tipo_dato_id: Mapped[int] = mapped_column(
        PK_TYPE,
        primary_key=True,
        autoincrement=True,
    )
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    estado: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )


class DataField(Base):
    __tablename__ = "campo"
    __table_args__ = (
        UniqueConstraint(
            "modelo_id",
            "nombre",
            name="uq_campo_modelo_nombre",
        ),
        UniqueConstraint(
            "modelo_id",
            "orden",
            name="uq_campo_modelo_orden",
        ),
    )

    campo_id: Mapped[int] = mapped_column(
        PK_TYPE,
        primary_key=True,
        autoincrement=True,
    )
    modelo_id: Mapped[int] = mapped_column(
        ForeignKey("modelo.modelo_id"),
        nullable=False,
    )
    tipo_dato_id: Mapped[int] = mapped_column(
        ForeignKey("tipo_dato.tipo_dato_id"),
        nullable=False,
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(250), nullable=True)
    orden: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estado: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )


class RuleType(Base):
    __tablename__ = "tipo_regla"

    tipo_regla_id: Mapped[int] = mapped_column(
        PK_TYPE,
        primary_key=True,
        autoincrement=True,
    )
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(300), nullable=True)
    estado: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )


class BusinessRule(Base):
    __tablename__ = "regla"
    __table_args__ = (
        UniqueConstraint(
            "modelo_id",
            "nombre",
            name="uq_regla_modelo_nombre",
        ),
    )

    regla_id: Mapped[int] = mapped_column(
        PK_TYPE,
        primary_key=True,
        autoincrement=True,
    )
    modelo_id: Mapped[int] = mapped_column(
        ForeignKey("modelo.modelo_id"),
        nullable=False,
    )
    tipo_regla_id: Mapped[int] = mapped_column(
        ForeignKey("tipo_regla.tipo_regla_id"),
        nullable=False,
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    estado: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class RuleField(Base):
    __tablename__ = "regla_campo"

    regla_id: Mapped[int] = mapped_column(
        ForeignKey("regla.regla_id"),
        primary_key=True,
    )
    campo_id: Mapped[int] = mapped_column(
        ForeignKey("campo.campo_id"),
        primary_key=True,
    )
    rol_campo: Mapped[str] = mapped_column(
        String(30),
        primary_key=True,
    )


class RuleParameter(Base):
    __tablename__ = "regla_parametro"

    parametro_id: Mapped[int] = mapped_column(
        PK_TYPE,
        primary_key=True,
        autoincrement=True,
    )
    regla_id: Mapped[int] = mapped_column(
        ForeignKey("regla.regla_id"),
        nullable=False,
    )
    clave: Mapped[str] = mapped_column(String(50), nullable=False)
    valor: Mapped[str] = mapped_column(String(500), nullable=False)
    orden: Mapped[int | None] = mapped_column(Integer, nullable=True)

# ============================================================
# COMPATIBILIDAD TEMPORAL - 2026-11-18
# Nombres utilizados en la primera versión de M02. No crean modelos
# adicionales: son alias de las clases actuales para permitir una
# transición segura entre versiones del proyecto.
# ============================================================ 
FieldDefinition = DataField
Rule = BusinessRule

