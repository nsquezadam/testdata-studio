from __future__ import annotations

# ============================================================
# CREACIÓN 2026-11-20 - M04 / CP-09
# Validación previa e importación de resultados de ejecución mediante CSV.
# Motivo: implementar HU-08 / RF13 y reutilizar la clasificación de RF14.
# El archivo nunca define el estado final: TestData Studio lo calcula.
# ============================================================

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.routes.execution import _classify, _owned_case_context
from app.db import get_db
from app.models.execution import Execution
from app.models.user import User
from app.schemas.execution import (
    CsvExecutionImportResponse,
    CsvExecutionRowPreview,
    CsvExecutionValidationResponse,
    ExecutionResponse,
)


router = APIRouter(prefix="/execution-imports", tags=["Resultados y ejecución"])

REQUIRED_COLUMNS = [
    "caso_prueba_id",
    "resultado_obtenido",
    "bloqueado",
    "observacion",
    "fecha_ejecucion",
]
MAX_CSV_ROWS = 500
MAX_CSV_BYTES = 1024 * 1024


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "si", "sí", "yes", "s", "y"}:
        return True
    if normalized in {"false", "0", "no", "n", ""}:
        return False
    raise ValueError("bloqueado debe ser true/false, 1/0 o si/no.")


def _parse_datetime(value: str) -> datetime:
    raw = value.strip()
    if not raw:
        raise ValueError("fecha_ejecucion es obligatoria.")
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("fecha_ejecucion debe usar formato ISO, por ejemplo 2026-11-20T21:30:00.") from exc


def _decode_csv(content: bytes) -> str:
    if not content:
        raise HTTPException(status_code=422, detail="El archivo CSV está vacío.")
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(status_code=422, detail="El archivo CSV supera el máximo permitido de 1 MB.")
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="El archivo debe utilizar codificación UTF-8.") from exc


def _reader_from_text(text: str):
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","
    return csv.DictReader(io.StringIO(text), delimiter=delimiter)


def _validate_content(
    *,
    filename: str,
    content: bytes,
    db: Session,
    analyst: User,
) -> CsvExecutionValidationResponse:
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="Debe seleccionar un archivo con extensión .csv.")

    text = _decode_csv(content)
    reader = _reader_from_text(text)
    columns = [str(col or "").strip() for col in (reader.fieldnames or [])]
    missing = [column for column in REQUIRED_COLUMNS if column not in columns]
    unexpected = [column for column in columns if column and column not in REQUIRED_COLUMNS]

    general_errors: list[str] = []
    if missing:
        general_errors.append(f"Faltan columnas obligatorias: {', '.join(missing)}.")
    if unexpected:
        general_errors.append(
            "Existen columnas no contempladas en la estructura: " + ", ".join(unexpected) + "."
        )

    if general_errors:
        return CsvExecutionValidationResponse(
            archivo_nombre=filename,
            estructura_valida=False,
            columnas=columns,
            total_filas=0,
            filas_validas=0,
            filas_invalidas=0,
            errores_generales=general_errors,
            filas=[],
        )

    previews: list[CsvExecutionRowPreview] = []
    seen_case_ids: set[int] = set()

    for index, raw_row in enumerate(reader, start=2):
        if index > MAX_CSV_ROWS + 1:
            raise HTTPException(
                status_code=422,
                detail=f"El archivo supera el máximo de {MAX_CSV_ROWS} filas de datos.",
            )

        row = {str(key or "").strip(): _clean(value) for key, value in raw_row.items()}
        if not any(row.values()):
            continue

        errors: list[str] = []
        case_id: int | None = None
        blocked: bool | None = None
        executed_at: datetime | None = None
        expected: str | None = None

        try:
            case_id = int(row["caso_prueba_id"])
            if case_id <= 0:
                raise ValueError
        except (TypeError, ValueError):
            errors.append("caso_prueba_id debe ser un entero mayor que cero.")

        if case_id is not None:
            if case_id in seen_case_ids:
                errors.append("caso_prueba_id está duplicado dentro del archivo.")
            else:
                seen_case_ids.add(case_id)

            try:
                case, _, _, _ = _owned_case_context(db, case_id, analyst)
                expected = case.resultado_esperado
            except HTTPException as exc:
                if exc.status_code == 404:
                    errors.append("El caso de prueba no existe.")
                elif exc.status_code == 403:
                    errors.append("El caso de prueba no pertenece al usuario autenticado.")
                else:
                    errors.append("No fue posible validar el caso de prueba.")

        try:
            blocked = _parse_bool(row["bloqueado"])
        except ValueError as exc:
            errors.append(str(exc))

        try:
            executed_at = _parse_datetime(row["fecha_ejecucion"])
        except ValueError as exc:
            errors.append(str(exc))

        observed = row["resultado_obtenido"] or None
        note = row["observacion"] or None

        if blocked is True:
            if not note:
                errors.append("La observación es obligatoria cuando bloqueado=true.")
        elif blocked is False and not observed:
            errors.append("resultado_obtenido es obligatorio cuando la ejecución no está bloqueada.")

        calculated_status = None
        if not errors and expected is not None and blocked is not None:
            calculated_status = _classify(expected, observed, blocked)

        previews.append(
            CsvExecutionRowPreview(
                fila=index,
                caso_prueba_id=case_id,
                resultado_obtenido=observed,
                bloqueado=blocked,
                observacion=note,
                fecha_ejecucion=executed_at,
                estado_calculado=calculated_status,
                valida=not errors,
                errores=errors,
            )
        )

    if not previews:
        general_errors.append("El archivo no contiene filas de datos.")

    valid_count = sum(1 for row in previews if row.valida)
    invalid_count = len(previews) - valid_count
    return CsvExecutionValidationResponse(
        archivo_nombre=filename,
        estructura_valida=not general_errors,
        columnas=columns,
        total_filas=len(previews),
        filas_validas=valid_count,
        filas_invalidas=invalid_count,
        errores_generales=general_errors,
        filas=previews,
    )


