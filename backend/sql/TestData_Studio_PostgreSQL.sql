-- ============================================================
-- TESTDATA STUDIO - ESQUEMA POSTGRESQL CONSOLIDADO
-- Actualizado 2026-11-21 a partir de los modelos SQLAlchemy
-- 16 tablas utilizadas por la implementación actual
-- ============================================================
-- Uso: crear/conectarse a una BD vacía y ejecutar este archivo completo.
BEGIN;

CREATE TABLE rol (
	rol_id BIGSERIAL NOT NULL,
	nombre VARCHAR(50) NOT NULL,
	descripcion VARCHAR(200),
	estado BOOLEAN DEFAULT true NOT NULL,
	PRIMARY KEY (rol_id),
	UNIQUE (nombre)
);

CREATE TABLE tipo_dato (
	tipo_dato_id BIGSERIAL NOT NULL,
	codigo VARCHAR(30) NOT NULL,
	nombre VARCHAR(50) NOT NULL,
	descripcion VARCHAR(200),
	estado BOOLEAN DEFAULT true NOT NULL,
	PRIMARY KEY (tipo_dato_id),
	UNIQUE (codigo)
);

CREATE TABLE tipo_regla (
	tipo_regla_id BIGSERIAL NOT NULL,
	codigo VARCHAR(30) NOT NULL,
	nombre VARCHAR(100) NOT NULL,
	descripcion VARCHAR(300),
	estado BOOLEAN DEFAULT true NOT NULL,
	PRIMARY KEY (tipo_regla_id),
	UNIQUE (codigo)
);

CREATE TABLE usuario (
	usuario_id BIGSERIAL NOT NULL,
	rol_id BIGINT NOT NULL,
	nombre VARCHAR(100) NOT NULL,
	apellido VARCHAR(100) NOT NULL,
	email VARCHAR(150) NOT NULL,
	password_hash VARCHAR(255) NOT NULL,
	estado BOOLEAN DEFAULT true NOT NULL,
	fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
	PRIMARY KEY (usuario_id),
	FOREIGN KEY(rol_id) REFERENCES rol (rol_id)
);

CREATE UNIQUE INDEX ix_usuario_email ON usuario (email);

CREATE TABLE auditoria (
	auditoria_id BIGSERIAL NOT NULL,
	usuario_id BIGINT NOT NULL,
	entidad_afectada VARCHAR(30) NOT NULL,
	registro_id BIGINT NOT NULL,
	estado_anterior BOOLEAN NOT NULL,
	estado_nuevo BOOLEAN NOT NULL,
	fecha_cambio TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
	PRIMARY KEY (auditoria_id),
	FOREIGN KEY(usuario_id) REFERENCES usuario (usuario_id)
);

CREATE TABLE proyecto (
	proyecto_id BIGSERIAL NOT NULL,
	usuario_id BIGINT NOT NULL,
	nombre VARCHAR(120) NOT NULL,
	descripcion VARCHAR(500),
	estado BOOLEAN DEFAULT true NOT NULL,
	fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
	PRIMARY KEY (proyecto_id),
	FOREIGN KEY(usuario_id) REFERENCES usuario (usuario_id)
);

CREATE TABLE modelo (
	modelo_id BIGSERIAL NOT NULL,
	proyecto_id BIGINT NOT NULL,
	nombre VARCHAR(120) NOT NULL,
	descripcion VARCHAR(500),
	estado BOOLEAN DEFAULT true NOT NULL,
	fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
	PRIMARY KEY (modelo_id),
	CONSTRAINT uq_modelo_proyecto_nombre UNIQUE (proyecto_id, nombre),
	FOREIGN KEY(proyecto_id) REFERENCES proyecto (proyecto_id)
);

CREATE TABLE campo (
	campo_id BIGSERIAL NOT NULL,
	modelo_id BIGINT NOT NULL,
	tipo_dato_id BIGINT NOT NULL,
	nombre VARCHAR(100) NOT NULL,
	descripcion VARCHAR(250),
	orden INTEGER,
	estado BOOLEAN DEFAULT true NOT NULL,
	PRIMARY KEY (campo_id),
	CONSTRAINT uq_campo_modelo_nombre UNIQUE (modelo_id, nombre),
	CONSTRAINT uq_campo_modelo_orden UNIQUE (modelo_id, orden),
	FOREIGN KEY(modelo_id) REFERENCES modelo (modelo_id),
	FOREIGN KEY(tipo_dato_id) REFERENCES tipo_dato (tipo_dato_id)
);

