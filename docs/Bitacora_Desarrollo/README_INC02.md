INC-02 - Orden duplicado de campos dentro del mismo modelo
Fecha de corrección: 2026-11-18

Problema detectado:
Durante CP-05 Frontend se comprobó que era posible guardar dos campos del
mismo modelo con el mismo valor de orden.

Corrección aplicada:
1. FastAPI rechaza CREATE si (modelo_id, orden) ya existe.
2. FastAPI rechaza UPDATE si el nuevo orden pertenece a otro campo del mismo modelo.
3. SQLAlchemy incorpora UniqueConstraint(modelo_id, orden).
4. Se agrega script SQL para incorporar la restricción en PostgreSQL/Neon.
5. Se agregan pruebas automáticas de CREATE y UPDATE con orden duplicado.
6. Se agrega compatibilidad temporal entre los nombres antiguos
   FieldDefinition/Rule y los nombres actuales DataField/BusinessRule.
   Esto corrige el ImportError observado al iniciar Uvicorn cuando la carpeta
   local contiene archivos de versiones diferentes de M02.

ARCHIVOS ACTUALIZADOS EN ESTE PAQUETE
- app/api/routes/configuration.py
  Validación de orden único en CREATE y UPDATE.
- app/models/configuration.py
  UniqueConstraint y alias de compatibilidad.
- app/models/__init__.py
  Importaciones unificadas y compatibilidad entre versiones.
- tests/test_m02_configuration.py
  Pruebas de regresión para orden duplicado.
- sql/M02_INC02_orden_unico_campo.sql
  Revisión de duplicados y creación de restricción UNIQUE en Neon.
- README_INC02.txt
  Resumen de la corrección y archivos modificados.

Resultado esperado después del reemplazo:
- El backend inicia sin ImportError.
- Un orden repetido dentro del mismo modelo es rechazado.
- El mismo número de orden puede utilizarse en modelos diferentes.