async def _read_upload(file: UploadFile) -> tuple[str, bytes]:
    filename = (file.filename or "resultados.csv").strip() or "resultados.csv"
    content = await file.read()
    return filename, content


@router.post("/csv/validate", response_model=CsvExecutionValidationResponse)
async def validate_execution_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    analyst: User = Depends(require_roles("Analista/Tester")),
):
    filename, content = await _read_upload(file)
    return _validate_content(filename=filename, content=content, db=db, analyst=analyst)


@router.post(
    "/csv/import",
    response_model=CsvExecutionImportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_execution_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    analyst: User = Depends(require_roles("Analista/Tester")),
):
    filename, content = await _read_upload(file)
    validation = _validate_content(filename=filename, content=content, db=db, analyst=analyst)

    if not validation.estructura_valida:
        raise HTTPException(status_code=422, detail="La estructura del CSV no es válida.")
    valid_rows = [row for row in validation.filas if row.valida]
    invalid_rows = [row for row in validation.filas if not row.valida]
    if not valid_rows:
        raise HTTPException(status_code=422, detail="El archivo no contiene filas válidas para importar.")

    created: list[Execution] = []
    for row in valid_rows:
        execution = Execution(
            caso_prueba_id=row.caso_prueba_id,
            usuario_id=analyst.usuario_id,
            origen_registro="CSV",
            resultado_obtenido=row.resultado_obtenido,
            estado=row.estado_calculado,
            observacion=row.observacion,
            fecha_ejecucion=row.fecha_ejecucion,
        )
        db.add(execution)
        created.append(execution)

    db.commit()
    for execution in created:
        db.refresh(execution)

    return CsvExecutionImportResponse(
        archivo_nombre=filename,
        total_filas=validation.total_filas,
        importadas=len(created),
        omitidas=len(invalid_rows),
        ejecuciones=[
            ExecutionResponse(
                ejecucion_id=item.ejecucion_id,
                caso_prueba_id=item.caso_prueba_id,
                usuario_id=item.usuario_id,
                origen_registro=item.origen_registro,
                resultado_obtenido=item.resultado_obtenido,
                estado=item.estado,
                observacion=item.observacion,
                fecha_ejecucion=item.fecha_ejecucion,
                fecha_registro=item.fecha_registro,
            )
            for item in created
        ],
        filas_omitidas=invalid_rows,
    )
