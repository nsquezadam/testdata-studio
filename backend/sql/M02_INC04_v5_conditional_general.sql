-- ============================================================
-- MODIFICACIÓN 2026-11-18 - INC-04 v5 / CONDITIONAL GENERAL
-- TestData Studio - M02 Campos y Reglas
--
-- Objetivo:
-- 1) Normalizar roles antiguos de COMPARISON (ORIGEN/DESTINO).
-- 2) Actualizar la descripción funcional de CONDITIONAL.
-- 3) Identificar reglas CONDITIONAL heredadas que aún deben ser
--    completadas desde el frontend con SI / ENTONCES.
--
-- IMPORTANTE:
-- No se modifica automáticamente una regla CONDITIONAL heredada,
-- porque no es posible inferir de forma segura cuál debe ser el
-- campo objetivo ni la consecuencia elegida por el usuario.
-- ============================================================

-- Normalización segura de COMPARISON creada en iteraciones anteriores.
UPDATE regla_campo rc
SET rol_campo = 'PRINCIPAL'
FROM regla r
JOIN tipo_regla tr ON tr.tipo_regla_id = r.tipo_regla_id
WHERE rc.regla_id = r.regla_id
  AND tr.codigo = 'COMPARISON'
  AND rc.rol_campo = 'ORIGEN';

UPDATE regla_campo rc
SET rol_campo = 'REFERENCIA'
FROM regla r
JOIN tipo_regla tr ON tr.tipo_regla_id = r.tipo_regla_id
WHERE rc.regla_id = r.regla_id
  AND tr.codigo = 'COMPARISON'
  AND rc.rol_campo = 'DESTINO';

-- Descripción funcional definitiva de CONDITIONAL para el MVP.
UPDATE tipo_regla
SET descripcion =
    'Evalúa una condición sobre un campo y, cuando se cumple, aplica una consecuencia configurable sobre otro campo.'
WHERE codigo = 'CONDITIONAL';

-- Diagnóstico de reglas CONDITIONAL heredadas.
-- Si esta consulta devuelve filas, edítalas desde el nuevo formulario
-- del frontend para completar Campo condición + Campo objetivo + Consecuencia.
SELECT
    r.regla_id,
    r.nombre,
    r.estado,
    COUNT(DISTINCT rc.campo_id) AS cantidad_campos,
    STRING_AGG(DISTINCT rc.rol_campo, ', ' ORDER BY rc.rol_campo) AS roles,
    STRING_AGG(DISTINCT rp.clave, ', ' ORDER BY rp.clave) AS parametros
FROM regla r
JOIN tipo_regla tr
    ON tr.tipo_regla_id = r.tipo_regla_id
LEFT JOIN regla_campo rc
    ON rc.regla_id = r.regla_id
LEFT JOIN regla_parametro rp
    ON rp.regla_id = r.regla_id
WHERE tr.codigo = 'CONDITIONAL'
GROUP BY r.regla_id, r.nombre, r.estado
HAVING
    COUNT(DISTINCT rc.campo_id) <> 2
    OR NOT BOOL_OR(rc.rol_campo = 'CONDICION')
    OR NOT BOOL_OR(rc.rol_campo = 'PRINCIPAL')
    OR NOT BOOL_OR(rp.clave = 'accion')
ORDER BY r.regla_id;
