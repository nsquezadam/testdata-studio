import os

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.security import hash_password
from app.db import SessionLocal
from app.models.user import Role, User


DEMO_USERS = [
    {
        "role": "Administrador",
        "name": "Administrador",
        "lastname": "TestData",
        "email": os.getenv("ADMIN_EMAIL", "admin@testdata.local"),
        "password": os.getenv("ADMIN_PASSWORD", "Cambiar_Admin_123!"),
    },
    {
        "role": "Analista/Tester",
        "name": "Analista",
        "lastname": "Tester",
        "email": os.getenv("TESTER_EMAIL", "tester@testdata.local"),
        "password": os.getenv("TESTER_PASSWORD", "Cambiar_Tester_123!"),
    },
]


def main():
    with SessionLocal() as db:
        for item in DEMO_USERS:
            role = db.scalar(select(Role).where(Role.nombre == item["role"]))
            if role is None:
                raise RuntimeError(
                    f"No existe el rol {item['role']}. Ejecute primero el SQL base del proyecto."
                )

            user = db.scalar(
                select(User)
                .options(joinedload(User.rol))
                .where(User.email == item["email"].lower())
            )
            if user is None:
                user = User(
                    rol_id=role.rol_id,
                    nombre=item["name"],
                    apellido=item["lastname"],
                    email=item["email"].lower(),
                    password_hash=hash_password(item["password"]),
                    estado=True,
                )
                db.add(user)
                print(f"Creado: {item['email']} ({item['role']})")
            else:
                print(f"Ya existe: {item['email']}")
        db.commit()


if __name__ == "__main__":
    main()
