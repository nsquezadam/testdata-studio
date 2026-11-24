1) Ingresar como Administrador.
2) Verificar opciones.
3) Cerrar sesión.
4) Ingresar como Analista/Tester.
5) Verificar opciones.

Usuarios activos Admin y Analista/Tester.

{
  "email": "admin@testdata.local",
  "password": "Cambiar_Admin_123!"
}

{
  "email": "tester@testdata.local",
  "password": "Cambiar_Tester_123!"
}

{
  "email": "admin@testdata.local",
  "password": "Clave_Incorrecta_999"
}

{
  "email": "",
  "password": ""
}

{
  "email": "admin@testdata.local"
}
NOMENCLATURA

usuario_prueba_fe@testdata.local



Login React
   ↓
POST /api/auth/login
   ↓
FastAPI valida usuario
   ↓
PostgreSQL
   ↓
JWT
   ↓
React guarda access_token
   ↓
Usuario autenticado
   ↓
Dashboard


LOGEARSE CON ADMINISTRADOR
email": "admin@testdata.local", "password": "Cambiar_Admin_123!
DATOS API ENDPOINTS(PRUEBAS BACKEND)
GET    /api/users
GET    /api/users/roles
POST   /api/users
DATOS DE PRUEBA
  -nombre: Usuario,
  -apellido: Prueba,
  -email: qa.prueba@testdata.local,
  -password": Temporal_QA_123!,
  -rol_id": 2
  Frontend/API → PostgreSQL
PUT  /api/users/{usuario_id}-PUT    /api/users/3
DATOS DE  PRUEBA
  nombre: Usuario QA
  apellido: Prueba Modificada
  email: qa.prueba@testdata.local
  rol_id: 2
  password": null(conserva la contraseña actual)
PATCH  /api/users/{usuario_id}/estado
estado: false

{
  "email": "qa.prueba@testdata.local",
  "password": "Temporal_QA_123!"
}

EV-CP03-BE-01_Listar_Roles_GET(api_users_roles)




Administrador
      ↓
API TestData Studio
      ↓
Cambiar estado
      ↓
┌──────────────────────────────┐
│ misma transacción PostgreSQL │
│                              │
│ UPDATE usuario               │
│ INSERT auditoria             │
└──────────────────────────────┘


RoleResponse
    → perfiles disponibles.

UserCreate
    → datos requeridos para crear usuario.

UserUpdate
    → datos para modificar usuario.
      Password puede mantenerse sin cambio.

UserStatusUpdate
    → solamente activar/desactivar.

UserResponse
    → información que devolvemos al frontend.
      Nunca devuelve password_hash.


      En una segunda etapa del proyecto se podrá ampliar el mecanismo de auditoría para registrar no solo cambios de estado, sino también modificaciones sobre otros atributos relevantes de las entidades administradas. Esto permitiría disponer de un historial más detallado de operaciones, incluyendo tipo de cambio, campo modificado, valor anterior y valor nuevo, fortaleciendo la trazabilidad general de la plataforma.



EV-CP03-FE-01_DASHBOARD_ADMIN_HABILITADO_GU


DESPLIEGUE

Usuario
   │
   │ HTTPS
   ▼
React / Render
   │
   │ REST + JSON / HTTPS
   ▼
FastAPI / Render
   │
   │ SQLAlchemy / TLS
   ▼
PostgreSQL / Neon


| Subciclo | Criterio | Validación |
|---|---|---|
| CP-04-C01 | HU-03-CA01 | Consultar proyectos existentes |
| CP-04-C02 | HU-03-CA02 | Crear proyecto |
| CP-04-C03 | HU-03-CA03 | Modificar proyecto |
| CP-04-C04 | HU-03-CA04 | Crear modelo asociado a un proyecto |
| CP-04-C05 | HU-03-CA05 | Consultar proyecto con sus modelos asociados |
| CP-04-C06 | HU-03-CA06 | Validaciones de datos obligatorios |
| CP-04-C07 | HU-11-CA01 | Visualizar estado y acciones disponibles |
| CP-04-C08 | HU-11-CA03 | Activar/desactivar proyecto o modelo respetando permisos |
| CP-04-C09 | HU-11-CA05 | Verificar auditoría del cambio de estado |


GET    /api/projects
POST   /api/projects
PUT    /api/projects/{proyecto_id}
PATCH  /api/projects/{proyecto_id}/estado

GET    /api/projects/{proyecto_id}/models
POST   /api/projects/{proyecto_id}/models
PUT    /api/models/{modelo_id}
PATCH  /api/models/{modelo_id}/estado

EV_CP-04_BE_inicio_proyecto



EV_CP-04-BE_C02_crear proyecto
# Datos de prueba
{
  "nombre": "Proyecto_Prueba_1",
  "descripcion": "Proyecto de prueba, primer intento de creacion"
}

EV_CP-04-BE_C03_modificar_proyecto

{
  "nombre": "Proyecto_Prueba_1_Modificado",
  "descripcion": "Proyecto de prueba actualizado para validar la modificación"
}

EV_CP-04-C04 crear modelo
EV_CP-04-C06 obligatorios
EV_CP-04-C08 estados



Para preservar la trazabilidad de la información, TestData Studio implementa cambios de estado lógico en las entidades gestionables. Las operaciones de desactivación no eliminan físicamente los registros de PostgreSQL, sino que modifican el atributo estado. Paralelamente, cada transición válida es registrada en la tabla de auditoría, conservando el usuario responsable, la entidad afectada, el identificador del registro, el estado anterior, el nuevo estado y la fecha del cambio.


Un usuario autorizado se encuentra autenticado y existe un registro gestionable. Cuando accede a la gestión correspondiente, el sistema muestra el estado actual y permite solicitar Activar o Desactivar según sus permisos.

{
  "tipo_dato_id": 2,
  "nombre": "edad_cliente",
  "descripcion": "Edad del cliente utilizada para validar las reglas del modelo",
  "orden": 1
}