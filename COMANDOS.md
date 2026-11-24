# Comandos útiles — TestData Studio

## Git

```bash
git status
git diff
git log --oneline --decorate -10
git add <archivo>
git commit -m "tipo: descripción"
git push origin main
```

Convenciones utilizadas:

- `feat:` nueva funcionalidad.
- `fix:` corrección funcional.
- `perf:` mejora de rendimiento.
- `test:` incorporación o ajuste de pruebas.
- `docs:` documentación.
- `chore:` mantenimiento/configuración.

## Backend

```bash
source .venv/Scripts/activate
cd backend
uvicorn app.main:app --reload
pytest -q
```

## Frontend

```bash
cd frontend
npm ci
npm run dev
npm run build
```

## Selenium

```bash
pytest -q automation/selenium --junitxml=automation/resultados/selenium_e2e.xml
```

## JMeter

```bash
jmeter -v
```

Los comandos completos de JM-01, JM-02 y JM-03 están documentados en `automation/jmeter/README_JMETER.md`.

## Estructura del proyecto sin dependencias

Git Bash:

```bash
find . -maxdepth 4 \
  -not -path './.git/*' \
  -not -path './.venv/*' \
  -not -path './frontend/node_modules/*' \
  -not -path './backend/.venv/*' \
  | sort
```
