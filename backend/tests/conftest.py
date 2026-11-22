import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
# MODIFICACIÓN 2026-11-21 - PRUEBAS AUTOMATIZADAS
# Se utiliza una clave de prueba de 32+ caracteres para cumplir la longitud
# recomendada de HS256 y evitar advertencias criptográficas durante pytest.
os.environ["JWT_SECRET"] = "testdata-studio-test-secret-32-chars-minimum"

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db import Base, SessionLocal, engine
from app.main import app
from app.models.audit import Audit
from app.models.configuration import (
    BusinessRule,
    DataField,
    DataType,
    RuleField,
    RuleParameter,
    RuleType,
)
from app.models.project import DataModel, Project
from app.models.generation import CaseRule, GeneratedData, Generation, TestCase
from app.models.execution import Execution
from app.models.user import Role, User


@pytest.fixture(scope="session", autouse=True)
def database_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_and_seed():
    with SessionLocal() as db:
        # MODIFICACIÓN 2026-11-20 - M04 / CP-08
        # Ejecución depende de caso_prueba, por lo que se elimina primero.
        db.query(Execution).delete()
        # MODIFICACIÓN 2026-11-18 - M03 / CP-06
        # Se limpian primero las tablas de generación para respetar las FK.
        db.query(GeneratedData).delete()
        db.query(CaseRule).delete()
        db.query(TestCase).delete()
        db.query(Generation).delete()
        db.query(RuleParameter).delete()
        db.query(RuleField).delete()
        db.query(BusinessRule).delete()
        db.query(DataField).delete()
        db.query(Audit).delete()
        db.query(DataModel).delete()
        db.query(Project).delete()
        db.query(User).delete()
        db.query(Role).delete()
        db.query(DataType).delete()
        db.query(RuleType).delete()
        db.commit()

        admin_role = Role(nombre="Administrador", descripcion="Admin", estado=True)
        tester_role = Role(nombre="Analista/Tester", descripcion="Tester", estado=True)
        db.add_all([admin_role, tester_role])
        db.flush()

        db.add_all(
            [
                User(
                    rol_id=admin_role.rol_id,
                    nombre="Ana",
                    apellido="Admin",
                    email="admin@test.local",
                    password_hash=hash_password("Admin123!"),
                    estado=True,
                ),
                User(
                    rol_id=tester_role.rol_id,
                    nombre="Tania",
                    apellido="Tester",
                    email="tester@test.local",
                    password_hash=hash_password("Tester123!"),
                    estado=True,
                ),
                User(
                    rol_id=tester_role.rol_id,
                    nombre="Inactivo",
                    apellido="Tester",
                    email="inactivo@test.local",
                    password_hash=hash_password("Inactivo123!"),
                    estado=False,
                ),
            ]
        )

        db.add_all(
            [
                DataType(codigo="STRING", nombre="Texto", descripcion="Cadena de texto.", estado=True),
                DataType(codigo="INTEGER", nombre="Entero", descripcion="Número entero.", estado=True),
                DataType(codigo="DECIMAL", nombre="Decimal", descripcion="Número decimal.", estado=True),
                DataType(codigo="DATE", nombre="Fecha", descripcion="Fecha.", estado=True),
                DataType(codigo="BOOLEAN", nombre="Booleano", descripcion="Valor lógico.", estado=True),
                DataType(codigo="EMAIL", nombre="Correo", descripcion="Correo electrónico.", estado=True),
            ]
        )

        db.add_all(
            [
                RuleType(codigo="REQUIRED", nombre="Obligatoriedad", descripcion="Campo obligatorio.", estado=True),
                RuleType(codigo="RANGE", nombre="Rango", descripcion="Mínimo y máximo.", estado=True),
                RuleType(codigo="ALLOWED_VALUES", nombre="Valores permitidos", descripcion="Lista de valores.", estado=True),
                RuleType(codigo="FORMAT", nombre="Formato / longitud", descripcion="Patrón o longitud.", estado=True),
                RuleType(codigo="COMPARISON", nombre="Comparación entre campos", descripcion="Compara campos.", estado=True),
                RuleType(codigo="CONDITIONAL", nombre="Condicional simple", descripcion="Condición simple.", estado=True),
            ]
        )
        db.commit()


@pytest.fixture()
def client():
    return TestClient(app)
