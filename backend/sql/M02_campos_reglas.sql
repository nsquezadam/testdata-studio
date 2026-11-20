-- ============================================================
-- TESTDATA STUDIO - M02 CAMPOS Y REGLAS
-- Compatible con el backend actual:
-- proyecto(usuario_id) y modelo(modelo_id)
-- ============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS tipo_dato (
    tipo_dato_id BIGSERIAL PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL UNIQUE,
    nombre VARCHAR(50) NOT NULL,
    descripcion VARCHAR(200),
    estado BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS campo (
    campo_id BIGSERIAL PRIMARY KEY,
    modelo_id BIGINT NOT NULL,
    tipo_dato_id BIGINT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(250),
    orden INTEGER,
    estado BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_campo_modelo
        FOREIGN KEY (modelo_id)
        REFERENCES modelo(modelo_id),

    CONSTRAINT fk_campo_tipo_dato
        FOREIGN KEY (tipo_dato_id)
        REFERENCES tipo_dato(tipo_dato_id),

    CONSTRAINT uq_campo_modelo_nombre
        UNIQUE (modelo_id, nombre),

    CONSTRAINT chk_campo_orden
        CHECK (orden IS NULL OR orden > 0)
);

CREATE TABLE IF NOT EXISTS tipo_regla (
    tipo_regla_id BIGSERIAL PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(300),
    estado BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS regla (
    regla_id BIGSERIAL PRIMARY KEY,
    modelo_id BIGINT NOT NULL,
    tipo_regla_id BIGINT NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    descripcion VARCHAR(500),
    estado BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_regla_modelo
        FOREIGN KEY (modelo_id)
        REFERENCES modelo(modelo_id),

    CONSTRAINT fk_regla_tipo
        FOREIGN KEY (tipo_regla_id)
        REFERENCES tipo_regla(tipo_regla_id),

    CONSTRAINT uq_regla_modelo_nombre
        UNIQUE (modelo_id, nombre)
);

CREATE TABLE IF NOT EXISTS regla_campo (
    regla_id BIGINT NOT NULL,
    campo_id BIGINT NOT NULL,
    rol_campo VARCHAR(30) NOT NULL,

    CONSTRAINT pk_regla_campo
        PRIMARY KEY (regla_id, campo_id, rol_campo),

    CONSTRAINT fk_regla_campo_regla
        FOREIGN KEY (regla_id)
        REFERENCES regla(regla_id),

    CONSTRAINT fk_regla_campo_campo
        FOREIGN KEY (campo_id)
        REFERENCES campo(campo_id)
);

CREATE TABLE IF NOT EXISTS regla_parametro (
    parametro_id BIGSERIAL PRIMARY KEY,
    regla_id BIGINT NOT NULL,
    clave VARCHAR(50) NOT NULL,
    valor VARCHAR(500) NOT NULL,
    orden INTEGER,

    CONSTRAINT fk_regla_parametro_regla
        FOREIGN KEY (regla_id)
        REFERENCES regla(regla_id),

    CONSTRAINT chk_regla_parametro_orden
        CHECK (orden IS NULL OR orden >= 1)
);

CREATE INDEX IF NOT EXISTS idx_campo_modelo ON campo(modelo_id);
CREATE INDEX IF NOT EXISTS idx_campo_tipo ON campo(tipo_dato_id);
CREATE INDEX IF NOT EXISTS idx_regla_modelo ON regla(modelo_id);
CREATE INDEX IF NOT EXISTS idx_regla_tipo ON regla(tipo_regla_id);
CREATE INDEX IF NOT EXISTS idx_regla_campo_campo ON regla_campo(campo_id);
CREATE INDEX IF NOT EXISTS idx_regla_parametro_regla ON regla_parametro(regla_id);

INSERT INTO tipo_dato (codigo, nombre, descripcion, estado)
VALUES
    ('STRING',  'Texto', 'Cadena de texto.', TRUE),
    ('INTEGER', 'Entero', 'Número entero.', TRUE),
    ('DECIMAL', 'Decimal', 'Número decimal.', TRUE),
    ('DATE',    'Fecha', 'Fecha.', TRUE),
    ('BOOLEAN', 'Booleano', 'Valor lógico verdadero/falso.', TRUE),
    ('EMAIL',   'Correo', 'Dirección de correo electrónico.', TRUE)
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO tipo_regla (codigo, nombre, descripcion, estado)
VALUES
    ('REQUIRED',       'Obligatoriedad',           'Valida presencia u obligatoriedad del campo.', TRUE),
    ('RANGE',          'Rango',                    'Valida valores mínimos y máximos.', TRUE),
    ('ALLOWED_VALUES', 'Valores permitidos',       'Valida pertenencia a una lista de valores.', TRUE),
    ('FORMAT',         'Formato / longitud',       'Valida formato, patrón o longitud.', TRUE),
    ('COMPARISON',     'Comparación entre campos', 'Compara el valor de dos campos.', TRUE),
    ('CONDITIONAL',    'Condicional simple',       'Aplica una condición simple entre campos o valores.', TRUE)
ON CONFLICT (codigo) DO NOTHING;

COMMIT;

-- Validación rápida
SELECT COUNT(*) AS total_tipos_dato FROM tipo_dato;
SELECT COUNT(*) AS total_tipos_regla FROM tipo_regla;
