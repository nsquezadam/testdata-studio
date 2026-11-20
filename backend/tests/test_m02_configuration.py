# MODIFICACIÓN 2026-11-18 - INC-02 / INC-03
# INC-02: pruebas de regresión para impedir órdenes duplicados al crear
# o modificar campos dentro del mismo modelo.
# INC-03: se valida que los catálogos expongan tipo_dato_id y tipo_regla_id
# para mantener el contrato utilizado por el frontend.

from sqlalchemy import select

from app.db import SessionLocal
from app.models.audit import Audit
from app.models.configuration import BusinessRule, DataField, DataType, RuleType


def _token_tester(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "tester@test.local", "password": "Tester123!"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(client):
    return {"Authorization": f"Bearer {_token_tester(client)}"}


def _crear_modelo(client, headers):
    proyecto = client.post(
        "/api/projects",
        headers=headers,
        json={"nombre": "Proyecto M02", "descripcion": "Prueba M02"},
    )
    assert proyecto.status_code == 201
    proyecto_id = proyecto.json()["proyecto_id"]

    modelo = client.post(
        f"/api/projects/{proyecto_id}/models",
        headers=headers,
        json={"nombre": "Modelo M02", "descripcion": "Modelo para campos y reglas"},
    )
    assert modelo.status_code == 201
    return modelo.json()["modelo_id"]


def _id_catalogo(model_class, codigo):
    with SessionLocal() as db:
        return db.scalar(select(model_class).where(model_class.codigo == codigo)).__dict__[
            "tipo_dato_id" if model_class is DataType else "tipo_regla_id"
        ]


def test_catalogos_m02_disponibles(client):
    headers = _headers(client)
    tipos_dato = client.get("/api/data-types", headers=headers)
    tipos_regla = client.get("/api/rule-types", headers=headers)

    assert tipos_dato.status_code == 200
    assert tipos_regla.status_code == 200
    assert len(tipos_dato.json()) == 6
    assert len(tipos_regla.json()) == 6
    assert all("tipo_dato_id" in item for item in tipos_dato.json())
    assert all("tipo_regla_id" in item for item in tipos_regla.json())


def test_crear_y_modificar_campo(client):
    headers = _headers(client)
    modelo_id = _crear_modelo(client, headers)
    tipo_entero = _id_catalogo(DataType, "INTEGER")

    crear = client.post(
        f"/api/models/{modelo_id}/fields",
        headers=headers,
        json={
            "tipo_dato_id": tipo_entero,
            "nombre": "edad",
            "descripcion": "Edad del cliente",
            "orden": 1,
        },
    )
    assert crear.status_code == 201
    campo_id = crear.json()["campo_id"]

    modificar = client.put(
        f"/api/fields/{campo_id}",
        headers=headers,
        json={
            "tipo_dato_id": tipo_entero,
            "nombre": "edad_cliente",
            "descripcion": "Edad actual del cliente",
            "orden": 1,
        },
    )
    assert modificar.status_code == 200
    assert modificar.json()["nombre"] == "edad_cliente"


def test_crear_regla_rango_valida(client):
    headers = _headers(client)
    modelo_id = _crear_modelo(client, headers)
    tipo_entero = _id_catalogo(DataType, "INTEGER")
    tipo_rango = _id_catalogo(RuleType, "RANGE")

    campo = client.post(
        f"/api/models/{modelo_id}/fields",
        headers=headers,
        json={"tipo_dato_id": tipo_entero, "nombre": "edad", "orden": 1},
    ).json()

    response = client.post(
        f"/api/models/{modelo_id}/rules",
        headers=headers,
        json={
            "tipo_regla_id": tipo_rango,
            "nombre": "Rango edad",
            "descripcion": "Edad entre 18 y 65",
            "campos": [{"campo_id": campo["campo_id"], "rol_campo": "PRINCIPAL"}],
            "parametros": [
                {"clave": "min", "valor": "18", "orden": 1},
                {"clave": "max", "valor": "65", "orden": 2},
            ],
        },
    )

    assert response.status_code == 201
    assert response.json()["tipo_regla_codigo"] == "RANGE"
    assert len(response.json()["parametros"]) == 2


def test_rechaza_rango_incoherente(client):
    headers = _headers(client)
    modelo_id = _crear_modelo(client, headers)
    tipo_entero = _id_catalogo(DataType, "INTEGER")
    tipo_rango = _id_catalogo(RuleType, "RANGE")

    campo = client.post(
        f"/api/models/{modelo_id}/fields",
        headers=headers,
        json={"tipo_dato_id": tipo_entero, "nombre": "monto", "orden": 1},
    ).json()

    response = client.post(
        f"/api/models/{modelo_id}/rules",
        headers=headers,
        json={
            "tipo_regla_id": tipo_rango,
            "nombre": "Rango inválido",
            "campos": [{"campo_id": campo["campo_id"], "rol_campo": "PRINCIPAL"}],
            "parametros": [
                {"clave": "min", "valor": "100", "orden": 1},
                {"clave": "max", "valor": "20", "orden": 2},
            ],
        },
    )

    assert response.status_code == 400
    assert "mínimo" in response.json()["detail"]


def test_estado_logico_campo_y_regla_genera_auditoria(client):
    headers = _headers(client)
    modelo_id = _crear_modelo(client, headers)
    tipo_entero = _id_catalogo(DataType, "INTEGER")
    tipo_rango = _id_catalogo(RuleType, "RANGE")

    campo = client.post(
        f"/api/models/{modelo_id}/fields",
        headers=headers,
        json={"tipo_dato_id": tipo_entero, "nombre": "edad", "orden": 1},
    ).json()

    regla = client.post(
        f"/api/models/{modelo_id}/rules",
        headers=headers,
        json={
            "tipo_regla_id": tipo_rango,
            "nombre": "Rango edad",
            "campos": [{"campo_id": campo["campo_id"], "rol_campo": "PRINCIPAL"}],
            "parametros": [
                {"clave": "min", "valor": "18", "orden": 1},
                {"clave": "max", "valor": "65", "orden": 2},
            ],
        },
    ).json()

    bloqueado = client.patch(
        f"/api/fields/{campo['campo_id']}/estado",
        headers=headers,
        json={"estado": False},
    )
    assert bloqueado.status_code == 400

    desactivar_regla = client.patch(
        f"/api/rules/{regla['regla_id']}/estado",
        headers=headers,
        json={"estado": False},
    )
    assert desactivar_regla.status_code == 200

    desactivar_campo = client.patch(
        f"/api/fields/{campo['campo_id']}/estado",
        headers=headers,
        json={"estado": False},
    )
    assert desactivar_campo.status_code == 200

    with SessionLocal() as db:
        entidades = set(
            db.scalars(
                select(Audit.entidad_afectada).where(
                    Audit.entidad_afectada.in_(["CAMPO", "REGLA"])
                )
            ).all()
        )
    assert entidades == {"CAMPO", "REGLA"}


def test_rechaza_orden_repetido_en_mismo_modelo(client):
    headers = _headers(client)
    modelo_id = _crear_modelo(client, headers)
    tipo_entero = _id_catalogo(DataType, "INTEGER")

    primero = client.post(
        f"/api/models/{modelo_id}/fields",
        headers=headers,
        json={
            "tipo_dato_id": tipo_entero,
            "nombre": "campo_uno",
            "orden": 1,
        },
    )
    assert primero.status_code == 201

    repetido = client.post(
        f"/api/models/{modelo_id}/fields",
        headers=headers,
        json={
            "tipo_dato_id": tipo_entero,
            "nombre": "campo_dos",
            "orden": 1,
        },
    )

    assert repetido.status_code == 409
    assert "orden 1" in repetido.json()["detail"]
    assert "campo_uno" in repetido.json()["detail"]


def test_rechaza_modificar_campo_a_orden_ocupado(client):
    headers = _headers(client)
    modelo_id = _crear_modelo(client, headers)
    tipo_entero = _id_catalogo(DataType, "INTEGER")

    campo_uno = client.post(
        f"/api/models/{modelo_id}/fields",
        headers=headers,
        json={"tipo_dato_id": tipo_entero, "nombre": "campo_uno", "orden": 1},
    ).json()

    campo_dos = client.post(
        f"/api/models/{modelo_id}/fields",
        headers=headers,
        json={"tipo_dato_id": tipo_entero, "nombre": "campo_dos", "orden": 2},
    ).json()

    repetido = client.put(
        f"/api/fields/{campo_dos['campo_id']}",
        headers=headers,
        json={
            "tipo_dato_id": tipo_entero,
            "nombre": "campo_dos",
            "orden": 1,
        },
    )

    assert repetido.status_code == 409
    assert "orden 1" in repetido.json()["detail"]
    assert "campo_uno" in repetido.json()["detail"]

# ============================================================
# MODIFICACIÓN 2026-11-18 - INC-04 v5 / CONDITIONAL GENERAL
# Pruebas de regresión para la definición SI/ENTONCES de CONDITIONAL,
# la separación respecto de COMPARISON y el contrato ALLOWED_VALUES.
# ============================================================


def test_comparison_usa_principal_y_referencia(client):
    headers = _headers(client)
    modelo_id = _crear_modelo(client, headers)
    tipo_fecha = _id_catalogo(DataType, "DATE")
    tipo_comparison = _id_catalogo(RuleType, "COMPARISON")

    inicio = client.post(
        f"/api/models/{modelo_id}/fields",
        headers=headers,
        json={"tipo_dato_id": tipo_fecha, "nombre": "fecha_inicio", "orden": 1},
    ).json()
    fin = client.post(
        f"/api/models/{modelo_id}/fields",
        headers=headers,
        json={"tipo_dato_id": tipo_fecha, "nombre": "fecha_fin", "orden": 2},
    ).json()

    response = client.post(
        f"/api/models/{modelo_id}/rules",
        headers=headers,
        json={
            "tipo_regla_id": tipo_comparison,
            "nombre": "Fechas válidas",
            "campos": [
                {"campo_id": inicio["campo_id"], "rol_campo": "PRINCIPAL"},
                {"campo_id": fin["campo_id"], "rol_campo": "REFERENCIA"},
            ],
            "parametros": [{"clave": "operador", "valor": "<", "orden": 1}],
        },
    )

    assert response.status_code == 201
    roles = {item["rol_campo"] for item in response.json()["campos"]}
    assert roles == {"PRINCIPAL", "REFERENCIA"}


def test_conditional_required_valida(client):
    headers = _headers(client)
    modelo_id = _crear_modelo(client, headers)
    tipo_texto = _id_catalogo(DataType, "STRING")
    tipo_conditional = _id_catalogo(RuleType, "CONDITIONAL")

    condicion = client.post(
        f"/api/models/{modelo_id}/fields",
        headers=headers,
        json={"tipo_dato_id": tipo_texto, "nombre": "tipo_cliente", "orden": 1},
    ).json()
    objetivo = client.post(
        f"/api/models/{modelo_id}/fields",
        headers=headers,
        json={"tipo_dato_id": tipo_texto, "nombre": "razon_social", "orden": 2},
    ).json()

    response = client.post(
        f"/api/models/{modelo_id}/rules",
        headers=headers,
        json={
            "tipo_regla_id": tipo_conditional,
            "nombre": "Razón social empresa",
            "campos": [
                {"campo_id": condicion["campo_id"], "rol_campo": "CONDICION"},
                {"campo_id": objetivo["campo_id"], "rol_campo": "PRINCIPAL"},
            ],
            "parametros": [
                {"clave": "condicion_operador", "valor": "=", "orden": 1},
                {"clave": "condicion_valor", "valor": "EMPRESA", "orden": 2},
                {"clave": "accion", "valor": "REQUIRED", "orden": 3},
            ],
        },
    )

    assert response.status_code == 201
    params = {item["clave"]: item["valor"] for item in response.json()["parametros"]}
    assert params["accion"] == "REQUIRED"
    assert "accion_valor" not in params


def test_conditional_consecuencia_comparativa_valida(client):
    headers = _headers(client)
    modelo_id = _crear_modelo(client, headers)
    tipo_texto = _id_catalogo(DataType, "STRING")
    tipo_decimal = _id_catalogo(DataType, "DECIMAL")
    tipo_conditional = _id_catalogo(RuleType, "CONDITIONAL")

    condicion = client.post(
        f"/api/models/{modelo_id}/fields",
        headers=headers,
        json={"tipo_dato_id": tipo_texto, "nombre": "tipo_cliente", "orden": 1},
    ).json()
    objetivo = client.post(
        f"/api/models/{modelo_id}/fields",
        headers=headers,
        json={"tipo_dato_id": tipo_decimal, "nombre": "descuento", "orden": 2},
    ).json()

    response = client.post(
        f"/api/models/{modelo_id}/rules",
        headers=headers,
        json={
            "tipo_regla_id": tipo_conditional,
            "nombre": "Descuento VIP",
            "campos": [
                {"campo_id": condicion["campo_id"], "rol_campo": "CONDICION"},
                {"campo_id": objetivo["campo_id"], "rol_campo": "PRINCIPAL"},
            ],
            "parametros": [
                {"clave": "condicion_operador", "valor": "=", "orden": 1},
                {"clave": "condicion_valor", "valor": "VIP", "orden": 2},
                {"clave": "accion", "valor": "GREATER_EQUAL", "orden": 3},
                {"clave": "accion_valor", "valor": "15", "orden": 4},
            ],
        },
    )

    assert response.status_code == 201
    params = {item["clave"]: item["valor"] for item in response.json()["parametros"]}
    assert params["accion"] == "GREATER_EQUAL"
    assert params["accion_valor"] == "15"


def test_conditional_rechaza_mayor_que_sobre_texto(client):
    headers = _headers(client)
    modelo_id = _crear_modelo(client, headers)
    tipo_texto = _id_catalogo(DataType, "STRING")
    tipo_conditional = _id_catalogo(RuleType, "CONDITIONAL")

    condicion = client.post(
        f"/api/models/{modelo_id}/fields",
        headers=headers,
        json={"tipo_dato_id": tipo_texto, "nombre": "tipo_cliente", "orden": 1},
    ).json()
    objetivo = client.post(
        f"/api/models/{modelo_id}/fields",
        headers=headers,
        json={"tipo_dato_id": tipo_texto, "nombre": "categoria", "orden": 2},
    ).json()

    response = client.post(
        f"/api/models/{modelo_id}/rules",
        headers=headers,
        json={
            "tipo_regla_id": tipo_conditional,
            "nombre": "Condición inválida",
            "campos": [
                {"campo_id": condicion["campo_id"], "rol_campo": "CONDICION"},
                {"campo_id": objetivo["campo_id"], "rol_campo": "PRINCIPAL"},
            ],
            "parametros": [
                {"clave": "condicion_operador", "valor": "=", "orden": 1},
                {"clave": "condicion_valor", "valor": "VIP", "orden": 2},
                {"clave": "accion", "valor": "GREATER_THAN", "orden": 3},
                {"clave": "accion_valor", "valor": "A", "orden": 4},
            ],
        },
    )

    assert response.status_code == 400
    assert "Entero, Decimal o Fecha" in response.json()["detail"]


def test_allowed_values_usa_parametro_valores(client):
    headers = _headers(client)
    modelo_id = _crear_modelo(client, headers)
    tipo_texto = _id_catalogo(DataType, "STRING")
    tipo_allowed = _id_catalogo(RuleType, "ALLOWED_VALUES")

    campo = client.post(
        f"/api/models/{modelo_id}/fields",
        headers=headers,
        json={"tipo_dato_id": tipo_texto, "nombre": "categoria", "orden": 1},
    ).json()

    response = client.post(
        f"/api/models/{modelo_id}/rules",
        headers=headers,
        json={
            "tipo_regla_id": tipo_allowed,
            "nombre": "Categorías permitidas",
            "campos": [{"campo_id": campo["campo_id"], "rol_campo": "PRINCIPAL"}],
            "parametros": [
                {"clave": "valores", "valor": "A,B,C", "orden": 1},
            ],
        },
    )

    assert response.status_code == 201
    assert response.json()["parametros"][0]["clave"] == "valores"
