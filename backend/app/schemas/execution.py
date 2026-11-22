from __future__ import annotations

# ============================================================
# CREACIÓN 2026-11-20 - M04 / CP-08
# Contratos REST para consulta y registro manual de resultados.
# Motivo: implementar HU-07 / RF12 y clasificación inicial de RF14.
# ============================================================

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


ExecutionStatus = Literal["PENDIENTE", "APROBADO", "FALLIDO", "BLOQUEADO"]
StoredExecutionStatus = Literal["APROBADO", "FALLIDO", "BLOQUEADO"]


class ExecutionCreate(BaseModel):
    resultado_obtenido: str | None = Field(default=None, max_length=2000)
    bloqueado: bool = False
    observacion: str | None = Field(default=None, max_length=1000)
    fecha_ejecucion: datetime

    @model_validator(mode="after")
    def validate_execution(self):
        result = (self.resultado_obtenido or "").strip()
        note = (self.observacion or "").strip()
        if self.bloqueado:
            if not note:
                raise ValueError("Debe indicar una observación para registrar una ejecución bloqueada.")
        elif not result:
            raise ValueError("Debe informar el resultado obtenido.")
        return self


class ExecutionDataItem(BaseModel):
    campo_id: int
    campo_nombre: str
    tipo_dato_codigo: str
    valor_generado: str | None


class ExecutionResponse(BaseModel):
    ejecucion_id: int
    caso_prueba_id: int
    usuario_id: int
    origen_registro: Literal["MANUAL", "CSV"]
    resultado_obtenido: str | None
    estado: StoredExecutionStatus
    observacion: str | None
    fecha_ejecucion: datetime
    fecha_registro: datetime


class ExecutionCaseListItem(BaseModel):
    caso_prueba_id: int
    generacion_id: int
    proyecto_id: int
    proyecto_nombre: str
    modelo_id: int
    modelo_nombre: str
    tipo_escenario: Literal["VALIDO", "INVALIDO", "LIMITE"]
    resultado_esperado: str
    estado: ExecutionStatus
    origen_registro: Literal["MANUAL", "CSV"] | None = None
    resultado_obtenido: str | None = None
    fecha_ejecucion: datetime | None = None
    # Último guardado en la plataforma (distinto de la fecha externa de ejecución).
    fecha_registro: datetime | None = None
    ejecucion_id: int | None = None


# MODIFICACIÓN 2026-11-21 - M04 / CP-08 / CP-10
# Respuesta paginada y opciones de filtro de todos los casos del usuario.
class ExecutionFilterOption(BaseModel):
    proyecto_id: int
    proyecto_nombre: str
    modelo_id: int
    modelo_nombre: str


class ExecutionCasePage(BaseModel):
    items: list[ExecutionCaseListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    opciones: list[ExecutionFilterOption]


class ExecutionCaseDetail(ExecutionCaseListItem):
    datos: list[ExecutionDataItem]
    observacion: str | None = None

# ============================================================
# CREACIÓN 2026-11-20 - M04 / CP-09
# Contratos para validación previa e importación de resultados por CSV.
# Motivo: implementar HU-08 / RF13 sin permitir que el archivo defina
# directamente el estado final; la clasificación continúa siendo responsabilidad
# de TestData Studio (RF14).
# ============================================================

class CsvExecutionRowPreview(BaseModel):
    fila: int
    caso_prueba_id: int | None = None
    resultado_obtenido: str | None = None
    bloqueado: bool | None = None
    observacion: str | None = None
    fecha_ejecucion: datetime | None = None
    estado_calculado: StoredExecutionStatus | None = None
    valida: bool
    errores: list[str] = Field(default_factory=list)


class CsvExecutionValidationResponse(BaseModel):
    archivo_nombre: str
    estructura_valida: bool
    columnas: list[str]
    total_filas: int
    filas_validas: int
    filas_invalidas: int
    errores_generales: list[str] = Field(default_factory=list)
    filas: list[CsvExecutionRowPreview] = Field(default_factory=list)


class CsvExecutionImportResponse(BaseModel):
    archivo_nombre: str
    total_filas: int
    importadas: int
    omitidas: int
    ejecuciones: list[ExecutionResponse] = Field(default_factory=list)
    filas_omitidas: list[CsvExecutionRowPreview] = Field(default_factory=list)
