-- ============================================================
-- INC-02 - Evitar órdenes duplicados de campos dentro de un modelo
-- TestData Studio / M02
-- Fecha: 2026-11-18
-- Motivo: impedir (modelo_id, orden) duplicado detectado en CP-05 Frontend.
-- ============================================================

-- 1) Revisar duplicados antes de crear la restricción.
SELECT
    modelo_id,
    orden,
    COUNT(*) AS cantidad,
    STRING_AGG(campo_id::text || ' - ' || nombre, ', ' ORDER BY campo_id) AS campos
FROM campo
WHERE orden IS NOT NULL
GROUP BY modelo_id, orden
HAVING COUNT(*) > 1
ORDER BY modelo_id, orden;

-- IMPORTANTE:
-- Si la consulta anterior devuelve registros, corregir primero esos órdenes
-- desde la aplicación o mediante un UPDATE controlado.
-- Ejemplo observado durante CP-05 FE:
-- id_marca orden 1 / marca orden 1 -> dejar id_marca=1 y asignar marca=2.

-- 2) Ejecutar este bloque SOLO cuando la consulta anterior no devuelva duplicados.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_campo_modelo_orden'
    ) THEN
        ALTER TABLE campo
        ADD CONSTRAINT uq_campo_modelo_orden
        UNIQUE (modelo_id, orden);
    END IF;
END $$;

-- 3) Verificación final.
SELECT
    conname,
    pg_get_constraintdef(oid) AS definicion
FROM pg_constraint
WHERE conname = 'uq_campo_modelo_orden';
