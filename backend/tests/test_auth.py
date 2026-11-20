# HU-01 / CP-01 / CP-02


def test_hu01_ca01_valid_credentials_allow_access(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@test.local", "password": "Admin123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["user"]["email"] == "admin@test.local"


def test_hu01_ca02_admin_profile_is_returned(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@test.local", "password": "Admin123!"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["rol"] == "Administrador"


def test_hu01_ca03_tester_profile_is_returned(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "tester@test.local", "password": "Tester123!"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["rol"] == "Analista/Tester"


def test_hu01_ca04_invalid_credentials_are_rejected(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@test.local", "password": "Incorrecta"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Correo o contraseña no válidos."


def test_hu01_ca05_required_fields_are_rejected(client):
    response = client.post("/api/auth/login", json={"email": "", "password": ""})
    assert response.status_code == 422


def test_hu01_ca06_inactive_user_is_rejected(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "inactivo@test.local", "password": "Inactivo123!"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "La cuenta no se encuentra habilitada."


def test_admin_route_denies_tester(client):
    login = client.post(
        "/api/auth/login",
        json={"email": "tester@test.local", "password": "Tester123!"},
    ).json()
    response = client.get(
        "/api/secure/admin",
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )
    assert response.status_code == 403
