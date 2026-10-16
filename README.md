# Proy Andrea

API REST para registrar pacientes y administrar sus consultas médicas. Está
desarrollada con FastAPI y PyMongo, y guarda los datos en una única colección
MongoDB llamada `pacientes`.

El nombre del proyecto en Vercel y de la base de datos MongoDB es `proy-andrea`.

## Instalación local

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Edita `.env` y configura `MONGODB_URI` con la conexión de Atlas. No compartas ni
subas ese archivo a GitHub: contiene secretos y está excluido por `.gitignore`.

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

La documentación interactiva está en <http://127.0.0.1:8000/docs>.

## Configuración

| Variable | Propósito | Valor de ejemplo |
| --- | --- | --- |
| `APP_NAME` | Nombre de la API | `Proy Andrea` |
| `APP_VERSION` | Versión | `1.0.0` |
| `API_V1_PREFIX` | Prefijo de las rutas | `/api/v1` |
| `MONGODB_URI` | Conexión de Atlas | No publicar |
| `MONGODB_DB` | Base de datos | `proy-andrea` |
| `MONGODB_COLLECTION` | Colección única de pacientes | `pacientes` |

En Vercel, agrega estas variables en **Project Settings → Environment
Variables**. La integración de Atlas puede crear las variables de conexión;
usa sus nombres y valores reales, sin compartir la URI.

## Rutas

Las rutas de pacientes comienzan con `/api/v1/pacientes`.

| Método | Ruta | Acción |
| --- | --- | --- |
| `POST` | `/api/v1/pacientes` | Registrar paciente |
| `GET` | `/api/v1/pacientes` | Listar pacientes; acepta `estado` y/o `q` |
| `GET` | `/api/v1/pacientes/buscar?q=ana` | Buscar por nombre, apellido o CI |
| `GET` | `/api/v1/pacientes/estado/activo` | Filtrar por estado |
| `GET` | `/api/v1/pacientes/especialidad/cardiologia` | Filtrar por especialidad |
| `GET` | `/api/v1/pacientes/periodo?fecha_inicio=2026-01-01&fecha_fin=2026-12-31` | Buscar consultas por período |
| `GET` | `/api/v1/pacientes/{id}` | Consultar paciente |
| `PUT` | `/api/v1/pacientes/{id}` | Modificar paciente |
| `DELETE` | `/api/v1/pacientes/{id}` | Eliminar paciente |
| `POST` | `/api/v1/pacientes/{id}/consultas` | Agregar consulta |
| `GET` | `/api/v1/pacientes/{id}/consultas` | Consultar historial |

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Las pruebas usan una colección simulada y no necesitan conexión a Atlas.

## GitHub

Usa `main` para la base estable y `dev` para integrar funcionalidades. Crea
cada rama de funcionalidad desde `dev`, abre un Pull Request hacia `dev` y
verifica que CI pase antes de integrarlo. Al terminar, abre un Pull Request de
`dev` hacia `main`.

## Vercel

Crea el recurso MongoDB Atlas desde **Storage → MongoDB Atlas** con el nombre
`proy-andrea`. Importa este repositorio como proyecto Vercel con ese mismo
nombre, conecta el recurso Atlas y configura las variables de entorno. El
archivo `vercel.json` dirige las solicitudes a `api/index.py`.
