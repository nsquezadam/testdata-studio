from __future__ import annotations

# ============================================================
# CREACIÓN 2026-11-18 - M03 / CP-06
# Modelos de persistencia para Generación de Datos y Escenarios.
# Se implementan las tablas definidas en el diseño del proyecto:
# generacion, caso_prueba, caso_regla y dato_generado.
# Motivo: conservar trazabilidad entre modelo, reglas, escenarios,
# datos generados y resultado esperado (RF08, RF09 y RF10).
# ============================================================

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


PK_TYPE = BigInteger().with_variant(Integer, "sqlite")


class Generation(Base):
    __tablename__ = "generacion"
    __table_args__ = (
        CheckConstraint("cantidad_solicitada > 0", name="chk_generacion_cantidad_positiva"),
    )

    generacion_id: Mapped[int] = mapped_column(
        PK_TYPE,
        primary_key=True,
        autoincrement=True,
    )
    modelo_id: Mapped[int] = mapped_column(
        ForeignKey("modelo.modelo_id"),
        nullable=False,
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.usuario_id"),
        nullable=False,
    )
    cantidad_solicitada: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_generacion: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    estado: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        server_default=text("'PENDIENTE'"),
    )


class TestCase(Base):
    __tablename__ = "caso_prueba"
    __table_args__ = (
        CheckConstraint(
            "tipo_escenario IN ('VALIDO','INVALIDO','LIMITE')",
            name="chk_caso_prueba_tipo_escenario",
        ),
    )

    caso_prueba_id: Mapped[int] = mapped_column(
        PK_TYPE,
        primary_key=True,
        autoincrement=True,
    )
    generacion_id: Mapped[int] = mapped_column(
        ForeignKey("generacion.generacion_id"),
        nullable=False,
    )
    tipo_escenario: Mapped[str] = mapped_column(String(20), nullable=False)
    resultado_esperado: Mapped[str] = mapped_column(String(500), nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class CaseRule(Base):
    __tablename__ = "caso_regla"

    caso_prueba_id: Mapped[int] = mapped_column(
        ForeignKey("caso_prueba.caso_prueba_id"),
        primary_key=True,
    )
    regla_id: Mapped[int] = mapped_column(
        ForeignKey("regla.regla_id"),
        primary_key=True,
    )
    cumple_esperado: Mapped[bool] = mapped_column(Boolean, nullable=False)
    detalle_esperado: Mapped[str | None] = mapped_column(String(500), nullable=True)


class GeneratedData(Base):
    __tablename__ = "dato_generado"
    __table_args__ = (
        UniqueConstraint(
            "caso_prueba_id",
            "campo_id",
            name="uq_dato_generado_caso_campo",
        ),
    )

    dato_generado_id: Mapped[int] = mapped_column(
        PK_TYPE,
        primary_key=True,
        autoincrement=True,
    )
    caso_prueba_id: Mapped[int] = mapped_column(
        ForeignKey("caso_prueba.caso_prueba_id"),
        nullable=False,
    )
    campo_id: Mapped[int] = mapped_column(
        ForeignKey("campo.campo_id"),
        nullable=False,
    )
    valor_generado: Mapped[str | None] = mapped_column(Text, nullable=True)
