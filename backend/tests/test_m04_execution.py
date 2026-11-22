# ============================================================
# CREACIÓN 2026-11-20 - M04 / CP-08
# Pruebas de integración para HU-07 / RF12 y clasificación base RF14.
# Validan estado PENDIENTE, detalle, APROBADO, FALLIDO, BLOQUEADO,
# obligatoriedad y rechazo de casos inexistentes.
# ============================================================

from tests.test_m03_generation import _configure_six_rules, _headers


def _create_generation(client, headers, scenario="VALIDO", amount=1):
    model_id = _configure_six_rules(client, headers)
    response = client.post(
        "/api/generations",
        headers=headers,
        json={
            "modelo_id": model_id,
            "cantidad_solicitada": amount,
            "tipo_escenario": scenario,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_execution_case_starts_pending(client):
    headers = _headers(client)
    generation = _create_generation(client, headers, "VALIDO", 1)
    case_id = generation["casos"][0]["caso_prueba_id"]

    response = client.get("/api/execution-cases", headers=headers)
    assert response.status_code == 200
    item = next(row for row in response.json() if row["caso_prueba_id"] == case_id)
    assert item["estado"] == "PENDIENTE"
    assert item["resultado_obtenido"] is None
    assert item["origen_registro"] is None


def test_execution_case_detail_includes_generated_data(client):
    headers = _headers(client)
    generation = _create_generation(client, headers, "VALIDO", 1)
    case_id = generation["casos"][0]["caso_prueba_id"]

    response = client.get(f"/api/execution-cases/{case_id}", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["caso_prueba_id"] == case_id
    assert body["estado"] == "PENDIENTE"
    assert len(body["datos"]) >= 1
    assert body["resultado_esperado"].startswith("Aceptar")


def test_manual_execution_is_approved_when_semantic_result_matches(client):
    headers = _headers(client)
    generation = _create_generation(client, headers, "VALIDO", 1)
    case_id = generation["casos"][0]["caso_prueba_id"]

    response = client.post(
        f"/api/execution-cases/{case_id}/executions",
        headers=headers,
        json={
            "resultado_obtenido": "Aceptado",
            "bloqueado": False,
            "observacion": "La aplicación externa aceptó los datos.",
            "fecha_ejecucion": "2026-11-20T18:30:00",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["estado"] == "APROBADO"
    assert response.json()["origen_registro"] == "MANUAL"

    detail = client.get(f"/api/execution-cases/{case_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["estado"] == "APROBADO"
    assert detail.json()["resultado_obtenido"] == "Aceptado"


def test_manual_execution_is_failed_when_result_differs(client):
    headers = _headers(client)
    generation = _create_generation(client, headers, "VALIDO", 1)
    case_id = generation["casos"][0]["caso_prueba_id"]

    response = client.post(
        f"/api/execution-cases/{case_id}/executions",
        headers=headers,
        json={
            "resultado_obtenido": "Rechazado",
            "bloqueado": False,
            "observacion": "El sistema externo rechazó el registro.",
            "fecha_ejecucion": "2026-11-20T18:35:00",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["estado"] == "FALLIDO"


def test_manual_execution_can_be_blocked(client):
    headers = _headers(client)
    generation = _create_generation(client, headers, "INVALIDO", 1)
    case_id = generation["casos"][0]["caso_prueba_id"]

    response = client.post(
        f"/api/execution-cases/{case_id}/executions",
        headers=headers,
        json={
            "resultado_obtenido": None,
            "bloqueado": True,
            "observacion": "El ambiente externo no se encontraba disponible.",
            "fecha_ejecucion": "2026-11-20T18:40:00",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["estado"] == "BLOQUEADO"
    assert response.json()["resultado_obtenido"] is None


def test_manual_execution_requires_result_or_block_reason(client):
    headers = _headers(client)
    generation = _create_generation(client, headers, "VALIDO", 1)
    case_id = generation["casos"][0]["caso_prueba_id"]

    missing_result = client.post(
        f"/api/execution-cases/{case_id}/executions",
        headers=headers,
        json={
            "resultado_obtenido": "",
            "bloqueado": False,
            "observacion": "",
            "fecha_ejecucion": "2026-11-20T18:45:00",
        },
    )
    assert missing_result.status_code == 422

    blocked_without_note = client.post(
        f"/api/execution-cases/{case_id}/executions",
        headers=headers,
        json={
            "resultado_obtenido": None,
            "bloqueado": True,
            "observacion": "",
            "fecha_ejecucion": "2026-11-20T18:45:00",
        },
    )
    assert blocked_without_note.status_code == 422


def test_manual_execution_rejects_unknown_case(client):
    headers = _headers(client)
    response = client.post(
        "/api/execution-cases/999999/executions",
        headers=headers,
        json={
            "resultado_obtenido": "Aceptado",
            "bloqueado": False,
            "observacion": "Caso inexistente",
            "fecha_ejecucion": "2026-11-20T18:50:00",
        },
    )
    assert response.status_code == 404


# MODIFICACIÓN 2026-11-21 - M04 / CP-08 / CP-10
# Regresión: los filtros deben incluir casos fuera de los últimos 50.
def test_execution_pagination_and_filters_include_historical_cases(client):
    from app.db import SessionLocal
    from app.models.generation import Generation, TestCase
    from app.models.project import DataModel, Project
    from sqlalchemy import select

    headers = _headers(client)
    generation = _create_generation(client, headers, "VALIDO", 3)
    old_ids = [item["caso_prueba_id"] for item in generation["casos"]]
    for observed in ("Rechazado", "Aceptado"):
        response = client.post(
            f"/api/execution-cases/{old_ids[0]}/executions", headers=headers,
            json={"resultado_obtenido": observed, "fecha_ejecucion": "2026-11-21T12:00:00"},
        )
        assert response.status_code == 201, response.text
    imported = client.post(
        "/api/execution-imports/csv/import", headers=headers,
        files={"file": ("resultados.csv", (
            "caso_prueba_id,resultado_obtenido,bloqueado,observacion,fecha_ejecucion\n"
            f"{old_ids[1]},Rechazado,false,Resultado distinto,2026-11-21T12:00:00\n"
        ).encode(), "text/csv")},
    )
    assert imported.status_code == 201, imported.text

    # Segundo proyecto/modelo, 60 casos recientes para reproducir el límite.
    # Se usa la API para crear la generación y datos de prueba reales.
    from tests.test_m03_generation import _configure_six_rules
    with SessionLocal() as db:
        old_generation = db.get(Generation, generation["generacion_id"])
        old_model = db.get(DataModel, old_generation.modelo_id)
        old_project = db.get(Project, old_model.proyecto_id)
        old_model_id, old_project_id = old_model.modelo_id, old_project.proyecto_id
        old_model.nombre = "Modelo histórico"
        old_project.nombre = "Proyecto histórico"
        db.commit()
    new_model_id = _configure_six_rules(client, headers)
    generated = client.post("/api/generations", headers=headers, json={
        "modelo_id": new_model_id, "cantidad_solicitada": 60, "tipo_escenario": "VALIDO",
    })
    assert generated.status_code == 201, generated.text

    def page(**params):
        response = client.get("/api/execution-cases/page", headers=headers, params=params)
        assert response.status_code == 200, response.text
        return response.json()

    first = page()
    assert first["total"] == 63 and first["total_pages"] == 2
    assert len(first["items"]) == 50
    assert all(row["estado"] == "PENDIENTE" for row in first["items"])
    assert {item["modelo_id"] for item in first["opciones"]} == {old_model_id, new_model_id}
    second = page(page=2)
    assert len(second["items"]) == 13
    all_ids = [row["caso_prueba_id"] for row in first["items"] + second["items"]]
    assert len(set(all_ids)) == 63 and all_ids == sorted(all_ids, reverse=True)
    assert set(old_ids).issubset(all_ids)
    assert page(page=999)["page"] == 2
    approved = page(estado="APROBADO", origen_registro="MANUAL", proyecto_id=old_project_id, modelo_id=old_model_id)
    assert approved["total"] == 1 and approved["items"][0]["caso_prueba_id"] == old_ids[0]
    assert {item["modelo_id"] for item in approved["opciones"]} == {old_model_id, new_model_id}
    failed = page(estado="FALLIDO", origen_registro="CSV")
    assert failed["total"] == 1 and failed["items"][0]["caso_prueba_id"] == old_ids[1]
    assert page(estado="PENDIENTE")["total"] == 61
    assert page(estado="PENDIENTE", origen_registro="CSV")["total"] == 0
    assert page(proyecto_id=old_project_id)["total"] == 3
    assert page(modelo_id=old_model_id)["total"] == 3
    legacy = client.get("/api/execution-cases", headers=headers, params={"estado": "APROBADO", "limit": 1})
    assert legacy.status_code == 200 and legacy.json()[0]["caso_prueba_id"] == old_ids[0]
    summary = client.get("/api/dashboard/summary", headers=headers).json()
    assert (summary["total_escenarios"], summary["aprobados"], summary["fallidos"], summary["pendientes"]) == (63, 1, 1, 61)


def test_execution_pagination_respects_user_and_role(client):
    from app.db import SessionLocal
    from app.models.user import User
    from sqlalchemy import select

    headers = _headers(client)
    _create_generation(client, headers, "VALIDO", 2)
    # Habilita un segundo usuario de prueba en la base SQLite aislada.
    with SessionLocal() as db:
        other = db.scalar(select(User).where(User.email == "inactivo@test.local"))
        other.estado = True
        db.commit()
    response = client.post("/api/auth/login", json={"email": "inactivo@test.local", "password": "Inactivo123!"})
    assert response.status_code == 200, response.text
    other_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    response = client.get("/api/execution-cases/page", headers=other_headers)
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "page_size": 50, "total_pages": 0, "opciones": []}
    response = client.post("/api/auth/login", json={"email": "admin@test.local", "password": "Admin123!"})
    admin_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert client.get("/api/execution-cases/page", headers=admin_headers).status_code == 403
    assert client.get("/api/execution-cases/page").status_code == 401


def test_execution_pagination_rejects_invalid_parameters(client):
    headers = _headers(client)
    for params in ({"page": 0}, {"page_size": 201}, {"estado": "ERROR"}, {"origen_registro": "ERROR"}, {"modelo_id": 0}):
        assert client.get("/api/execution-cases/page", headers=headers, params=params).status_code == 422
