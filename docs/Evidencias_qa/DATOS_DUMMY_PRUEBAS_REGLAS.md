--DATOS_DUMMY_PRUEBAS_REGLAS

EV_CP-05_BE_C05_01_CREAR_REGLA_REQUIRED
=============================
C05.1 — Regla REQUIRED
=============================
POST /api/models/{modelo_id}/rules

modelo_id = 1 ---tipo_regla_id = 1

email_cliente → campo_id = 2


{
  "tipo_regla_id": 1,
  "nombre": "Email obligatorio",
  "descripcion": "El correo electrónico del cliente debe estar informado",
  "campos": [
    {
      "campo_id": 2,
      "rol_campo": "PRINCIPAL"
    }
  ],
  "parametros": []
}


=============================
C05.2 — Regla RANGE
=============================

tipo_regla_id = 2 → RANGE
edad_cliente → campo_id = 1


{
  "tipo_regla_id": 2,
  "nombre": "Rango edad cliente",
  "descripcion": "La edad del cliente debe encontrarse entre 18 y 65 años",
  "campos": [
    {
      "campo_id": 1,
      "rol_campo": "PRINCIPAL"
    }
  ],
  "parametros": [
    {
      "clave": "min",
      "valor": "18",
      "orden": 1
    },
    {
      "clave": "max",
      "valor": "65",
      "orden": 2
    }
  ]
}

=============================
C05.3 — ALLOWED_VALUES
=============================
tipo_cliente -- campo_id = 3


{
  "tipo_regla_id": 3,
  "nombre": "Tipos de cliente permitidos",
  "descripcion": "El tipo de cliente debe corresponder a uno de los valores permitidos",
  "campos": [
    {
      "campo_id": 3,
      "rol_campo": "PRINCIPAL"
    }
  ],
  "parametros": [
    {
      "clave": "valor",
      "valor": "PERSONA",
      "orden": 1
    },
    {
      "clave": "valor",
      "valor": "EMPRESA",
      "orden": 2
    },
    {
      "clave": "valor",
      "valor": "VIP",
      "orden": 3
    }
  ]
}
=============================
C05.4 — FORMAT / longitud
=============================

email_cliente--- campo_id = 2.
patron, longitud_min o longitud_max.

{
  "tipo_regla_id": 4,
  "nombre": "Longitud correo cliente",
  "descripcion": "El correo electrónico debe cumplir con una longitud válida",
  "campos": [
    {
      "campo_id": 2,
      "rol_campo": "PRINCIPAL"
    }
  ],
  "parametros": [
    {
      "clave": "longitud_min",
      "valor": "5",
      "orden": 1
    },
    {
      "clave": "longitud_max",
      "valor": "150",
      "orden": 2
    }
  ]
}

=============================
C05.5 — COMPARISON
=============================
ORIGEN
DESTINO

fecha_inicio → campo_id = 4
fecha_fin    → campo_id = 5

fecha_inicio < fecha_fin

{
  "tipo_regla_id": 5,
  "nombre": "Validación fechas del período",
  "descripcion": "La fecha de inicio debe ser anterior a la fecha de término",
  "campos": [
    {
      "campo_id": 4,
      "rol_campo": "ORIGEN"
    },
    {
      "campo_id": 5,
      "rol_campo": "DESTINO"
    }
  ],
  "parametros": [
    {
      "clave": "operador",
      "valor": "<",
      "orden": 1
    }
  ]
}

=============================
C05.5 — COMPARISON
=============================
tipo_cliente → campo_id = 3
tipo_cliente = EMPRESA

{
  "tipo_regla_id": 6,
  "nombre": "Condición cliente empresa",
  "descripcion": "Aplica una condición cuando el tipo de cliente corresponde a EMPRESA",
  "campos": [
    {
      "campo_id": 3,
      "rol_campo": "PRINCIPAL"
    }
  ],
  "parametros": [
    {
      "clave": "operador",
      "valor": "=",
      "orden": 1
    },
    {
      "clave": "valor",
      "valor": "EMPRESA",
      "orden": 2
    }
  ]
}


=========================================

CONFIGURACIONES REGLAS

