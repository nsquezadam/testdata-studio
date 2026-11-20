-- ============================================================
-- TestData Studio - M02 / INC-04
-- Fecha: 2026-11-18
-- Objetivo:
--   Normalizar reglas COMPARISON creadas durante iteraciones anteriores.
--   El contrato definitivo utiliza roles PRINCIPAL y REFERENCIA.
-- Motivo:
--   El frontend anterior almacenó algunas asociaciones como ORIGEN/DESTINO,
--   mientras FastAPI valida PRINCIPAL/REFERENCIA.
-- ============================================================

-- 1. Revisar reglas COMPARISON que todavía usan nomenclatura anterior.
SELECT
    r.regla_id,
    r.nombre,
    rc.campo_id,
    rc.rol_campo
FROM regla r
JOIN tipo_regla tr
    ON tr.tipo_regla_id = r.tipo_regla_id
JOIN regla_campo rc
    ON rc.regla_id = r.regla_id
WHERE tr.codigo = 'COMPARISON'
  AND rc.rol_campo IN ('ORIGEN', 'DESTINO')
ORDER BY r.regla_id, rc.campo_id;

-- 2. Normalizar roles heredados.
UPDATE regla_campo rc
SET rol_campo = 'PRINCIPAL'
FROM regla r, tipo_regla tr
WHERE rc.regla_id = r.regla_id
  AND tr.tipo_regla_id = r.tipo_regla_id
  AND tr.codigo = 'COMPARISON'
  AND rc.rol_campo = 'ORIGEN';

UPDATE regla_campo rc
SET rol_campo = 'REFERENCIA'
FROM regla r, tipo_regla tr
WHERE rc.regla_id = r.regla_id
  AND tr.tipo_regla_id = r.tipo_regla_id
  AND tr.codigo = 'COMPARISON'
  AND rc.rol_campo = 'DESTINO';

-- 3. Verificar reglas CONDITIONAL heredadas.
-- No se modifican automáticamente porque no es posible inferir qué campo
-- debe actuar como CONDICION. Si una regla aparece aquí, debe editarse desde
-- el frontend y completar "Campo que será obligatorio" y "Campo condición".
SELECT
    r.regla_id,
    r.nombre,
    COUNT(rc.campo_id) AS cantidad_campos,
    STRING_AGG(rc.rol_campo, ', ' ORDER BY rc.rol_campo) AS roles
FROM regla r
JOIN tipo_regla tr
    ON tr.tipo_regla_id = r.tipo_regla_id
LEFT JOIN regla_campo rc
    ON rc.regla_id = r.regla_id
WHERE tr.codigo = 'CONDITIONAL'
GROUP BY r.regla_id, r.nombre
HAVING COUNT(rc.campo_id) <> 2
    OR NOT (
        BOOL_OR(rc.rol_campo = 'PRINCIPAL')
        AND BOOL_OR(rc.rol_campo = 'CONDICION')
    )
ORDER BY r.regla_id;
