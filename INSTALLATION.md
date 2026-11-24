# Instalación y ejecución de TestData Studio

Esta guía permite instalar el proyecto desde un ZIP limpio o desde el repositorio Git.

## 1. Requisitos previos

- **Python 3.11 o superior**.
- **Node.js 20.19+ o 22.12+** (requisito de Vite 8).
- **PostgreSQL** local o una base PostgreSQL compatible, por ejemplo Neon.
- Git opcional.
- Google Chrome únicamente si se ejecutarán pruebas Selenium.
- Apache JMeter 5.6.3 únicamente si se ejecutarán pruebas de rendimiento/carga/estrés.

No se distribuyen `.venv` ni `node_modules`; cada equipo debe instalar sus dependencias.

## 2. Descomprimir

Descomprimir el proyecto en una carpeta sin copiar configuraciones privadas de otro equipo.

Ejemplo:

```bash
cd /c/Users/TU_USUARIO
cd proyectoTit
```

## 3. Backend

Desde la raíz del proyecto:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

En PowerShell, la activación equivalente es:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 4. Variables del backend

Copiar el archivo de ejemplo:

```bash
cp backend/.env.example backend/.env
```

Editar `backend/.env` y configurar como mínimo:

- `DATABASE_URL`
- `JWT_SECRET`
- `FRONTEND_ORIGIN`
- credenciales iniciales para Admin y Testers si se utilizará el seed.

Generar una clave JWT robusta:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

No compartir el archivo `.env`.

## 5. Base de datos

Crear una base llamada `testdata_studio` cuando se utilice PostgreSQL local.

Después ejecutar el script consolidado:

```text
backend/sql/TestData_Studio_PostgreSQL.sql
```

El script crea las 16 tablas utilizadas por la aplicación y carga los catálogos base:

- roles Administrador y Analista/Tester;
- seis tipos de datos;
- seis tipos de reglas.

> Importante: para una instalación nueva se debe utilizar este script consolidado. Los scripts M02/M03/M04 separados quedan como historial técnico de evolución y no son necesarios después del script final.

## 6. Usuarios iniciales

Con `backend/.env` ya configurado:

```bash
cd backend
python scripts/seed_demo_users.py
```

El seed puede crear:

- 1 Administrador.
- 3 Analista/Tester.

Si un correo ya existe, el script no modifica su contraseña.

Para cambiar la contraseña de un usuario existente, iniciar sesión como Administrador y utilizar **Gestión de usuarios**.

## 7. Iniciar backend

Desde `backend/`:

```bash
uvicorn app.main:app --reload
```

Verificar:

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

## 8. Frontend

En otra terminal:

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

El archivo `frontend/.env` local debe contener:

```env
VITE_API_URL=http://localhost:8000/api
```

Abrir:

```text
http://localhost:5173
```

## 9. Validación mínima después de instalar

Backend:

```bash
cd backend
pytest -q
```

Resultado de referencia del cierre técnico:

```text
54 passed
```

Frontend:

```bash
cd frontend
npm run build
```

## 10. Pruebas Selenium opcionales

Con backend y frontend levantados:

```bash
pip install -r automation/selenium/requirements.txt
```

Configurar las credenciales solo en la terminal:

```bash
export SELENIUM_ADMIN_EMAIL="admin@testdata.local"
export SELENIUM_ADMIN_PASSWORD="TU_CLAVE"
export SELENIUM_TESTER_EMAIL="tester@testdata.local"
export SELENIUM_TESTER_PASSWORD="TU_CLAVE"
```

Ejecutar:

```bash
pytest -q automation/selenium
```

## 11. JMeter opcional

Los planes se encuentran en `automation/jmeter/`.

No almacenar contraseñas reales en los archivos `.jmx` ni en Git.

## 12. Configuración de despliegue

### Backend

Ejemplo de servicio web:

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Variables requeridas en el servicio:

- `DATABASE_URL`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_MINUTES`
- `FRONTEND_ORIGIN` con la URL pública del frontend.

### Frontend

```text
Root Directory: frontend
Build Command: npm ci && npm run build
Publish Directory: dist
```

Variable:

```text
VITE_API_URL=https://TU-BACKEND/api
```

Después de cambiar una variable de entorno del frontend se debe realizar un nuevo build/deploy.

## 13. Cómo preparar el ZIP de entrega

El ZIP final debe incluir código fuente, scripts de instalación, documentación seleccionada y evidencias finales, pero debe excluir:

```text
.git/
.venv/
backend/.venv/
frontend/node_modules/
backend/.env
frontend/.env
automation/jmeter/local.properties
__pycache__/
.pytest_cache/
*.log
```

También conviene excluir resultados temporales o evidencias antiguas que hayan sido reemplazadas por las capturas finales.

## 14. Comprobación antes de compartir

1. Descomprimir una copia del ZIP en una carpeta temporal.
2. Confirmar que no existan `.env` reales ni contraseñas.
3. Confirmar que `README.md`, `INSTALLATION.md`, `.env.example`, SQL y `package-lock.json` estén presentes.
4. Crear un entorno virtual nuevo e instalar el backend.
5. Ejecutar `npm ci` en frontend.
6. Ejecutar `pytest -q` y `npm run build`.
7. Levantar la aplicación y realizar un login de prueba.
