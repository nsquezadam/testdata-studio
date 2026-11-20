-- ============================================================
-- TESTDATA STUDIO - VERIFICACIÓN PREVIA M02
-- Ejecutar primero en Neon / DBeaver.
-- ============================================================

-- 1. Verificar si las tablas de M02 ya existen.
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'tipo_dato',
      'campo',
      'tipo_regla',
      'regla',
      'regla_campo',
      'regla_parametro'
  )
ORDER BY table_name;

-- 2. Verificar que la tabla actual del modelo se llame "modelo".
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('modelo', 'modelo_dato')
ORDER BY table_name;

-- 3. Si campo/regla ya existen, revisar sus columnas.
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('campo', 'regla', 'regla_campo', 'regla_parametro')
ORDER BY table_name, ordinal_position;

-- 4. Revisar las llaves foráneas de M02, si existen.
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS tabla_referenciada,
    ccu.column_name AS columna_referenciada
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
 AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
 AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
  AND tc.table_name IN ('campo', 'regla', 'regla_campo', 'regla_parametro')
ORDER BY tc.table_name, kcu.column_name;