CREATE TABLE generacion (
	generacion_id BIGSERIAL NOT NULL,
	modelo_id BIGINT NOT NULL,
	usuario_id BIGINT NOT NULL,
	cantidad_solicitada INTEGER NOT NULL,
	fecha_generacion TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
	estado VARCHAR(30) DEFAULT 'PENDIENTE' NOT NULL,
	PRIMARY KEY (generacion_id),
	CONSTRAINT chk_generacion_cantidad_positiva CHECK (cantidad_solicitada > 0),
	FOREIGN KEY(modelo_id) REFERENCES modelo (modelo_id),
	FOREIGN KEY(usuario_id) REFERENCES usuario (usuario_id)
);

CREATE TABLE regla (
	regla_id BIGSERIAL NOT NULL,
	modelo_id BIGINT NOT NULL,
	tipo_regla_id BIGINT NOT NULL,
	nombre VARCHAR(150) NOT NULL,
	descripcion VARCHAR(500),
	estado BOOLEAN DEFAULT true NOT NULL,
	fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
	PRIMARY KEY (regla_id),
	CONSTRAINT uq_regla_modelo_nombre UNIQUE (modelo_id, nombre),
	FOREIGN KEY(modelo_id) REFERENCES modelo (modelo_id),
	FOREIGN KEY(tipo_regla_id) REFERENCES tipo_regla (tipo_regla_id)
);

CREATE TABLE caso_prueba (
	caso_prueba_id BIGSERIAL NOT NULL,
	generacion_id BIGINT NOT NULL,
	tipo_escenario VARCHAR(20) NOT NULL,
	resultado_esperado VARCHAR(500) NOT NULL,
	fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
	PRIMARY KEY (caso_prueba_id),
	CONSTRAINT chk_caso_prueba_tipo_escenario CHECK (tipo_escenario IN ('VALIDO','INVALIDO','LIMITE')),
	FOREIGN KEY(generacion_id) REFERENCES generacion (generacion_id)
);

CREATE TABLE regla_campo (
	regla_id BIGINT NOT NULL,
	campo_id BIGINT NOT NULL,
	rol_campo VARCHAR(30) NOT NULL,
	PRIMARY KEY (regla_id, campo_id, rol_campo),
	FOREIGN KEY(regla_id) REFERENCES regla (regla_id),
	FOREIGN KEY(campo_id) REFERENCES campo (campo_id)
);

CREATE TABLE regla_parametro (
	parametro_id BIGSERIAL NOT NULL,
	regla_id BIGINT NOT NULL,
	clave VARCHAR(50) NOT NULL,
	valor VARCHAR(500) NOT NULL,
	orden INTEGER,
	PRIMARY KEY (parametro_id),
	FOREIGN KEY(regla_id) REFERENCES regla (regla_id)
);

CREATE TABLE caso_regla (
	caso_prueba_id BIGINT NOT NULL,
	regla_id BIGINT NOT NULL,
	cumple_esperado BOOLEAN NOT NULL,
	detalle_esperado VARCHAR(500),
	PRIMARY KEY (caso_prueba_id, regla_id),
	FOREIGN KEY(caso_prueba_id) REFERENCES caso_prueba (caso_prueba_id),
	FOREIGN KEY(regla_id) REFERENCES regla (regla_id)
);

CREATE TABLE dato_generado (
	dato_generado_id BIGSERIAL NOT NULL,
	caso_prueba_id BIGINT NOT NULL,
	campo_id BIGINT NOT NULL,
	valor_generado TEXT,
	PRIMARY KEY (dato_generado_id),
	CONSTRAINT uq_dato_generado_caso_campo UNIQUE (caso_prueba_id, campo_id),
	FOREIGN KEY(caso_prueba_id) REFERENCES caso_prueba (caso_prueba_id),
	FOREIGN KEY(campo_id) REFERENCES campo (campo_id)
);

