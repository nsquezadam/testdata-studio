# SEG-01 – Seguridad RNF01 – TestData Studio

Fecha: 2026-11-21

## Objetivo
Validar de forma automatizada controles básicos de seguridad del MVP asociados a RNF01: almacenamiento de contraseñas mediante hash y control de acceso según usuario autenticado y perfil.

## Archivo agregado
- `backend/tests/test_security_rnf01.py`

No modifica código productivo, frontend ni base de datos.

## Controles automatizados
- SEG-01-C01: endpoint protegido rechaza acceso sin token (401).
- SEG-01-C02: token inválido es rechazado (401).
- SEG-01-C03: token JWT manipulado es rechazado (401).
- SEG-01-C04: Analista/Tester no accede a Gestión de Usuarios (403).
- SEG-01-C05: Administrador autorizado sí accede (200).
- SEG-01-C06: contraseña persistida no está en texto plano y el hash es verificable.
- SEG-01-C07: cadena básica de inyección SQL en login no elude autenticación (401).
- SEG-01-C08: respuesta de login no expone `password` ni `password_hash`.

## Ejecución específica
Desde `~/proyectoTit/backend`:

```bash
pytest -q tests/test_security_rnf01.py --junitxml=../automation/resultados/SEG-01_seguridad_rnf01.xml
```

Resultado esperado:

```text
........ [100%]
8 passed
```

## Regresión completa esperada
Si ya se aplicó la optimización RNF03 y su prueba adicional:

```bash
pytest -q
```

Resultado esperado actual:

```text
54 passed
```

## Evidencias sugeridas
- `EV_AUT_SEG01_01_SEGURIDAD_RNF01_8_PASSED.png`
- `automation/resultados/SEG-01_seguridad_rnf01.xml`

## Alcance
Esta suite constituye una validación automatizada de controles de seguridad del MVP. No debe presentarse como auditoría de seguridad completa ni como pentest profesional.
