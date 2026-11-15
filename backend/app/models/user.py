from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


PK_TYPE = BigInteger().with_variant(Integer, "sqlite")


class Role(Base):
    __tablename__ = "rol"

    rol_id: Mapped[int] = mapped_column(PK_TYPE, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    usuarios: Mapped[list["User"]] = relationship(back_populates="rol")


class User(Base):
    __tablename__ = "usuario"

    usuario_id: Mapped[int] = mapped_column(PK_TYPE, primary_key=True, autoincrement=True)
    rol_id: Mapped[int] = mapped_column(ForeignKey("rol.rol_id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    rol: Mapped[Role] = relationship(back_populates="usuarios")
