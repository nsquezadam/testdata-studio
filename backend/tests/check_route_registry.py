"""Verificación manual de registro de rutas - 2026-11-20."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import app

EXPECTED = {
    "/api/data-types",
    "/api/rule-types",
    "/api/models/{modelo_id}/fields",
    "/api/models/{modelo_id}/rules",
    "/api/models/{modelo_id}/generation-readiness",
    "/api/generations",
}

paths = set(app.openapi()["paths"].keys())
missing = sorted(EXPECTED - paths)
print("Rutas esperadas:")
for path in sorted(EXPECTED):
    print(("OK   " if path in paths else "FALTA"), path)

if missing:
    raise SystemExit(f"Faltan rutas: {missing}")

print("Registro de rutas correcto.")
