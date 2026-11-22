"""SEG-01 - Pruebas automatizadas de seguridad para RNF01.

MODIFICACIÓN 2026-11-21 - SEGURIDAD / RNF01
Se incorporan controles automáticos sobre autenticación, autorización por rol,
integridad del JWT y almacenamiento seguro de contraseñas.
Motivo: disponer de evidencia objetiva de que el MVP protege endpoints y no
almacena contraseñas en texto plano.
"""

from sqlalchemy import select

from app.core.security import verify_password
from app.db import SessionLocal
from app.models.user import User


def _login(client, email: str, password: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_seg01_c01_endpoint_protegido_rechaza_acceso_sin_token(client):
    """C01: un endpoint administrativo no debe aceptar acceso anónimo."""
    response = client.get("/api/users")

    assert response.status_code == 401
    assert response.json()["detail"] == "Se requiere autenticación."


def test_seg01_c02_token_invalido_es_rechazado(client):
    """C02: un JWT inexistente/incorrecto no debe permitir acceder a /auth/me."""
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer token-invalido-seg01"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Sesión inválida o expirada."


def test_seg01_c03_token_manipulado_es_rechazado(client):
    """C03: modificar un JWT emitido por la aplicación invalida su firma."""
    token = _login(client, "tester@test.local", "Tester123!")
    ultimo = "a" if token[-1] != "a" else "b"
    token_manipulado = f"{token[:-1]}{ultimo}"

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token_manipulado}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Sesión inválida o expirada."


def test_seg01_c04_analista_no_puede_acceder_a_gestion_usuarios(client):
    """C04: el rol Analista/Tester no puede consumir funciones de Administrador."""
    token = _login(client, "tester@test.local", "Tester123!")

    response = client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "No posee permisos para realizar esta acción."


def test_seg01_c05_administrador_si_puede_acceder_a_gestion_usuarios(client):
    """C05: el rol Administrador autorizado sí obtiene acceso al recurso."""
    token = _login(client, "admin@test.local", "Admin123!")

    response = client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_seg01_c06_password_se_almacena_con_hash_y_no_en_texto_plano(client):
    """C06: la contraseña persistida debe ser un hash verificable, no texto plano."""
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == "admin@test.local"))
        assert user is not None
        assert user.password_hash != "Admin123!"
        assert len(user.password_hash) > len("Admin123!")
        assert verify_password("Admin123!", user.password_hash) is True


def test_seg01_c07_intento_basico_inyeccion_login_no_autentica(client):
    """C07: una cadena típica de inyección SQL no debe eludir la autenticación."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "' OR 1=1 --",
            "password": "' OR 1=1 --",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Correo o contraseña no válidos."


def test_seg01_c08_respuesta_login_no_expone_password_hash(client):
    """C08: la API no debe devolver contraseña ni password_hash en la sesión."""
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@test.local", "password": "Admin123!"},
    )

    assert response.status_code == 200
    body = response.json()
    user = body["user"]
    assert "password" not in user
    assert "password_hash" not in user
