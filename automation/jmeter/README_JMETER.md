# TestData Studio — JMeter

Creado: 2026-11-21.

Los planes usan únicamente componentes estándar de Apache JMeter y no requieren plugins.

## Trazabilidad

- JM-01 Rendimiento: RNF02 y RNF03 / CG-06 y CG-07.
- JM-02 Carga: CG-08.
- JM-03 Estrés: CG-08.

## JM-01 — Rendimiento

- 1 usuario.
- 20 iteraciones de consultas habituales.
- Dashboard y listado de generaciones: aserción de tiempo máximo 3000 ms.
- Una generación de 100 registros: aserción de tiempo máximo 5000 ms.
- La generación se ejecuta una sola vez por usuario mediante Once Only Controller.

## JM-02 — Carga

- 10 usuarios concurrentes.
- Ramp-up: 30 s.
- Duración: 300 s (5 min).
- Operaciones: Dashboard + listado de generaciones.
- Criterio: sin errores críticos y comportamiento estable.

## JM-03 — Estrés incremental

Se ejecutan fases seriales:

1. 10 usuarios / 60 s.
2. 25 usuarios / 60 s.
3. 50 usuarios / 60 s.

El objetivo no es exigir un umbral productivo, sino observar degradación, errores y punto de saturación del MVP.

## Configuración local

Copiar:

```bash
cp automation/jmeter/local.properties.example automation/jmeter/local.properties
```

Editar `local.properties` con la contraseña del Analista/Tester y confirmar `modelo_id=5` (o el modelo preparado que corresponda).

## Ejecución recomendada — Git Bash / Windows

Ejecutar con backend levantado en `127.0.0.1:8000`.

### JM-01

```bash
jmeter -n \
  -t automation/jmeter/JM-01_Rendimiento_RNF02_RNF03.jmx \
  -q automation/jmeter/local.properties \
  -l automation/jmeter/resultados/JM-01.jtl \
  -e -o automation/jmeter/reportes/JM-01
```

### JM-02

```bash
jmeter -n \
  -t automation/jmeter/JM-02_Carga.jmx \
  -q automation/jmeter/local.properties \
  -l automation/jmeter/resultados/JM-02.jtl \
  -e -o automation/jmeter/reportes/JM-02
```

### JM-03

```bash
jmeter -n \
  -t automation/jmeter/JM-03_Estres_Incremental.jmx \
  -q automation/jmeter/local.properties \
  -l automation/jmeter/resultados/JM-03.jtl \
  -e -o automation/jmeter/reportes/JM-03
```

> Para mediciones de rendimiento, JMeter recomienda ejecución no-GUI. La interfaz gráfica se puede usar primero para abrir y revisar cada `.jmx`.

## Evidencias sugeridas

- EV_JM-01_RESUMEN.png
- EV_JM-01_RNF03_GENERACION_100.png
- EV_JM-02_REPORTE_CARGA.png
- EV_JM-03_REPORTE_ESTRES.png

No subir `local.properties` porque contiene credenciales.
# JMeter TestData Studio — corrección V3 (2026-11-21)

Se corrigió la estructura `hashTree` de los tres planes para compatibilidad con Apache JMeter 5.6.3.

## JM-01
- Login una vez.
- Genera 100 registros una sola vez para RNF03 (máximo 5000 ms).
- Consulta Dashboard 20 veces para RNF02 (máximo 3000 ms).

## JM-02
- 10 usuarios, ramp-up 30 s, duración 300 s.
- Cada usuario inicia sesión una vez.
- Alterna Dashboard y listado de generaciones con pausa de 500 ms.

## JM-03
- Estrés incremental temporizado: 10 -> 25 -> 50 usuarios.
- Fases de 60 s con delays 0 / 60 / 120 s.

## Credenciales
Los planes leen propiedades `tester_email` y `tester_password`. En Git Bash pueden reutilizarse las variables de Selenium:

```bash
jmeter ... -Jtester_email="$SELENIUM_TESTER_EMAIL" -Jtester_password="$SELENIUM_TESTER_PASSWORD"
```

No guardar contraseñas reales en Git.


# TestData Studio - JM-01 V4 (2026-11-21)

## Motivo del ajuste
La primera ejecución de JM-01 mostró que RNF03 alcanzó exactamente 10.002 ms y terminó con `java.net.SocketTimeoutException: Read timed out`. Ese valor coincide con el timeout técnico de 10.000 ms configurado en el HTTP Request, por lo que JMeter cortó la espera antes de recibir la respuesta completa.

## Cambio realizado
Solo se modificó `JM-01_Rendimiento_RNF02_RNF03.jmx`:
- Timeout técnico de lectura para **RNF03 - Generar 100 registros**: 10.000 ms -> 60.000 ms.
- Se mantiene SIN CAMBIOS la `DurationAssertion` de **5.000 ms**.
- RNF02 sigue con su criterio de **3.000 ms**.

Esto no flexibiliza el requisito: permite medir cuánto tarda realmente el endpoint. Si la respuesta tarda más de 5 segundos, RNF03 seguirá quedando FALLIDO aunque el HTTP 201 llegue correctamente.

## Antes de repetir
El primer request pudo haber seguido procesándose en el servidor después de que JMeter abandonó la espera. Conviene verificar si apareció una generación nueva de 100 casos antes de ejecutar nuevamente.

## Ejecución
```bash
rm -rf automation/resultados/JM-01_reporte
rm -f automation/resultados/JM-01_resultados.jtl

jmeter -n \
  -t automation/jmeter/JM-01_Rendimiento_RNF02_RNF03.jmx \
  -Jtester_email="$SELENIUM_TESTER_EMAIL" \
  -Jtester_password="$SELENIUM_TESTER_PASSWORD" \
  -l automation/resultados/JM-01_resultados.jtl \
  -e \
  -o automation/resultados/JM-01_reporte
```