=========================================

| Subcaso | Validación | Resultado esperado |
|---|---|---|
| C06.1 | RANGE con mínimo mayor que máximo | 400 |
| C06.2 | FORMAT con longitud mínima mayor que máxima | 400 |
| C06.3 | COMPARISON con un solo campo | 400 |
| C06.4 | CONDITIONAL sin parámetro `valor` | 400 |


==========================================
C06.1 — RANGE incoherente
==========================================
POST /api/models/1/rules
El valor mínimo no puede ser mayor que el valor máximo.
{
  "tipo_regla_id": 2,
  "nombre": "Rango inválido prueba",
  "descripcion": "Prueba de validación de mínimo mayor que máximo",
  "campos": [
    {
      "campo_id": 1,
      "rol_campo": "PRINCIPAL"
    }
  ],
  "parametros": [
    {
      "clave": "min",
      "valor": "100",
      "orden": 1
    },
    {
      "clave": "max",
      "valor": "20",
      "orden": 2
    }
  ]
}


==========================================
C06.2 — FORMAT incoherente
==========================================

mail_cliente :
longitud_min = 200
longitud_max = 100
mensajeLa longitud mínima no puede ser mayor que la longitud máxima.
{
  "tipo_regla_id": 4,
  "nombre": "Longitud inválida prueba",
  "descripcion": "Prueba de validación de longitudes",
  "campos": [
    {
      "campo_id": 2,
      "rol_campo": "PRINCIPAL"
    }
  ],
  "parametros": [
    {
      "clave": "longitud_min",
      "valor": "200",
      "orden": 1
    },
    {
      "clave": "longitud_max",
      "valor": "100",
      "orden": 2
    }
  ]
}

==========================================
C06.3 — COMPARISON con un solo campo
==========================================
mensaje_La comparación entre campos requiere exactamente dos campos diferentes.
{
  "tipo_regla_id": 5,
  "nombre": "Comparación inválida prueba",
  "descripcion": "Prueba de comparación con un único campo",
  "campos": [
    {
      "campo_id": 4,
      "rol_campo": "ORIGEN"
    }
  ],
  "parametros": [
    {
      "clave": "operador",
      "valor": "<",
      "orden": 1
    }
  ]
}

==========================================
C06.4 — CONDITIONAL incompleta
==========================================
mensaje: La condición simple requiere los parámetros "operador" y "valor".
{
  "tipo_regla_id": 6,
  "nombre": "Condición incompleta prueba",
  "descripcion": "Prueba de condición sin valor",
  "campos": [
    {
      "campo_id": 3,
      "rol_campo": "PRINCIPAL"
    }
  ],
  "parametros": [
    {
      "clave": "operador",
      "valor": "=",
      "orden": 1
    }
  ]
}


==========================================
C —
MODIFICACION DE  REGLA
==========================================

=============================
C05.5 — COMPARISON
=============================
tipo_cliente → campo_id = 3
tipo_cliente = PYME

{
  "tipo_regla_id": 6,
  "nombre": "Condición cliente empresa",
  "descripcion": "Mondificacion  condición cuando el tipo de cliente cambia de  EMPRESA a Pyme ",
  "campos": [
    {
      "campo_id": 3,
      "rol_campo": "PRINCIPAL"
    }
  ],
  "parametros": [
    {
      "clave": "operador",
      "valor": "=",
      "orden": 1
    },
    {
      "clave": "valor",
      "valor": "Pyme",
      "orden": 2
    }
  ]
}


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
WHERE r.modelo_id = 1 AND r.regla_id = 6
ORDER BY r.regla_id;




==============================================


| Acción | Ejemplo |
|---|---|
| `REQUIRED` | `razon_social` debe estar informado |
| `EQUALS` | `moneda = CLP` |
| `NOT_EQUALS` | `estado != PENDIENTE` |
| `GREATER_THAN` | `monto > 0` |
| `GREATER_EQUAL` | `descuento >= 15` |
| `LESS_THAN` | `edad < 18` |
| `LESS_EQUAL` | `descuento <= 20` |
| `ALLOWED_VALUES` | valor dentro de una lista definida |