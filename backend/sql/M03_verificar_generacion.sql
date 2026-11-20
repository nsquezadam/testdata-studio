-- ============================================================
-- TESTDATA STUDIO - M03 / CP-06
-- VERIFICACIÓN DE TRAZABILIDAD
-- CREACIÓN 2026-11-18
-- ============================================================

-- 1. Generaciones realizadas.
SELECT
    g.generacion_id,
    g.modelo_id,
    g.usuario_id,
    g.cantidad_solicitada,
    g.estado,
    g.fecha_generacion
FROM generacion g
ORDER BY g.generacion_id DESC;

-- 2. Casos y resultado esperado.
SELECT
    cp.caso_prueba_id,
    cp.generacion_id,
    cp.tipo_escenario,
    cp.resultado_esperado,
    cp.fecha_creacion
FROM caso_prueba cp
ORDER BY cp.caso_prueba_id DESC;

-- 3. Trazabilidad Regla -> Escenario -> Resultado esperado.
SELECT
    cp.caso_prueba_id,
    cp.tipo_escenario,
    r.regla_id,
    r.nombre AS regla,
    cr.cumple_esperado,
    cr.detalle_esperado,
    cp.resultado_esperado
FROM caso_prueba cp
JOIN caso_regla cr ON cr.caso_prueba_id = cp.caso_prueba_id
JOIN regla r ON r.regla_id = cr.regla_id
ORDER BY cp.caso_prueba_id, r.regla_id;

-- 4. Datos generados por escenario.
SELECT
    cp.caso_prueba_id,
    cp.tipo_escenario,
    c.campo_id,
    c.nombre AS campo,
    dg.valor_generado
FROM caso_prueba cp
JOIN dato_generado dg ON dg.caso_prueba_id = cp.caso_prueba_id
JOIN campo c ON c.campo_id = dg.campo_id
ORDER BY cp.caso_prueba_id, c.orden, c.campo_id;
