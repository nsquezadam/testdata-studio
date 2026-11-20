from fastapi import FastAPI

# ============================================================
# MODIFICACIÓN 2026-11-20 - REGISTRO DE ROUTERS
# Se verifica el registro único de los routers configuration y generation.
# Motivo: durante CP-06 Frontend se detectó 404 en /api/models/{id}/rules
# y advertencias de Operation ID duplicado para generation.
# ============================================================

from fastapi.middleware.cors import CORSMiddleware

# MODIFICACIÓN 2026-11-18 - M03 / CP-06
# Se incorpora el router de generación de datos y escenarios.
# Motivo: habilitar HU-05 / RF08-RF10 sin mezclar aún la exportación CP-07.
from app.api.routes import auth, health, secure_demo, users, projects, configuration, generation
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API REST de TestData Studio - DEV v1 Autenticación y perfiles",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(secure_demo.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(projects.router, prefix=settings.api_prefix)
app.include_router(configuration.router, prefix=settings.api_prefix)
app.include_router(generation.router, prefix=settings.api_prefix)

@app.get("/")
def root():
    return {
        "app": "TestData Studio",
        "version": "DEV v1",
        "docs": "/docs",
    }
