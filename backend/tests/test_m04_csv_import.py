# ============================================================
# CREACIÓN 2026-11-20 - M04 / CP-09
# Pruebas de integración HU-08 / RF13 + revalidación RF14 con origen CSV.
# Validan estructura, vista previa, filas inválidas, importación parcial,
# clasificación automática y persistencia con origen_registro=CSV.
# ============================================================

from tests.test_m03_generation import _headers
from tests.test_m04_execution import _create_generation


def _csv_file(content: str, name: str = "resultados.csv"):
    return {"file": (name, content.encode("utf-8"), "text/csv")}


def test_csv_validate_accepts_defined_structure_and_calculates_status(client):
    headers = _headers(client)
    generation = _create_generation(client, headers, "VALIDO", 1)
    case_id = generation["casos"][0]["caso_prueba_id"]

    csv_text = (
        "caso_prueba_id,resultado_obtenido,bloqueado,observacion,fecha_ejecucion\n"
        f"{case_id},Aceptado,false,Resultado correcto,2026-11-20T21:30:00\n"
    )
    response = client.post(
        "/api/execution-imports/csv/validate",
        headers=headers,
        files=_csv_file(csv_text),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["estructura_valida"] is True
    assert body["filas_validas"] == 1
    assert body["filas_invalidas"] == 0
    assert body["filas"][0]["estado_calculado"] == "APROBADO"


def test_csv_validate_reports_missing_columns_without_persisting(client):
    headers = _headers(client)
    csv_text = "caso_prueba_id,resultado_obtenido\n1,Aceptado\n"
    response = client.post(
        "/api/execution-imports/csv/validate",
        headers=headers,
        files=_csv_file(csv_text),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["estructura_valida"] is False
    assert any("Faltan columnas obligatorias" in msg for msg in body["errores_generales"])


def test_csv_validate_identifies_unknown_case(client):
    headers = _headers(client)
    csv_text = (
        "caso_prueba_id,resultado_obtenido,bloqueado,observacion,fecha_ejecucion\n"
        "999999,Aceptado,false,Caso inexistente,2026-11-20T21:30:00\n"
    )
    response = client.post(
        "/api/execution-imports/csv/validate",
        headers=headers,
        files=_csv_file(csv_text),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["filas_validas"] == 0
    assert body["filas_invalidas"] == 1
    assert "El caso de prueba no existe." in body["filas"][0]["errores"]


def test_csv_import_persists_only_valid_rows_and_marks_origin_csv(client):
    headers = _headers(client)
    generation = _create_generation(client, headers, "VALIDO", 2)
    case_1 = generation["casos"][0]["caso_prueba_id"]
    case_2 = generation["casos"][1]["caso_prueba_id"]

    csv_text = (
        "caso_prueba_id,resultado_obtenido,bloqueado,observacion,fecha_ejecucion\n"
        f"{case_1},Aceptado,false,Debe aprobar,2026-11-20T21:30:00\n"
        f"{case_2},Rechazado,false,Debe fallar,2026-11-20T21:31:00\n"
        "999999,Aceptado,false,Caso inexistente,2026-11-20T21:32:00\n"
    )
    response = client.post(
        "/api/execution-imports/csv/import",
        headers=headers,
        files=_csv_file(csv_text),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["importadas"] == 2
    assert body["omitidas"] == 1
    assert {item["origen_registro"] for item in body["ejecuciones"]} == {"CSV"}
    assert [item["estado"] for item in body["ejecuciones"]] == ["APROBADO", "FALLIDO"]

    approved = client.get(
        "/api/execution-cases",
        headers=headers,
        params={"estado": "APROBADO"},
    )
    assert approved.status_code == 200
    assert any(row["caso_prueba_id"] == case_1 and row["origen_registro"] == "CSV" for row in approved.json())


def test_csv_import_supports_blocked_row_with_required_observation(client):
    headers = _headers(client)
    generation = _create_generation(client, headers, "INVALIDO", 1)
    case_id = generation["casos"][0]["caso_prueba_id"]

    csv_text = (
        "caso_prueba_id,resultado_obtenido,bloqueado,observacion,fecha_ejecucion\n"
        f"{case_id},,true,Ambiente externo no disponible,2026-11-20T21:35:00\n"
    )
    response = client.post(
        "/api/execution-imports/csv/import",
        headers=headers,
        files=_csv_file(csv_text),
    )
    assert response.status_code == 201, response.text
    item = response.json()["ejecuciones"][0]
    assert item["estado"] == "BLOQUEADO"
    assert item["resultado_obtenido"] is None
    assert item["origen_registro"] == "CSV"


def test_csv_import_rejects_file_without_any_valid_rows(client):
    headers = _headers(client)
    csv_text = (
        "caso_prueba_id,resultado_obtenido,bloqueado,observacion,fecha_ejecucion\n"
        "999999,Aceptado,false,Caso inexistente,2026-11-20T21:40:00\n"
    )
    response = client.post(
        "/api/execution-imports/csv/import",
        headers=headers,
        files=_csv_file(csv_text),
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "El archivo no contiene filas válidas para importar."