CREATE TABLE ejecucion (
	ejecucion_id BIGSERIAL NOT NULL,
	caso_prueba_id BIGINT NOT NULL,
	usuario_id BIGINT NOT NULL,
	origen_registro VARCHAR(20) DEFAULT 'MANUAL' NOT NULL,
	resultado_obtenido TEXT,
	estado VARCHAR(20) NOT NULL,
	observacion VARCHAR(1000),
	fecha_ejecucion TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	fecha_registro TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
	PRIMARY KEY (ejecucion_id),
	CONSTRAINT chk_ejecucion_origen_registro CHECK (origen_registro IN ('MANUAL','CSV')),
	CONSTRAINT chk_ejecucion_estado CHECK (estado IN ('APROBADO','FALLIDO','BLOQUEADO')),
	FOREIGN KEY(caso_prueba_id) REFERENCES caso_prueba (caso_prueba_id),
	FOREIGN KEY(usuario_id) REFERENCES usuario (usuario_id)
);

CREATE INDEX ix_ejecucion_caso_prueba_id ON ejecucion (caso_prueba_id);

-- Índices adicionales para claves foráneas consultadas con frecuencia
CREATE INDEX IF NOT EXISTS idx_usuario_rol ON usuario(rol_id);
CREATE INDEX IF NOT EXISTS idx_proyecto_usuario ON proyecto(usuario_id);
CREATE INDEX IF NOT EXISTS idx_modelo_proyecto ON modelo(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_campo_modelo ON campo(modelo_id);
CREATE INDEX IF NOT EXISTS idx_campo_tipo_dato ON campo(tipo_dato_id);
CREATE INDEX IF NOT EXISTS idx_regla_modelo ON regla(modelo_id);
CREATE INDEX IF NOT EXISTS idx_regla_tipo ON regla(tipo_regla_id);
CREATE INDEX IF NOT EXISTS idx_regla_campo_campo ON regla_campo(campo_id);
CREATE INDEX IF NOT EXISTS idx_regla_parametro_regla ON regla_parametro(regla_id);
CREATE INDEX IF NOT EXISTS idx_generacion_modelo ON generacion(modelo_id);
CREATE INDEX IF NOT EXISTS idx_generacion_usuario ON generacion(usuario_id);
CREATE INDEX IF NOT EXISTS idx_caso_prueba_generacion ON caso_prueba(generacion_id);
CREATE INDEX IF NOT EXISTS idx_caso_regla_regla ON caso_regla(regla_id);
CREATE INDEX IF NOT EXISTS idx_dato_generado_campo ON dato_generado(campo_id);
CREATE INDEX IF NOT EXISTS idx_ejecucion_usuario ON ejecucion(usuario_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_usuario ON auditoria(usuario_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_entidad_registro ON auditoria(entidad_afectada, registro_id);

-- Catálogos base
INSERT INTO rol (nombre, descripcion, estado) VALUES
('Administrador', 'Perfil con gestión de usuarios y configuración administrativa.', TRUE),
('Analista/Tester', 'Perfil operativo para proyectos, modelos, reglas, generación y resultados.', TRUE)
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO tipo_dato (codigo, nombre, descripcion, estado) VALUES
('STRING', 'Texto', 'Cadena de texto.', TRUE),
('INTEGER', 'Entero', 'Número entero.', TRUE),
('DECIMAL', 'Decimal', 'Número decimal.', TRUE),
('DATE', 'Fecha', 'Fecha.', TRUE),
('BOOLEAN', 'Booleano', 'Valor lógico verdadero/falso.', TRUE),
('EMAIL', 'Correo', 'Dirección de correo electrónico.', TRUE)
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO tipo_regla (codigo, nombre, descripcion, estado) VALUES
('REQUIRED', 'Obligatoriedad', 'Valida presencia u obligatoriedad del campo.', TRUE),
('RANGE', 'Rango', 'Valida valores mínimos y máximos.', TRUE),
('ALLOWED_VALUES', 'Valores permitidos', 'Valida pertenencia a una lista de valores.', TRUE),
('FORMAT', 'Formato / longitud', 'Valida formato, patrón o longitud.', TRUE),
('COMPARISON', 'Comparación entre campos', 'Compara el valor de dos campos.', TRUE),
('CONDITIONAL', 'Condicional simple', 'Aplica una condición simple entre campos o valores.', TRUE)
ON CONFLICT (codigo) DO NOTHING;

COMMIT;

-- Validación esperada: 16 tablas de la aplicación
SELECT COUNT(*) AS total_tablas FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
