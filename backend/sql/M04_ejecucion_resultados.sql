-- ============================================================
-- CREACIÓN 2026-11-20 - M04 / CP-08
-- Tabla de ejecuciones externas registradas en TestData Studio.
-- No ejecuta pruebas; conserva resultado observado, origen y clasificación.
-- ============================================================

CREATE TABLE IF NOT EXISTS ejecucion (
    ejecucion_id BIGSERIAL PRIMARY KEY,
    caso_prueba_id BIGINT NOT NULL REFERENCES caso_prueba(caso_prueba_id),
    usuario_id BIGINT NOT NULL REFERENCES usuario(usuario_id),
    origen_registro VARCHAR(20) NOT NULL DEFAULT 'MANUAL',
    resultado_obtenido TEXT NULL,
    estado VARCHAR(20) NOT NULL,
    observacion VARCHAR(1000) NULL,
    fecha_ejecucion TIMESTAMP NOT NULL,
    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_ejecucion_origen_registro CHECK (origen_registro IN ('MANUAL','CSV')),
    CONSTRAINT chk_ejecucion_estado CHECK (estado IN ('APROBADO','FALLIDO','BLOQUEADO'))
);

CREATE INDEX IF NOT EXISTS ix_ejecucion_caso_prueba_id
    ON ejecucion(caso_prueba_id);

CREATE INDEX IF NOT EXISTS ix_ejecucion_estado
    ON ejecucion(estado);


--*********************************************
-- CONSULTAS PERSISTENCIA
--********************************************
--EJECUCIONES_REGISTRADAS
SELECT
    ejecucion_id,
    caso_prueba_id,
    usuario_id,
    origen_registro,
    resultado_obtenido,
    estado,
    observacion,
    fecha_ejecucion,
    fecha_registro
FROM ejecucion
ORDER BY ejecucion_id;

-- REVISION EJECUCION CON EL CASO

SELECT
    e.ejecucion_id,
    cp.caso_prueba_id,
    cp.generacion_id,
    cp.tipo_escenario,
    cp.resultado_esperado,
    e.resultado_obtenido,
    e.estado,
    e.origen_registro,
    e.observacion,
    e.fecha_ejecucion,
    e.fecha_registro
FROM ejecucion e
JOIN caso_prueba cp
    ON cp.caso_prueba_id = e.caso_prueba_id
ORDER BY e.ejecucion_id;

--REVISION POR  ID
SELECT
    cp.caso_prueba_id,
    cp.resultado_esperado,
    e.resultado_obtenido,
    e.estado,
    e.origen_registro,
    e.observacion,
    e.fecha_ejecucion
FROM caso_prueba cp
LEFT JOIN ejecucion e
    ON e.caso_prueba_id = cp.caso_prueba_id
WHERE cp.caso_prueba_id = 13;

--VALIDACION ESTADOS
SELECT
    estado,
    COUNT(*) AS total
FROM ejecucion
GROUP BY estado
ORDER BY estado;