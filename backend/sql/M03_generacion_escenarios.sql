-- ============================================================
-- TESTDATA STUDIO - M03 GENERACIÓN DE DATOS Y ESCENARIOS
-- CREACIÓN 2026-11-19 - CP-06 / HU-05 / RF08-RF10
--
-- Crea las tablas definidas en el modelo relacional para conservar:
-- modelo -> generación -> caso -> dato / regla -> resultado esperado.
-- No incluye EJECUCION (M04) ni exportación (CP-07 / RF11).
-- ============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS generacion (
    generacion_id BIGSERIAL PRIMARY KEY,
    modelo_id BIGINT NOT NULL,
    usuario_id BIGINT NOT NULL,
    cantidad_solicitada INTEGER NOT NULL,
    fecha_generacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(30) NOT NULL DEFAULT 'PENDIENTE',

    CONSTRAINT fk_generacion_modelo
        FOREIGN KEY (modelo_id) REFERENCES modelo(modelo_id),
    CONSTRAINT fk_generacion_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuario(usuario_id),
    CONSTRAINT chk_generacion_cantidad_positiva
        CHECK (cantidad_solicitada > 0),
    CONSTRAINT chk_generacion_estado
        CHECK (estado IN ('PENDIENTE','COMPLETADA','ERROR'))
);

CREATE TABLE IF NOT EXISTS caso_prueba (
    caso_prueba_id BIGSERIAL PRIMARY KEY,
    generacion_id BIGINT NOT NULL,
    tipo_escenario VARCHAR(20) NOT NULL,
    resultado_esperado VARCHAR(500) NOT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_caso_prueba_generacion
        FOREIGN KEY (generacion_id) REFERENCES generacion(generacion_id),
    CONSTRAINT chk_caso_prueba_tipo_escenario
        CHECK (tipo_escenario IN ('VALIDO','INVALIDO','LIMITE'))
);

CREATE TABLE IF NOT EXISTS caso_regla (
    caso_prueba_id BIGINT NOT NULL,
    regla_id BIGINT NOT NULL,
    cumple_esperado BOOLEAN NOT NULL,
    detalle_esperado VARCHAR(500),

    CONSTRAINT pk_caso_regla PRIMARY KEY (caso_prueba_id, regla_id),
    CONSTRAINT fk_caso_regla_caso
        FOREIGN KEY (caso_prueba_id) REFERENCES caso_prueba(caso_prueba_id),
    CONSTRAINT fk_caso_regla_regla
        FOREIGN KEY (regla_id) REFERENCES regla(regla_id)
);

CREATE TABLE IF NOT EXISTS dato_generado (
    dato_generado_id BIGSERIAL PRIMARY KEY,
    caso_prueba_id BIGINT NOT NULL,
    campo_id BIGINT NOT NULL,
    valor_generado TEXT,

    CONSTRAINT fk_dato_generado_caso
        FOREIGN KEY (caso_prueba_id) REFERENCES caso_prueba(caso_prueba_id),
    CONSTRAINT fk_dato_generado_campo
        FOREIGN KEY (campo_id) REFERENCES campo(campo_id),
    CONSTRAINT uq_dato_generado_caso_campo
        UNIQUE (caso_prueba_id, campo_id)
);

CREATE INDEX IF NOT EXISTS idx_generacion_modelo ON generacion(modelo_id);
CREATE INDEX IF NOT EXISTS idx_generacion_usuario ON generacion(usuario_id);
CREATE INDEX IF NOT EXISTS idx_caso_prueba_generacion ON caso_prueba(generacion_id);
CREATE INDEX IF NOT EXISTS idx_caso_regla_regla ON caso_regla(regla_id);
CREATE INDEX IF NOT EXISTS idx_dato_generado_campo ON dato_generado(campo_id);

COMMIT;

-- Validación rápida de estructura.
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('generacion', 'caso_prueba', 'caso_regla', 'dato_generado')
ORDER BY table_name;
