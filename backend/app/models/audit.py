from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


PK_TYPE = BigInteger().with_variant(Integer, "sqlite")


class Audit(Base):
    __tablename__ = "auditoria"
    # Indentificar Auditoria  
    auditoria_id: Mapped[int] = mapped_column(
        PK_TYPE,
        primary_key=True,
        autoincrement=True,
    )
    # quien realizo el cambio
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.usuario_id"),
        nullable=False,
    )
    # qué tipo de elemento se modificó
    entidad_afectada: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    # que usuario fue  modificado
    registro_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    # estado antes del cambio
    estado_anterior: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    # estado después del cambio
    estado_nuevo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    # cuando ocurrio
    fecha_cambio: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )