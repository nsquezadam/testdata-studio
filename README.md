# TestData Studio

**Plataforma web para la generación y seguimiento de datos de prueba basados en reglas de negocio.**

Proyecto de título de Ingeniería en Informática.

## Descripción

TestData Studio permite crear proyectos y modelos de datos, configurar campos y reglas de negocio, generar escenarios de prueba válidos, inválidos y límite, exportar datos y registrar los resultados obtenidos durante una ejecución externa.

La trazabilidad principal del sistema es:

**Regla de negocio → Escenario → Dato generado → Resultado esperado → Resultado obtenido → Estado**

## Módulos

- **M01 – Proyectos y Modelos:** administración de proyectos y modelos de datos.
- **M02 – Campos y Reglas:** configuración de campos y reglas REQUIRED, RANGE, ALLOWED_VALUES, FORMAT, COMPARISON y CONDITIONAL.
- **M03 – Generación:** generación de escenarios y datos, trazabilidad y exportación CSV/JSON.
- **M04 – Ejecución y Resultados:** registro manual/importación CSV, clasificación y dashboard de seguimiento.
- **Transversal:** autenticación JWT, perfiles Administrador y Analista/Tester, auditoría lógica y seguridad.

## Tecnologías

**Frontend:** React 19, Vite 8 y CSS.\
**Backend:** Python, FastAPI, SQLAlchemy y PostgreSQL.\
**Seguridad:** JWT y hash de contraseñas.\
**Testing:** pytest, Selenium y Apache JMeter.\
**Persistencia utilizada en el proyecto:** PostgreSQL/Neon.

## Inicio rápido

La instalación completa está documentada en [INSTALLATION.md](INSTALLATION.md).

Resumen:

```bash
# 1) Backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env

# 2) Base de datos
# Crear testdata_studio y ejecutar:
# backend/sql/TestData_Studio_PostgreSQL.sql

# 3) Usuarios demo
cd backend
python scripts/seed_demo_users.py
uvicorn app.main:app --reload

# 4) Frontend (otra terminal)
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Aplicación local: `http://localhost:5173`\
API: `http://127.0.0.1:8000`\
Swagger/OpenAPI: `http://127.0.0.1:8000/docs`

## Pruebas

Regresión backend:

```bash
cd backend
pytest -q
```

Estado de cierre validado el 2026-11-21: **54 pruebas backend aprobadas**.

Las pruebas E2E y no funcionales están en `automation/`:

- Selenium: 4 escenarios E2E.
- JMeter JM-01: rendimiento RNF02/RNF03.
- JMeter JM-02: carga con 10 usuarios.
- JMeter JM-03: estrés incremental 10 → 25 → 50 usuarios.
- SEG-01: 8 controles automáticos asociados a RNF01 Seguridad.

## Usuarios y contraseñas

Los usuarios se almacenan en PostgreSQL y sus contraseñas se guardan mediante hash.

Las variables `ADMIN_PASSWORD`, `TESTER_PASSWORD`, `TESTER2_PASSWORD` y `TESTER3_PASSWORD` de `backend/.env` se utilizan únicamente cuando se ejecuta el script `seed_demo_users.py` para una instalación nueva.

**Cambiar una contraseña en `.env` no actualiza un usuario que ya existe.** Para usuarios existentes, utilizar **Gestión de usuarios** con perfil Administrador.

## Estructura principal

```text
proyectoTit/
├── backend/          API, modelos, servicios, SQL y pruebas pytest
├── frontend/         aplicación React/Vite
├── automation/       Selenium y JMeter
├── docs/             documentación académica y diagramas
├── evidencias/       evidencias seleccionadas del proyecto
├── database/         material complementario de base de datos
├── design/           material de diseño
├── INSTALLATION.md   instalación y preparación del paquete
├── README.md
└── .gitignore
```

## Seguridad de archivos

No se deben compartir ni subir al repositorio:

- `backend/.env` o `frontend/.env`.
- `.venv/`.
- `node_modules/`.
- `automation/jmeter/local.properties`.
- logs, cachés y contraseñas reales.

Los archivos `.env.example` sí forman parte del proyecto y contienen únicamente valores de ejemplo.
