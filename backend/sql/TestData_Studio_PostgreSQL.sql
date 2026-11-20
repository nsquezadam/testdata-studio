-- ============================================================
-- TESTDATA STUDIO
-- Esquema PostgreSQL final 
-- 16 tablas / 91 campos / normalizado hasta 3FN
-- ============================================================
--
-- IMPORTANTE:
-- 1. Crear previamente una base de datos llamada testdata_studio desde pgAdmin.
-- 2. Conectarse a esa base de datos.
-- 3. Ejecutar este script completo.
--
-- AUDITORIA RF16: Se registra en la tabla AUDITORIA los cambios de estado de las entidades
-- USUARIO, PROYECTO, MODELO_DATO, CAMPO y REGLA usan estado BOOLEAN
-- para activación/desactivación lógica.
-- La aplicación debe realizar el UPDATE de estado y el INSERT en AUDITORIA
-- dentro de la misma transacción.
-- ============================================================

BEGIN;

-- ============================================================
-- 1. SEGURIDAD
-- ============================================================

CREATE TABLE rol (
    rol_id          BIGSERIAL PRIMARY KEY,
    nombre          VARCHAR(50) NOT NULL UNIQUE,
    descripcion     VARCHAR(200),
    estado          BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE usuario (
    usuario_id      BIGSERIAL PRIMARY KEY,
    rol_id          BIGINT NOT NULL REFERENCES rol(rol_id),
    nombre          VARCHAR(100) NOT NULL,
    apellido        VARCHAR(100) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    estado          BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. M01 - PROYECTOS Y MODELOS
-- ============================================================

CREATE TABLE proyecto (
    proyecto_id         BIGSERIAL PRIMARY KEY,
    usuario_id_creador  BIGINT NOT NULL REFERENCES usuario(usuario_id),
    nombre              VARCHAR(150) NOT NULL,
    descripcion         TEXT,
    estado              BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE modelo_dato (
    modelo_id       BIGSERIAL PRIMARY KEY,
    proyecto_id     BIGINT NOT NULL REFERENCES proyecto(proyecto_id),
    nombre          VARCHAR(150) NOT NULL,
    descripcion     TEXT,
    estado          BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_modelo_dato_proyecto_nombre UNIQUE (proyecto_id, nombre)
);

-- ============================================================
-- M02 - CAMPOS Y REGLAS
-- TestData Studio
-- ============================================================

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
    descripcion TEXT,
    estado BOOLEAN NOT NULL DEFAULT TRUE
);


CREATE TABLE IF NOT EXISTS regla (
    regla_id BIGSERIAL PRIMARY KEY,
    modelo_id BIGINT NOT NULL,
    tipo_regla_id BIGINT NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    estado BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_regla_modelo
        FOREIGN KEY (modelo_id)
        REFERENCES modelo(modelo_id),

    CONSTRAINT fk_regla_tipo
        FOREIGN KEY (tipo_regla_id)
        REFERENCES tipo_regla(tipo_regla_id)
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


--=============================================================
-- tipo_dato
--===============================================================

INSERT INTO tipo_dato
    (codigo, nombre, descripcion, estado)
VALUES
    ('STRING',  'Texto',    'Cadena de texto.', TRUE),
    ('INTEGER', 'Entero',   'Número entero.', TRUE),
    ('DECIMAL', 'Decimal',  'Número decimal.', TRUE),
    ('DATE',    'Fecha',    'Fecha.', TRUE),
    ('BOOLEAN', 'Booleano', 'Valor lógico verdadero/falso.', TRUE),
    ('EMAIL',   'Correo',   'Dirección de correo electrónico.', TRUE)
ON CONFLICT (codigo) DO NOTHING;

SELECT *
FROM tipo_dato
ORDER BY tipo_dato_id;
--=============================================================
-- tipo_regla
--===============================================================
INSERT INTO tipo_regla
    (codigo, nombre, descripcion, estado)
VALUES
    (
        'REQUIRED',
        'Obligatoriedad',
        'Valida presencia u obligatoriedad del campo.',
        TRUE
    ),
    (
        'RANGE',
        'Rango',
        'Valida valores mínimos y máximos.',
        TRUE
    ),
    (
        'ALLOWED_VALUES',
        'Valores permitidos',
        'Valida pertenencia a una lista de valores.',
        TRUE
    ),
    (
        'FORMAT',
        'Formato / longitud',
        'Valida formato, patrón o longitud.',
        TRUE
    ),
    (
        'COMPARISON',
        'Comparación entre campos',
        'Compara el valor de dos campos.',
        TRUE
    ),
    (
        'CONDITIONAL',
        'Condicional simple',
        'Aplica una condición simple entre campos o valores.',
        TRUE
    )
ON CONFLICT (codigo) DO NOTHING;



SELECT
    (SELECT COUNT(*) FROM tipo_dato)  AS tipos_dato,
    (SELECT COUNT(*) FROM tipo_regla) AS tipos_regla;

    
-- ============================================================
-- 4. M03 - GENERACIÓN DE DATOS Y ESCENARIOS
-- ============================================================

CREATE TABLE generacion (
    generacion_id       BIGSERIAL PRIMARY KEY,
    modelo_id           BIGINT NOT NULL REFERENCES modelo_dato(modelo_id),
    usuario_id          BIGINT NOT NULL REFERENCES usuario(usuario_id),
    cantidad_solicitada INTEGER NOT NULL,
    fecha_generacion    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado              VARCHAR(30) NOT NULL DEFAULT 'PENDIENTE',
    CONSTRAINT ck_generacion_cantidad CHECK (cantidad_solicitada > 0),
    CONSTRAINT ck_generacion_estado
        CHECK (estado IN ('PENDIENTE', 'COMPLETADA', 'ERROR'))
);

CREATE TABLE caso_prueba (
    caso_prueba_id      BIGSERIAL PRIMARY KEY,
    generacion_id       BIGINT NOT NULL REFERENCES generacion(generacion_id),
    tipo_escenario      VARCHAR(20) NOT NULL,
    resultado_esperado  VARCHAR(500) NOT NULL,
    fecha_creacion      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_caso_prueba_tipo
        CHECK (tipo_escenario IN ('VALIDO', 'INVALIDO', 'LIMITE'))
);

CREATE TABLE caso_regla (
    caso_prueba_id   BIGINT NOT NULL REFERENCES caso_prueba(caso_prueba_id),
    regla_id         BIGINT NOT NULL REFERENCES regla(regla_id),
    cumple_esperado  BOOLEAN NOT NULL,
    detalle_esperado VARCHAR(500),
    CONSTRAINT pk_caso_regla PRIMARY KEY (caso_prueba_id, regla_id)
);

CREATE TABLE dato_generado (
    dato_generado_id BIGSERIAL PRIMARY KEY,
    caso_prueba_id   BIGINT NOT NULL REFERENCES caso_prueba(caso_prueba_id),
    campo_id         BIGINT NOT NULL REFERENCES campo(campo_id),
    valor_generado   TEXT,
    CONSTRAINT uq_dato_generado_caso_campo UNIQUE (caso_prueba_id, campo_id)
);

-- ============================================================
-- 5. M04 - EJECUCIÓN Y RESULTADOS
-- ============================================================

CREATE TABLE ejecucion (
    ejecucion_id        BIGSERIAL PRIMARY KEY,
    caso_prueba_id      BIGINT NOT NULL REFERENCES caso_prueba(caso_prueba_id),
    usuario_id          BIGINT NOT NULL REFERENCES usuario(usuario_id),
    origen_registro     VARCHAR(20) NOT NULL,
    resultado_obtenido  TEXT,
    estado              VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    observacion         TEXT,
    fecha_ejecucion     TIMESTAMP,
    fecha_registro      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_ejecucion_origen
        CHECK (origen_registro IN ('MANUAL', 'CSV')),
    CONSTRAINT ck_ejecucion_estado
        CHECK (estado IN ('APROBADO', 'FALLIDO', 'BLOQUEADO', 'PENDIENTE'))
);

-- ============================================================
-- 6. TRANSVERSAL - AUDITORÍA RF16
-- ============================================================

CREATE TABLE auditoria (
    auditoria_id       BIGSERIAL PRIMARY KEY,
    usuario_id         BIGINT NOT NULL REFERENCES usuario(usuario_id),
    entidad_afectada   VARCHAR(30) NOT NULL,
    registro_id        BIGINT NOT NULL,
    estado_anterior    BOOLEAN NOT NULL,
    estado_nuevo       BOOLEAN NOT NULL,
    fecha_cambio       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_auditoria_entidad
        CHECK (entidad_afectada IN ('USUARIO', 'PROYECTO', 'MODELO_DATO', 'CAMPO', 'REGLA')),
    CONSTRAINT ck_auditoria_cambio_estado
        CHECK (estado_anterior <> estado_nuevo)
);

-- ============================================================
-- 7. ÍNDICES DE APOYO
-- PostgreSQL no crea automáticamente índices para las FKs.
-- ============================================================

CREATE INDEX idx_usuario_rol                ON usuario(rol_id);
CREATE INDEX idx_proyecto_usuario_creador   ON proyecto(usuario_id_creador);
CREATE INDEX idx_modelo_dato_proyecto       ON modelo_dato(proyecto_id);
CREATE INDEX idx_campo_modelo               ON campo(modelo_id);
CREATE INDEX idx_campo_tipo_dato            ON campo(tipo_dato_id);
CREATE INDEX idx_regla_modelo               ON regla(modelo_id);
CREATE INDEX idx_regla_tipo                 ON regla(tipo_regla_id);
CREATE INDEX idx_regla_campo_campo          ON regla_campo(campo_id);
CREATE INDEX idx_regla_parametro_regla      ON regla_parametro(regla_id);
CREATE INDEX idx_generacion_modelo           ON generacion(modelo_id);
CREATE INDEX idx_generacion_usuario          ON generacion(usuario_id);
CREATE INDEX idx_caso_prueba_generacion      ON caso_prueba(generacion_id);
CREATE INDEX idx_caso_regla_regla            ON caso_regla(regla_id);
CREATE INDEX idx_dato_generado_campo         ON dato_generado(campo_id);
CREATE INDEX idx_ejecucion_caso              ON ejecucion(caso_prueba_id);
CREATE INDEX idx_ejecucion_usuario           ON ejecucion(usuario_id);
CREATE INDEX idx_auditoria_usuario           ON auditoria(usuario_id);
CREATE INDEX idx_auditoria_entidad_registro  ON auditoria(entidad_afectada, registro_id);
CREATE INDEX idx_auditoria_fecha             ON auditoria(fecha_cambio);

-- ============================================================
-- 8. DATOS BASE
-- ============================================================

INSERT INTO rol (nombre, descripcion)
VALUES
    ('Administrador', 'Perfil con gestión de usuarios y configuración administrativa.'),
    ('Analista/Tester', 'Perfil operativo para proyectos, modelos, reglas, generación y resultados.')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO tipo_dato (codigo, nombre, descripcion)
VALUES
    ('STRING',  'Texto',          'Cadena de texto.'),
    ('INTEGER', 'Entero',         'Número entero.'),
    ('DECIMAL', 'Decimal',        'Número decimal.'),
    ('DATE',    'Fecha',          'Fecha.'),
    ('BOOLEAN', 'Booleano',       'Valor lógico verdadero/falso.'),
    ('EMAIL',   'Correo',         'Dirección de correo electrónico.')
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO tipo_regla (codigo, nombre, descripcion)
VALUES
    ('REQUIRED',       'Obligatoriedad',             'Valida presencia u obligatoriedad del campo.'),
    ('RANGE',          'Rango',                      'Valida valores mínimos y máximos.'),
    ('ALLOWED_VALUES', 'Valores permitidos',         'Valida pertenencia a una lista de valores.'),
    ('FORMAT',         'Formato / longitud',         'Valida formato, patrón o longitud.'),
    ('COMPARISON',     'Comparación entre campos',   'Compara el valor de dos campos.'),
    ('CONDITIONAL',    'Condicional simple',         'Aplica una condición simple entre campos o valores.')
ON CONFLICT (codigo) DO NOTHING;

COMMIT;

-- ============================================================
-- 9. CONSULTAS DE VALIDACIÓN
-- ============================================================

-- Debe devolver 16 tablas del esquema public creadas por este script.
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- Datos base esperados: 2 roles, 6 tipos de dato y 6 tipos de regla.
SELECT COUNT(*) AS total_roles FROM rol;
SELECT COUNT(*) AS total_tipos_dato FROM tipo_dato;
SELECT COUNT(*) AS total_tipos_regla FROM tipo_regla;

-- Verificación de AUDITORIA.
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'auditoria'
ORDER BY ordinal_position;


-- ============================================================
-- 10. EJEMPLO DE OPERACIÓN RF16 (REFERENCIAL)
-- Debe ejecutarse desde la aplicación dentro de una transacción.
-- ============================================================
--
-- BEGIN;
-- UPDATE proyecto
--    SET estado = FALSE
--  WHERE proyecto_id = 1
--    AND estado = TRUE;
--
-- INSERT INTO auditoria
--     (usuario_id, entidad_afectada, registro_id, estado_anterior, estado_nuevo)
-- VALUES
--     (1, 'PROYECTO', 1, TRUE, FALSE);
-- COMMIT;
--
-- La aplicación debe validar permisos antes de ejecutar la operación.
-- ============================================================



-- ============================================================
-- 11. CONSULTAS DE TESTING  SEGUN CP
-- ============================================================

--Evidencias BD 

--EV-CP01-BD-01_Usuarios_Perfiles

SELECT
    u.usuario_id,
    u.nombre,
    u.apellido,
    u.email,
    r.nombre AS rol,
    u.estado
FROM usuario u
INNER JOIN rol r
    ON u.rol_id = r.rol_id
ORDER BY u.usuario_id;

-- CONTRASEÑAno está guardada en texto plano
SELECT
    usuario_id,
    email,
    LEFT(password_hash, 25) AS hash_password,
    estado
FROM usuario
ORDER BY usuario_id;


UPDATE usuario
SET estado = FALSE
WHERE email = 'tester@testdata.local';


--EV-CP02-BD-01_Usuario_Inactivo

UPDATE usuario
SET estado = FALSE
WHERE email = 'tester@testdata.local';


SELECT
    usuario_id,
    nombre,
    apellido,
    email,
    estado
FROM usuario
WHERE email = 'tester@testdata.local';


UPDATE usuario
SET estado = TRUE
WHERE email = 'tester@testdata.local';


--CP-03
SELECT
    auditoria_id,
    usuario_id,
    entidad_afectada,
    registro_id,
    estado_anterior,
    estado_nuevo,
    fecha_cambio
FROM auditoria
ORDER BY auditoria_id DESC;

--EV-CP03-BE-01_Crear_Usuario
--BE --qa.prueba@testdata.local
--fe  --usuario_prueba_fe@testdata.local
SELECT
    u.usuario_id,
    u.nombre,
    u.apellido,
    u.email,
    r.nombre AS rol,
    u.estado,
    u.fecha_creacion
FROM usuario u
INNER JOIN rol r
    ON r.rol_id = u.rol_id
WHERE u.email = 'qa.prueba@testdata.local';


--EV-CP03-BD-02_Usuario_Modificado
SELECT
    usuario_id,
    nombre,
    apellido,
    email,
    rol_id,
    estado
FROM usuario
WHERE email = 'qa.prueba@testdata.local';

-- EV-CP03-BE-03_Desactivar_Usuario
SELECT
    usuario_id,
    nombre,
    apellido,
    email,
    estado
FROM usuario
WHERE email = 'qa.prueba@testdata.local';

--AUDITORIA

SELECT
    a.auditoria_id,
    a.usuario_id AS usuario_que_realiza_cambio,
    a.entidad_afectada,
    a.registro_id AS usuario_modificado,
    a.estado_anterior,
    a.estado_nuevo,
    a.fecha_cambio
FROM auditoria a
WHERE a.entidad_afectada = 'USUARIO'
ORDER BY a.auditoria_id DESC;

-EV-CP03-BE-05_Reactivar_Usuario.png
SELECT
    auditoria_id,
    usuario_id,
    entidad_afectada,
    registro_id,
    estado_anterior,
    estado_nuevo,
    fecha_cambio
FROM auditoria
WHERE entidad_afectada = 'USUARIO'
  AND registro_id = 3
ORDER BY auditoria_id;

--CP-04-C09 y comprobar la auditoría.

SELECT
    proyecto_id,
    usuario_id,
    nombre,
    descripcion,
    estado,
    fecha_creacion
FROM proyecto
WHERE proyecto_id = 1;

SELECT
    modelo_id,
    proyecto_id,
    nombre,
    descripcion,
    estado,
    fecha_creacion
FROM modelo
WHERE proyecto_id = 1;



--CP-05 CAMPOS Y REGLAS
SELECT
    c.campo_id,
    c.modelo_id,
    c.nombre,
    td.codigo AS tipo_dato,
    c.descripcion,
    c.orden,
    c.estado
FROM campo c
JOIN tipo_dato td
    ON td.tipo_dato_id = c.tipo_dato_id
WHERE c.modelo_id = 1
ORDER BY c.orden;
--ver todos los campos
SELECT
    c.campo_id,
    c.modelo_id,
    c.nombre,
    td.codigo AS tipo_dato,
    c.descripcion,
    c.orden,
    c.estado
FROM campo c
JOIN tipo_dato td
    ON td.tipo_dato_id = c.tipo_dato_id
WHERE c.modelo_id = 1

---REGLAS  

SELECT
    r.regla_id,
    r.modelo_id,
    tr.codigo AS tipo_regla,
    r.nombre,
    r.descripcion,
    r.estado,
    c.campo_id,
    c.nombre AS campo,
    rc.rol_campo
FROM regla r
JOIN tipo_regla tr
    ON tr.tipo_regla_id = r.tipo_regla_id
JOIN regla_campo rc
    ON rc.regla_id = r.regla_id
JOIN campo c
    ON c.campo_id = rc.campo_id
WHERE r.modelo_id = 1
ORDER BY r.regla_id;

--pasrametyros

SELECT
    r.regla_id,
    r.nombre AS regla,
    rp.clave,
    rp.valor,
    rp.orden
FROM regla r
JOIN regla_parametro rp
    ON rp.regla_id = r.regla_id
WHERE r.modelo_id = 1
ORDER BY r.regla_id, rp.orden;

SELECT
    regla_id,
    nombre,
    estado
FROM regla
WHERE modelo_id = 1
ORDER BY regla_id;
--=============================================================
--REVISION  ACTIVACION CAMPO  Y REGLA

SELECT
    c.campo_id,
    c.nombre AS campo,
    c.estado AS estado_campo,
    r.regla_id,
    r.nombre AS regla,
    r.estado AS estado_regla
FROM campo c
JOIN regla_campo rc
    ON rc.campo_id = c.campo_id
JOIN regla r
    ON r.regla_id = rc.regla_id
WHERE c.campo_id = 1
  AND r.regla_id = 2;