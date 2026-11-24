# TestData Studio — Selenium E2E

Creado: 2026-11-21.

Estas pruebas complementan la regresión backend con una verificación real del navegador.
No almacenan credenciales dentro del repositorio.

## Casos

- SEL-01: Login Administrador + Dashboard administrativo.
- SEL-02: Login Analista/Tester + Dashboard operativo.
- SEL-03: Navegación Analista/Tester hacia Generación y Resultados.
- SEL-04: Cierre de sesión y retorno al Login.

## Requisitos

1. Backend levantado en `http://127.0.0.1:8000`.
2. Frontend levantado en `http://localhost:5173`.
3. Google Chrome instalado.
4. Entorno virtual Python activo.

Instalar Selenium:

```bash
pip install -r automation/selenium/requirements.txt
```

## Credenciales — Git Bash

No guardar contraseñas en Git.

```bash
export SELENIUM_ADMIN_EMAIL="admin@testdata.local"
export SELENIUM_ADMIN_PASSWORD="TU_CLAVE_ADMIN"
export SELENIUM_TESTER_EMAIL="tester@testdata.local"
export SELENIUM_TESTER_PASSWORD="TU_CLAVE_TESTER"
```

Opcional:

```bash
export SELENIUM_BASE_URL="http://localhost:5173"
export SELENIUM_HEADLESS=0
```

## Ejecutar

Desde la raíz `~/proyectoTit`:

```bash
pytest -q automation/selenium --junitxml=automation/resultados/selenium_e2e.xml
```

Las capturas quedan en:

`automation/selenium/evidencias/`

Selenium 4 utiliza Selenium Manager para resolver el controlador de Chrome cuando es necesario.
