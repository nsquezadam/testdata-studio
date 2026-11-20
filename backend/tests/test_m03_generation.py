# ============================================================
# CREACIÓN 2026-11-18 - M03 / CP-06
# Pruebas de integración para HU-05 / RF08-RF10.
# Validan escenarios válidos, inválidos, límite y persistencia/trazabilidad.
#
# MODIFICACIÓN 2026-11-19 - M03 / CP-06 - TRAZABILIDAD ENRIQUECIDA
# Se valida que cada regla exponga campos, valores generados, parámetros y
# una explicación concreta; en VALIDO no existe una única regla objetivo.
#
# MODIFICACIÓN 2026-11-19 - M03 / CP-06 - AISLAMIENTO DE REGLA OBJETIVO
# Se exige que cada escenario INVALIDO posea exactamente una regla en FALSE:
# la regla objetivo. Las reglas dependientes de un REQUIRED con NULL deben
# quedar registradas como "No aplica" y no como un segundo incumplimiento.
# ============================================================

from sqlalchemy import select

from app.db import SessionLocal
from app.models.configuration import DataType, RuleType
from app.models.generation import CaseRule, GeneratedData, Generation, TestCase as GeneratedTestCase


def _token_tester(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "tester@test.local", "password": "Tester123!"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(client):
    return {"Authorization": f"Bearer {_token_tester(client)}"}


def _catalog_id(model_class, code):
    with SessionLocal() as db:
        item = db.scalar(select(model_class).where(model_class.codigo == code))
        assert item is not None
        return item.tipo_dato_id if model_class is DataType else item.tipo_regla_id


def _create_model(client, headers, name="Modelo M03"):
    project = client.post(
        "/api/projects",
        headers=headers,
        json={"nombre": f"Proyecto {name}", "descripcion": "Proyecto generación"},
    )
    assert project.status_code == 201
    model = client.post(
        f"/api/projects/{project.json()['proyecto_id']}/models",
        headers=headers,
        json={"nombre": name, "descripcion": "Modelo para CP-06"},
    )
    assert model.status_code == 201
    return model.json()["modelo_id"]


def _create_field(client, headers, model_id, type_code, name, order):
    response = client.post(
        f"/api/models/{model_id}/fields",
        headers=headers,
        json={
            "tipo_dato_id": _catalog_id(DataType, type_code),
            "nombre": name,
            "descripcion": f"Campo {name}",
            "orden": order,
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_rule(client, headers, model_id, type_code, name, fields, params):
    response = client.post(
        f"/api/models/{model_id}/rules",
        headers=headers,
        json={
            "tipo_regla_id": _catalog_id(RuleType, type_code),
            "nombre": name,
            "descripcion": f"Regla {name}",
            "campos": fields,
            "parametros": params,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _configure_six_rules(client, headers):
    model_id = _create_model(client, headers)

    age = _create_field(client, headers, model_id, "INTEGER", "edad_cliente", 1)
    email = _create_field(client, headers, model_id, "EMAIL", "email_cliente", 2)
    customer_type = _create_field(client, headers, model_id, "STRING", "tipo_cliente", 3)
    start = _create_field(client, headers, model_id, "DATE", "fecha_inicio", 4)
    end = _create_field(client, headers, model_id, "DATE", "fecha_fin", 5)

    _create_rule(
        client, headers, model_id, "REQUIRED", "Email obligatorio",
        [{"campo_id": email["campo_id"], "rol_campo": "PRINCIPAL"}], []
    )
    _create_rule(
        client, headers, model_id, "RANGE", "Rango edad",
        [{"campo_id": age["campo_id"], "rol_campo": "PRINCIPAL"}],
        [
            {"clave": "min", "valor": "18", "orden": 1},
            {"clave": "max", "valor": "65", "orden": 2},
        ]
    )
    _create_rule(
        client, headers, model_id, "ALLOWED_VALUES", "Tipos permitidos",
        [{"campo_id": customer_type["campo_id"], "rol_campo": "PRINCIPAL"}],
        [{"clave": "valores", "valor": "PERSONA,EMPRESA,VIP", "orden": 1}]
    )
    _create_rule(
        client, headers, model_id, "FORMAT", "Longitud correo",
        [{"campo_id": email["campo_id"], "rol_campo": "PRINCIPAL"}],
        [
            {"clave": "longitud_min", "valor": "5", "orden": 1},
            {"clave": "longitud_max", "valor": "150", "orden": 2},
        ]
    )
    _create_rule(
        client, headers, model_id, "COMPARISON", "Fechas válidas",
        [
            {"campo_id": start["campo_id"], "rol_campo": "PRINCIPAL"},
            {"campo_id": end["campo_id"], "rol_campo": "REFERENCIA"},
        ],
        [{"clave": "operador", "valor": "<", "orden": 1}]
    )
    _create_rule(
        client, headers, model_id, "CONDITIONAL", "VIP mayor de edad",
        [
            {"campo_id": age["campo_id"], "rol_campo": "PRINCIPAL"},
            {"campo_id": customer_type["campo_id"], "rol_campo": "CONDICION"},
        ],
        [
            {"clave": "condicion_operador", "valor": "=", "orden": 1},
            {"clave": "condicion_valor", "valor": "VIP", "orden": 2},
            {"clave": "accion", "valor": "GREATER_EQUAL", "orden": 3},
            {"clave": "accion_valor", "valor": "21", "orden": 4},
        ]
    )
    return model_id


def test_readiness_requiere_campos_y_reglas(client):
    headers = _headers(client)
    model_id = _create_model(client, headers, "Modelo vacío")

    response = client.get(
        f"/api/models/{model_id}/generation-readiness",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["listo"] is False
    assert data["campos_activos"] == 0
    assert data["reglas_activas"] == 0
    assert len(data["observaciones"]) == 2


def test_generacion_valida_con_seis_tipos_de_regla(client):
    headers = _headers(client)
    model_id = _configure_six_rules(client, headers)

    response = client.post(
        "/api/generations",
        headers=headers,
        json={
            "modelo_id": model_id,
            "cantidad_solicitada": 3,
            "tipo_escenario": "VALIDO",
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["estado"] == "COMPLETADA"
    assert data["tipo_escenario"] == "VALIDO"
    assert len(data["casos"]) == 3
    assert all(case["resultado_esperado"].startswith("Aceptar") for case in data["casos"])
    assert all(len(case["datos"]) == 5 for case in data["casos"])
    assert all(len(case["reglas"]) == 6 for case in data["casos"])
    assert all(all(rule["cumple_esperado"] for rule in case["reglas"]) for case in data["casos"])
    assert all(case["regla_objetivo_id"] is None for case in data["casos"])
    assert all(case["regla_objetivo_nombre"] is None for case in data["casos"])

    first_case = data["casos"][0]
    required = next(rule for rule in first_case["reglas"] if rule["tipo_regla_codigo"] == "REQUIRED")
    range_rule = next(rule for rule in first_case["reglas"] if rule["tipo_regla_codigo"] == "RANGE")
    comparison = next(rule for rule in first_case["reglas"] if rule["tipo_regla_codigo"] == "COMPARISON")
    conditional = next(rule for rule in first_case["reglas"] if rule["tipo_regla_codigo"] == "CONDITIONAL")

    assert required["campos"][0]["rol_campo"] == "PRINCIPAL"
    assert required["campos"][0]["valor_generado"] is not None
    assert "tiene valor" in required["detalle_esperado"]

    assert {param["clave"] for param in range_rule["parametros"]} == {"min", "max"}
    assert "rango permitido" in range_rule["detalle_esperado"]

    assert {field["rol_campo"] for field in comparison["campos"]} == {"PRINCIPAL", "REFERENCIA"}
    assert len(comparison["parametros"]) == 1

    assert {field["rol_campo"] for field in conditional["campos"]} == {"PRINCIPAL", "CONDICION"}
    assert "SI " in conditional["detalle_esperado"]
    assert "ENTONCES" in conditional["detalle_esperado"]


def test_generacion_invalida_incumple_regla_objetivo(client):
    headers = _headers(client)
    model_id = _configure_six_rules(client, headers)

    response = client.post(
        "/api/generations",
        headers=headers,
        json={
            "modelo_id": model_id,
            "cantidad_solicitada": 6,
            "tipo_escenario": "INVALIDO",
        },
    )
    assert response.status_code == 201, response.text
    cases = response.json()["casos"]
    assert len(cases) == 6
    assert all(case["regla_objetivo_id"] is not None for case in cases)
    assert all(case["resultado_esperado"].startswith("Rechazar") for case in cases)

    # Cada escenario inválido debe romper SOLO su regla objetivo.
    for case in cases:
        failed_rules = [rule for rule in case["reglas"] if not rule["cumple_esperado"]]
        assert len(failed_rules) == 1, case
        assert failed_rules[0]["regla_id"] == case["regla_objetivo_id"]
        assert failed_rules[0]["regla_nombre"] == case["regla_objetivo_nombre"]

    # El primer caso apunta a REQUIRED(email). FORMAT(email) no puede evaluarse
    # con NULL, por lo que debe quedar explícitamente como NO APLICA.
    required_case = cases[0]
    format_rule = next(
        rule for rule in required_case["reglas"]
        if rule["tipo_regla_codigo"] == "FORMAT"
    )
    assert format_rule["cumple_esperado"] is True
    assert format_rule["detalle_esperado"].startswith("No aplica:")


def test_generacion_limite_conserva_escenario_y_trazabilidad(client):
    headers = _headers(client)
    model_id = _configure_six_rules(client, headers)

    response = client.post(
        "/api/generations",
        headers=headers,
        json={
            "modelo_id": model_id,
            "cantidad_solicitada": 2,
            "tipo_escenario": "LIMITE",
        },
    )
    assert response.status_code == 201, response.text
    generation = response.json()
    assert all(case["tipo_escenario"] == "LIMITE" for case in generation["casos"])
    assert all(case["regla_objetivo_nombre"] for case in generation["casos"])
    assert all(case["resultado_esperado"].startswith("Aceptar") for case in generation["casos"])

    detail = client.get(
        f"/api/generations/{generation['generacion_id']}",
        headers=headers,
    )
    assert detail.status_code == 200
    assert len(detail.json()["casos"]) == 2

    listing = client.get(f"/api/generations?modelo_id={model_id}", headers=headers)
    assert listing.status_code == 200
    assert listing.json()[0]["generacion_id"] == generation["generacion_id"]
    assert listing.json()[0]["total_casos"] == 2

    with SessionLocal() as db:
        assert db.scalar(select(Generation)) is not None
        assert len(db.scalars(select(GeneratedTestCase)).all()) == 2
        assert len(db.scalars(select(GeneratedData)).all()) == 10
        assert len(db.scalars(select(CaseRule)).all()) == 12


def test_rechaza_generar_modelo_sin_reglas(client):
    headers = _headers(client)
    model_id = _create_model(client, headers, "Modelo sin reglas")
    _create_field(client, headers, model_id, "INTEGER", "edad", 1)

    response = client.post(
        "/api/generations",
        headers=headers,
        json={"modelo_id": model_id, "cantidad_solicitada": 1, "tipo_escenario": "VALIDO"},
    )
    assert response.status_code == 400
    assert "reglas activas" in response.json()["detail"]


def test_rechaza_cantidad_superior_a_100(client):
    headers = _headers(client)
    response = client.post(
        "/api/generations",
        headers=headers,
        json={"modelo_id": 1, "cantidad_solicitada": 101, "tipo_escenario": "VALIDO"},
    )
    assert response.status_code == 422


def test_generacion_invalida_aisla_dependencias_compartidas(client):
    # MODIFICACIÓN 2026-11-19 - M03 / CP-06 - AISLAMIENTO DE REGLA OBJETIVO
    # Caso de regresión inspirado en el modelo 5 probado manualmente:
    # - id_cliente participa en REQUIRED + RANGE.
    # - nombre_cliente participa en FORMAT + COMPARISON.
    # Motivo: asegurar que romper la regla objetivo no genere un segundo FALSE.
    headers = _headers(client)
    model_id = _create_model(client, headers, "Modelo aislamiento reglas")

    customer_id = _create_field(client, headers, model_id, "INTEGER", "id_cliente", 1)
    name = _create_field(client, headers, model_id, "STRING", "nombre_cliente", 2)
    business_name = _create_field(client, headers, model_id, "STRING", "razon_social", 3)

    required = _create_rule(
        client, headers, model_id, "REQUIRED", "id_obligatorio",
        [{"campo_id": customer_id["campo_id"], "rol_campo": "PRINCIPAL"}], []
    )
    format_rule = _create_rule(
        client, headers, model_id, "FORMAT", "nombre_obligatorio",
        [{"campo_id": name["campo_id"], "rol_campo": "PRINCIPAL"}],
        [
            {"clave": "longitud_min", "valor": "5", "orden": 1},
            {"clave": "longitud_max", "valor": "100", "orden": 2},
        ]
    )
    range_rule = _create_rule(
        client, headers, model_id, "RANGE", "rango_id",
        [{"campo_id": customer_id["campo_id"], "rol_campo": "PRINCIPAL"}],
        [
            {"clave": "min", "valor": "1", "orden": 1},
            {"clave": "max", "valor": "200", "orden": 2},
        ]
    )
    comparison = _create_rule(
        client, headers, model_id, "COMPARISON", "comparacion_nombres",
        [
            {"campo_id": name["campo_id"], "rol_campo": "PRINCIPAL"},
            {"campo_id": business_name["campo_id"], "rol_campo": "REFERENCIA"},
        ],
        [{"clave": "operador", "valor": "=", "orden": 1}]
    )

    response = client.post(
        "/api/generations",
        headers=headers,
        json={
            "modelo_id": model_id,
            "cantidad_solicitada": 2,
            "tipo_escenario": "INVALIDO",
        },
    )
    assert response.status_code == 201, response.text
    cases = response.json()["casos"]

    # Caso 1: REQUIRED es la única regla en FALSE y RANGE queda NO APLICA.
    first = cases[0]
    assert first["regla_objetivo_id"] == required["regla_id"]
    failed_first = [rule for rule in first["reglas"] if not rule["cumple_esperado"]]
    assert [rule["regla_id"] for rule in failed_first] == [required["regla_id"]]
    range_trace = next(rule for rule in first["reglas"] if rule["regla_id"] == range_rule["regla_id"])
    assert range_trace["cumple_esperado"] is True
    assert range_trace["detalle_esperado"].startswith("No aplica:")

    # Caso 2: FORMAT es la única regla en FALSE. COMPARISON debe ser reparada
    # igualando el campo de referencia al valor inválido generado en PRINCIPAL.
    second = cases[1]
    assert second["regla_objetivo_id"] == format_rule["regla_id"]
    failed_second = [rule for rule in second["reglas"] if not rule["cumple_esperado"]]
    assert [rule["regla_id"] for rule in failed_second] == [format_rule["regla_id"]]
    comparison_trace = next(rule for rule in second["reglas"] if rule["regla_id"] == comparison["regla_id"])
    assert comparison_trace["cumple_esperado"] is True

    values = {item["campo_nombre"]: item["valor_generado"] for item in second["datos"]}
    assert values["nombre_cliente"] == "XXXX"
    assert values["razon_social"] == "XXXX"
