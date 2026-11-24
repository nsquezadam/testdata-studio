TESTDATA STUDIO - INC-04
Fecha: 2026-11-18

Incidencia:
Durante CP-05 Frontend se detectó que los formularios de reglas no coincidían
completamente con el contrato del backend.

Problemas detectados:
1. COMPARISON enviaba roles ORIGEN/DESTINO, pero FastAPI valida
   PRINCIPAL/REFERENCIA.
2. CONDITIONAL mostraba un solo campo, aunque la regla requiere dos:
   PRINCIPAL y CONDICION.
3. ALLOWED_VALUES enviaba múltiples parámetros "valor", mientras el contrato
   actual utiliza un parámetro "valores" con la lista separada por coma.
4. La interfaz no explicaba claramente qué significa cada campo de las reglas
   que involucran dos campos.

Definición funcional acordada para el MVP:
- REQUIRED: un campo PRINCIPAL obligatorio.
- RANGE: un campo PRINCIPAL con mínimo y máximo.
- ALLOWED_VALUES: un campo PRINCIPAL y una lista de valores permitidos.
- FORMAT: un campo PRINCIPAL de tipo STRING/EMAIL con patrón y/o longitud.
- COMPARISON: Campo PRINCIPAL operador Campo REFERENCIA.
- CONDITIONAL: SI Campo CONDICION operador valor, entonces Campo PRINCIPAL
  debe estar informado (obligatoriedad condicional).

Archivos actualizados:
- app/api/routes/configuration.py
- tests/test_m02_configuration.py
- sql/M02_INC04_roles_reglas.sql (nuevo)
- README_INC04.txt (nuevo)

Resultado de regresión:
18 pruebas aprobadas.

TESTDATA STUDIO - M02
INC-04 v5 - Definición definitiva de CONDITIONAL
Fecha: 2026-11-18

CAMBIO FUNCIONAL
CONDITIONAL deja de representar solamente una obligatoriedad condicional.
Se define como una regla simple SI / ENTONCES:

SI [Campo condición] [Operador] [Valor]
ENTONCES [Campo objetivo] [Consecuencia] [Valor opcional]

Consecuencias soportadas en el MVP:
- REQUIRED
- EQUALS
- NOT_EQUALS
- GREATER_THAN
- GREATER_EQUAL
- LESS_THAN
- LESS_EQUAL
- ALLOWED_VALUES

El MVP mantiene deliberadamente una sola condición y una sola consecuencia.
No se incorporan combinaciones AND/OR múltiples en esta iteración.

ARCHIVOS ACTUALIZADOS
- app/api/routes/configuration.py
- tests/test_m02_configuration.py
- sql/M02_INC04_v5_conditional_general.sql
- README_INC04_v5.txt

NO SE MODIFICARON
- modelos SQLAlchemy
- schemas Pydantic
- estructura de tablas
- endpoints REST
- autenticación
- M01 Proyectos/Modelos

COMPATIBILIDAD
Las reglas antiguas pueden seguir listándose. Las reglas CONDITIONAL heredadas
que no tengan dos campos (CONDICION y PRINCIPAL) o parámetro accion deben
editarse una vez desde el nuevo formulario para completar la nueva definición.

VALIDACIÓN
Regresión backend ejecutada el 2026-11-18: 19 pruebas aprobadas.
