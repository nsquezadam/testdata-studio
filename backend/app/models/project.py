from __future__ import annotations

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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


PK_TYPE = BigInteger().with_variant(Integer, "sqlite")


class Project(Base):
    __tablename__ = "proyecto"

    proyecto_id: Mapped[int] = mapped_column(
        PK_TYPE,
        primary_key=True,
        autoincrement=True,
    )

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.usuario_id"),
        nullable=False,
    )

    nombre: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    descripcion: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

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

    modelos: Mapped[list["DataModel"]] = relationship(
        back_populates="proyecto",
        cascade="save-update, merge",
    )


class DataModel(Base):
    __tablename__ = "modelo"

    __table_args__ = (
        UniqueConstraint(
            "proyecto_id",
            "nombre",
            name="uq_modelo_proyecto_nombre",
        ),
    )

    modelo_id: Mapped[int] = mapped_column(
        PK_TYPE,
        primary_key=True,
        autoincrement=True,
    )

    proyecto_id: Mapped[int] = mapped_column(
        ForeignKey("proyecto.proyecto_id"),
        nullable=False,
    )

    nombre: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    descripcion: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

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

    proyecto: Mapped["Project"] = relationship(
        back_populates="modelos",
    )