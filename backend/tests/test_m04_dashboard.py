# ============================================================
# CREACIÓN 2026-11-20 - M04 / CP-10
# Pruebas de integración HU-10 / RF15.
# Validan conteo de escenarios, estados de ejecución, consistencia con la
# última ejecución y comportamiento controlado cuando no existen registros.
# ============================================================

from tests.test_m03_generation import _headers
from tests.test_m04_execution import _create_generation


def test_dashboard_returns_zero_values_without_data(client):
    headers = _headers(client)

    response = client.get("/api/dashboard/summary", headers=headers)

    assert response.status_code == 200, response.text
    assert response.json() == {
        "tipo_dashboard": "OPERATIVO",
        "total_generaciones": 0,
        "total_escenarios": 0,
        "ejecuciones_registradas": 0,
        "aprobados": 0,
        "fallidos": 0,
        "bloqueados": 0,
        "pendientes": 0,
    }


def test_dashboard_counts_generated_scenarios_and_execution_states(client):
    headers = _headers(client)
    generation = _create_generation(client, headers, "VALIDO", 4)
    case_ids = [item["caso_prueba_id"] for item in generation["casos"]]

    approved = client.post(
        f"/api/execution-cases/{case_ids[0]}/executions",
        headers=headers,
        json={
            "resultado_obtenido": "Aceptado",
            "bloqueado": False,
            "observacion": "Coincide con el esperado.",
            "fecha_ejecucion": "2026-11-20T22:30:00",
        },
    )
    assert approved.status_code == 201

    failed = client.post(
        f"/api/execution-cases/{case_ids[1]}/executions",
        headers=headers,
        json={
            "resultado_obtenido": "Rechazado",
            "bloqueado": False,
            "observacion": "No coincide con el esperado.",
            "fecha_ejecucion": "2026-11-20T22:31:00",
        },
    )
    assert failed.status_code == 201

    blocked = client.post(
        f"/api/execution-cases/{case_ids[2]}/executions",
        headers=headers,
        json={
            "resultado_obtenido": None,
            "bloqueado": True,
            "observacion": "Ambiente externo no disponible.",
            "fecha_ejecucion": "2026-11-20T22:32:00",
        },
    )
    assert blocked.status_code == 201

    response = client.get("/api/dashboard/summary", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["total_generaciones"] == 1
    assert body["total_escenarios"] == 4
    assert body["ejecuciones_registradas"] == 3
    assert body["aprobados"] == 1
    assert body["fallidos"] == 1
    assert body["bloqueados"] == 1
    assert body["pendientes"] == 1


def test_dashboard_uses_latest_execution_per_case(client):
    headers = _headers(client)
    generation = _create_generation(client, headers, "VALIDO", 1)
    case_id = generation["casos"][0]["caso_prueba_id"]

    first = client.post(
        f"/api/execution-cases/{case_id}/executions",
        headers=headers,
        json={
            "resultado_obtenido": "Rechazado",
            "bloqueado": False,
            "observacion": "Primera ejecución fallida.",
            "fecha_ejecucion": "2026-11-20T22:35:00",
        },
    )
    assert first.status_code == 201
    assert first.json()["estado"] == "FALLIDO"

    second = client.post(
        f"/api/execution-cases/{case_id}/executions",
        headers=headers,
        json={
            "resultado_obtenido": "Aceptado",
            "bloqueado": False,
            "observacion": "Retest aprobado.",
            "fecha_ejecucion": "2026-11-20T22:36:00",
        },
    )
    assert second.status_code == 201
    assert second.json()["estado"] == "APROBADO"

    response = client.get("/api/dashboard/summary", headers=headers)
    assert response.status_code == 200
    body = response.json()

    assert body["total_escenarios"] == 1
    assert body["ejecuciones_registradas"] == 1
    assert body["aprobados"] == 1
    assert body["fallidos"] == 0
    assert body["pendientes"] == 0


def test_admin_dashboard_returns_global_management_indicators(client):
    login = client.post(
        "/api/auth/login",
        json={"email": "admin@test.local", "password": "Admin123!"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.get("/api/dashboard/summary", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["tipo_dashboard"] == "ADMINISTRATIVO"
    assert body["total_usuarios"] == 3
    assert body["usuarios_activos"] == 2
    assert body["usuarios_inactivos"] == 1
    assert body["total_proyectos"] == 0
    assert body["total_modelos"] == 0
    assert body["total_escenarios"] == 0
    assert body["pendientes"] == 0
