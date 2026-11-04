\# Comandos utilizados - TestData Studio



Este documento reúne los principales comandos utilizados durante la creación, configuración y desarrollo del proyecto \*\*TestData Studio\*\*.



\---



\## Comandos principales



\### Verificar versión de Git



```bash

git --version

```



\### Ir a la carpeta del proyecto



```bash

cd /c/Users/nsque/proyectoTit

```



\### Inicializar el repositorio Git



```bash

git init -b main

```



\### Verificar estado del repositorio



```bash

git status

```



\### Mostrar archivos y carpetas



```bash

ls -la

```



\### Mostrar estructura de carpetas



```bash

find . -maxdepth 3 -type d | sort

```



\### Crear carpetas principales del proyecto



```bash

mkdir -p backend frontend database/scripts database/diagrams/DER database/diagrams/Relacional database/diagrams/UML\_Clases database/dictionary docs/01\_EVA1\_Semanas\_1\_2 docs/02\_Semana\_3/Casos\_Uso docs/02\_Semana\_3/DER docs/02\_Semana\_3/UML\_Clases docs/02\_Semana\_3/Modelo\_Relacional docs/03\_Semana\_4/Normalizacion docs/03\_Semana\_4/Diccionario\_Datos docs/03\_Semana\_4/Arbol\_Funcional docs/03\_Semana\_4/Wireframes docs/04\_Gantt docs/05\_Guias\_Estudio docs/06\_Entregas\_Finales design/wireframes design/figma design/evidencias tests evidencias/base\_datos evidencias/backend evidencias/frontend evidencias/pruebas

```



\### Crear archivos principales



```bash

touch README.md .gitignore COMANDOS.md

```



\### Crear archivos `.gitkeep` en carpetas vacías



Git no almacena carpetas vacías. Este comando crea un archivo temporal `.gitkeep` dentro de ellas.



```bash

find . -type d -empty -not -path "./.git\*" -exec touch {}/.gitkeep \\;

```



\### Abrir README con Bloc de notas



```bash

notepad README.md

```



\### Abrir `.gitignore`



```bash

notepad .gitignore

```



\### Abrir archivo de comandos



```bash

notepad COMANDOS.md

```



\---



\## Git - Control de versiones



\### Revisar archivos modificados



```bash

git status

```



\### Agregar todos los archivos al área de preparación



```bash

git add .

```



\### Crear un commit



```bash

git commit -m "Descripción del cambio"

```



Ejemplo para el primer respaldo:



```bash

git commit -m "Initial project structure and academic documentation"

```



\### Ver historial resumido de commits



```bash

git log --oneline

```



\### Ver ramas existentes



```bash

git branch

```



\### Ver repositorios remotos configurados



```bash

git remote -v

```



\### Asociar el repositorio local con GitHub



```bash

git remote add origin URL\_REPOSITORIO

```



Ejemplo:



```bash

git remote add origin https://github.com/TU\_USUARIO/testdata-studio.git

```



\### Subir por primera vez la rama principal



```bash

git push -u origin main

```



\### Subir cambios posteriores



```bash

git push

```



\### Descargar cambios del repositorio remoto



```bash

git pull

```



\---



\## Flujo habitual de trabajo con Git



Cada vez que se agreguen o modifiquen archivos se puede utilizar:



```bash

git status

git add .

git commit -m "Descripción del cambio realizado"

git push

```



Ejemplo:



```bash

git status

git add .

git commit -m "Add database diagrams and documentation"

git push

```



\---



\## PostgreSQL



\### Base de datos utilizada



```text

testdata\_studio

```



\### Script principal de creación de base de datos



Ubicación dentro del proyecto:



```text

database/scripts/TestData\_Studio\_PostgreSQL\_RF16\_FINAL.sql

```



\### Query para listar tablas creadas



```sql

SELECT

&#x20;   tablename AS tabla

FROM pg\_tables

WHERE schemaname = 'public'

ORDER BY tablename;

```



\### Contar tablas creadas



```sql

SELECT

&#x20;   COUNT(\*) AS total\_tablas

FROM pg\_tables

WHERE schemaname = 'public';

```



Resultado esperado:



```text

16

```



\### Validar datos base



```sql

SELECT COUNT(\*) AS total\_roles

FROM rol;



SELECT COUNT(\*) AS total\_tipos\_dato

FROM tipo\_dato;



SELECT COUNT(\*) AS total\_tipos\_regla

FROM tipo\_regla;

```



Resultados esperados:



```text

Roles: 2

Tipos de dato: 6

Tipos de regla: 6

```



\### Revisar estructura de la tabla auditoria



```sql

SELECT

&#x20;   column\_name,

&#x20;   data\_type,

&#x20;   character\_maximum\_length,

&#x20;   is\_nullable

FROM information\_schema.columns

WHERE table\_schema = 'public'

&#x20; AND table\_name = 'auditoria'

ORDER BY ordinal\_position;

```



\---



\## Backend - Python / FastAPI



Esta sección se completará cuando comience la implementación del backend.



Aquí se documentarán posteriormente comandos relacionados con:



```text

Python

Entorno virtual

FastAPI

Uvicorn

SQLAlchemy

PostgreSQL

Pytest

```



\---



\## Frontend - React



Esta sección se completará cuando comience la implementación de la interfaz web.



Aquí se documentarán posteriormente comandos relacionados con:



```text

Node.js

npm

React

Ejecución del frontend

Build

Pruebas

```



\---



\## Seguridad



Nunca se deben subir al repositorio archivos que contengan contraseñas o credenciales.



El archivo:



```text

.env

```



debe permanecer incluido en `.gitignore`.



Cuando sea necesario compartir la estructura de variables de entorno se utilizará:



```text

.env.example

```



sin contraseñas reales.

