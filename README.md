# TestData Studio

## Proyecto de Título

**TestData Studio: Plataforma Web para la Generación y Seguimiento de Datos de Prueba Basados en Reglas de Negocio**

Proyecto desarrollado en el contexto de la carrera de **Ingeniería en Informática**.

---

## Descripción

TestData Studio es una plataforma web orientada a apoyar la preparación, generación y seguimiento de datos utilizados en pruebas de software.

La solución permite configurar modelos de datos y reglas de negocio, generar escenarios válidos, inválidos y casos límite, y mantener trazabilidad entre:

**Regla de negocio → Escenario → Dato → Resultado esperado → Resultado obtenido → Estado**

El sistema busca centralizar información que normalmente se encuentra distribuida en planillas, documentos y procesos manuales, facilitando su administración y seguimiento durante el ciclo de pruebas.

---

## Tecnologías

El proyecto contempla el uso de las siguientes tecnologías:

- React
- CSS
- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- REST / JSON
- JWT
- Pytest
- Git
- GitHub

---

## Estructura del repositorio

```text
proyectoTit/
│
├── backend/
│   └── Código correspondiente al backend y API del sistema.
│
├── frontend/
│   └── Código correspondiente a la interfaz web.
│
├── database/
│   ├── scripts/
│   │   └── Scripts SQL utilizados para la creación y mantenimiento
│   │       de la base de datos.
│   │
│   ├── diagrams/
│   │   ├── DER/
│   │   ├── Relacional/
│   │   └── UML_Clases/
│   │
│   └── dictionary/
│       └── Diccionario de datos asociado al modelo implementado.
│
├── docs/
│   │
│   ├── Diagramas/
│   │   ├── Casos_Uso/
│   │   ├── DER/
│   │   ├── UML_Clases/
│   │   ├── Modelo_Relacional/
│   │   ├── Arbol_Funcional/
│   │   └── Wireframes/
│   │
│   ├── Planificacion/
│   │   ├── Gantt/
│   │   ├── Requerimientos/
│   │   ├── Historias_Usuario/
│   │   └── Factibilidad/
│   │
│   ├── Modelos_Datos/
│   │   ├── Normalizacion/
│   │   └── Diccionario_Datos/
│   │
│   └── Entregas_Finales/
│
├── design/
│   ├── wireframes/
│   ├── figma/
│   └── evidencias/
│
├── tests/
│   └── Pruebas automatizadas del proyecto.
│
├── evidencias/
│   ├── base_datos/
│   ├── backend/
│   ├── frontend/
│   └── pruebas/
│
├── README.md
├── COMANDOS.md
└── .gitignore
```

---

## Organización de la documentación

### Diagramas

La carpeta:

```text
docs/Diagramas/
```

contiene los diferentes diagramas utilizados durante el análisis y diseño del sistema:

- Casos de uso.
- Diagrama Entidad-Relación.
- Diagrama UML de clases.
- Modelo relacional.
- Árbol funcional.
- Wireframes.

---

### Planificación

La carpeta:

```text
docs/Planificacion/
```

contiene los documentos relacionados con la definición y gestión del proyecto:

- Carta Gantt.
- Requerimientos funcionales y no funcionales.
- Historias de usuario.
- Criterios de aceptación.
- Documentación de planificación.
- Factibilidad del proyecto.

La carpeta `Factibilidad` será utilizada para mantener los