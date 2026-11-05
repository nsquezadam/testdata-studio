from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)


@app.get("/")
def root():
    return {
        "aplicacion": "TestData Studio",
        "mensaje": "API funcionando correctamente"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.get("/db-health")
def database_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "database": "testdata_studio",
            "status": "conectada"
        }

    except Exception as error:
        return {
            "database": "testdata_studio",
            "status": "error",
            "detalle": str(error)
        }