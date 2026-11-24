# TestData Studio — Cierre de pruebas automatizadas

Fecha: 2026-11-21

Este paquete complementa los 10 casos manuales ya cerrados con tres capas automáticas:

1. **Pytest** — regresión backend (FastAPI / lógica de negocio).
2. **Selenium** — pruebas E2E visibles sobre Login, roles, navegación y logout.
3. **JMeter** — rendimiento, carga y estrés sobre la API.

## Orden recomendado

1. Ejecutar pytest y conservar XML/log.
2. Levantar backend + frontend y ejecutar Selenium.
3. Mantener backend levantado y ejecutar JMeter JM-01, JM-02 y JM-03.
4. Reunir evidencias y recién entonces actualizar la planilla de seguimiento.

## Pytest

Desde `backend/`:

```bash
pytest -q --junitxml=../automation/resultados/pytest_regresion.xml
```

La suite actual cubre autenticación, M02, M03 y M04.

## Selenium

Ver `automation/selenium/README_SELENIUM.md`.

## JMeter

Ver `automation/jmeter/README_JMETER.md`.

## Nota sobre JUnit

El proyecto backend es Python y usa pytest. No se incorpora el framework JUnit de Java.
Si una plataforma académica solicita un reporte en formato JUnit XML, pytest puede generarlo con `--junitxml`, sin cambiar el framework de pruebas.
