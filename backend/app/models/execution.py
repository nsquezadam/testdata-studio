from __future__ import annotations

# ============================================================
# CREACIÓN 2026-11-20 - M04 / CP-08
# Persistencia de resultados obtenidos durante ejecuciones externas.
# Motivo: implementar HU-07 / RF12 y preparar la comparación de RF14.
# TestData Studio no ejecuta pruebas externas; solo registra su resultado.
# ============================================================

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


PK_TYPE = BigInteger().with_variant(Integer, "sqlite")


class Execution(Base):
    __tablename__ = "ejecucion"
    __table_args__ = (
        CheckConstraint(
            "origen_registro IN ('MANUAL','CSV')",
            name="chk_ejecucion_origen_registro",
        ),
        CheckConstraint(
            "estado IN ('APROBADO','FALLIDO','BLOQUEADO')",
            name="chk_ejecucion_estado",
        ),
    )

    ejecucion_id: Mapped[int] = mapped_column(
        PK_TYPE,
        primary_key=True,
        autoincrement=True,
    )
    caso_prueba_id: Mapped[int] = mapped_column(
        ForeignKey("caso_prueba.caso_prueba_id"),
        nullable=False,
        index=True,
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.usuario_id"),
        nullable=False,
    )
    origen_registro: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'MANUAL'"),
    )
    resultado_obtenido: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    observacion: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    fecha_ejecucion: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
