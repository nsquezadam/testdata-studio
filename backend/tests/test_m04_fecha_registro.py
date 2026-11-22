# MODIFICACIÓN 2026-11-22 - M04 / CP-08 y CP-09
# Nuevas pruebas de fecha_registro sin modificar los tests anteriores.
from tests.test_m03_generation import _headers
from tests.test_m04_execution import _create_generation


# MODIFICACIÓN 2026-11-22 - M04 / CP-08: fecha del último registro
# Un retest crea un nuevo histórico, aun cuando la fecha real de ejecución
# declarada por el usuario sea anterior a la del primer intento.
def test_execution_case_shows_latest_registration_without_changing_execution_date(client):
    headers = _headers(client)
    generation = _create_generation(client, headers, "VALIDO", 1)
    case_id = generation["casos"][0]["caso_prueba_id"]

    def register(result, executed_at):
        response = client.post(
            f"/api/execution-cases/{case_id}/executions",
            headers=headers,
            json={
                "resultado_obtenido": result,
                "bloqueado": False,
                "observacion": "Retest de visualización de fechas",
                "fecha_ejecucion": executed_at,
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    first = register("Rechazado", "2026-11-21T10:30:00")
    second = register("Aceptado", "2026-11-20T09:00:00")
    assert second["ejecucion_id"] > first["ejecucion_id"]
    assert first["fecha_registro"] is not None
    assert second["fecha_registro"] is not None

    list_response = client.get("/api/execution-cases/page?page=1&page_size=50", headers=headers)
    assert list_response.status_code == 200, list_response.text
    row = next(x for x in list_response.json()["items"] if x["caso_prueba_id"] == case_id)
    assert row["ejecucion_id"] == second["ejecucion_id"]
    assert row["estado"] == "APROBADO"
    assert row["fecha_ejecucion"] == second["fecha_ejecucion"]
    assert row["fecha_registro"] == second["fecha_registro"]

    detail_response = client.get(f"/api/execution-cases/{case_id}", headers=headers)
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["fecha_registro"] == second["fecha_registro"]

    historical = client.get(f"/api/executions/{first['ejecucion_id']}", headers=headers)
    assert historical.status_code == 200, historical.text
    assert historical.json()["fecha_ejecucion"] == first["fecha_ejecucion"]
    assert historical.json()["fecha_registro"] == first["fecha_registro"]


def test_csv_import_lists_platform_registration_and_preserves_csv_execution_date(client):
    headers = _headers(client)
    generation = _create_generation(client, headers, "VALIDO", 1)
    case_id = generation["casos"][0]["caso_prueba_id"]
    csv = (
        "caso_prueba_id,resultado_obtenido,bloqueado,observacion,fecha_ejecucion\n"
        f"{case_id},Aceptado,false,Importacion posterior,2026-11-19T20:00:00\n"
    )
    response = client.post(
        "/api/execution-imports/csv/import",
        headers=headers,
        files={"file": ("resultados.csv", csv.encode("utf-8"), "text/csv")},
    )
    assert response.status_code == 201, response.text
    saved = response.json()["ejecuciones"][0]
    assert saved["fecha_registro"]
    assert saved["fecha_ejecucion"].startswith("2026-11-19T20:00:00")

    page = client.get("/api/execution-cases/page", headers=headers)
    assert page.status_code == 200, page.text
    row = next(x for x in page.json()["items"] if x["caso_prueba_id"] == case_id)
    assert row["fecha_registro"] == saved["fecha_registro"]
    assert row["fecha_ejecucion"] == saved["fecha_ejecucion"]
    assert row["origen_registro"] == "CSV"
