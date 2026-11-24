TESTDATA STUDIO - INC-03
Fecha: 2026-11-18

Problema detectado
------------------
Durante CP-05 Frontend, React mostró el warning "Each child in a list should have a unique key prop" y la creación de un campo terminó en HTTP 422.

Causa
-----
Los endpoints GET /api/data-types y GET /api/rule-types devolvían el identificador como "id", mientras CamposRulesPage esperaba "tipo_dato_id" y "tipo_regla_id". El <option> quedó con key/value indefinidos y el POST terminó enviando tipo_dato_id nulo.

Corrección
----------
- app/schemas/configuration.py: respuestas específicas para catálogos.
- app/api/routes/configuration.py: devuelve tipo_dato_id / tipo_regla_id.
- tests/test_m02_configuration.py: regresión del contrato de catálogos.

No se modifican tablas ni datos de PostgreSQL.
