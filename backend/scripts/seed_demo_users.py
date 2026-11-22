"""Crea usuarios demo iniciales para una instalación nueva de TestData Studio.

MODIFICACIÓN 2026-11-21 - PRE CIERRE / PRESENTACIÓN FINAL
- Se incorporan dos Analista/Tester adicionales (TESTER2 y TESTER3) COMENTADOS por defecto, para que puedan activarse en el futuro si se desea.
- Las contraseñas se leen exclusivamente desde variables de entorno.
- El script NO sobrescribe contraseñas de usuarios existentes.

Para cambiar la contraseña de un usuario ya creado, utilizar Gestión de usuarios
con un Administrador, de modo que el backend genere nuevamente el hash seguro.
"""

import os

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.security import hash_password
from app.db import SessionLocal
from app.models.user import Role, User


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value.startswith("REEMPLAZAR"):
        raise RuntimeError(
            f"Debe configurar {name} en backend/.env antes de ejecutar el seed."
        )
    return value


def _demo_users() -> list[dict[str, str]]:
    return [
        {
            "role": "Administrador",
            "name": "Administrador",
            "lastname": "TestData",
            "email": os.getenv("ADMIN_EMAIL", "admin@testdata.local").strip(),
            "password": _required("ADMIN_PASSWORD"),
        },
        {
            "role": "Analista/Tester",
            "name": "Analista",
            "lastname": "Tester",
            "email": os.getenv("TESTER_EMAIL", "tester@testdata.local").strip(),
            "password": _required("TESTER_PASSWORD"),
        },
        # {
        #     "role": "Analista/Tester",
        #     "name": "Tester",
        #     "lastname": "Dos",
        #     "email": os.getenv("TESTER2_EMAIL", "tester2@testdata.local").strip(),
        #     "password": _required("TESTER2_PASSWORD"),
        # },
        # {
        #     "role": "Analista/Tester",
        #     "name": "Tester",
        #     "lastname": "Tres",
        #     "email": os.getenv("TESTER3_EMAIL", "tester3@testdata.local").strip(),
        #     "password": _required("TESTER3_PASSWORD"),
        # },
    ]


def main() -> None:
    with SessionLocal() as db:
        for item in _demo_users():
            role = db.scalar(select(Role).where(Role.nombre == item["role"]))
            if role is None:
                raise RuntimeError(
                    f"No existe el rol {item['role']}. "
                    "Ejecute primero backend/sql/TestData_Studio_PostgreSQL.sql."
                )

            email = item["email"].lower()
            user = db.scalar(
                select(User)
                .options(joinedload(User.rol))
                .where(User.email == email)
            )

            if user is None:
                user = User(
                    rol_id=role.rol_id,
                    nombre=item["name"],
                    apellido=item["lastname"],
                    email=email,
                    password_hash=hash_password(item["password"]),
                    estado=True,
                )
                db.add(user)
                print(f"Creado: {email} ({item['role']})")
            else:
                print(f"Ya existe: {email} - no se modifica su contraseña")

        db.commit()


if __name__ == "__main__":
    main()
