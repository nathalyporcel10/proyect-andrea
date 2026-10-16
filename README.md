# Proy Andrea

API REST de agenda médica con FastAPI y MongoDB. La colección utilizada es
`pacientes`, dentro de la base `proy-andrea`.

## Instalación local

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Configura `MONGODB_URI` en `.env` con la conexión de MongoDB Atlas. No publiques
ese archivo: contiene credenciales y está excluido de Git.

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Abre <http://127.0.0.1:8000/docs> para probar la API.

## Registro de pacientes

`POST /api/v1/pacientes` crea un paciente con nombre, apellido, CI, fecha de
nacimiento, teléfono, correo, estado, contacto y consultas.

El correo, la fecha de nacimiento y los campos obligatorios se validan. La CI
tiene un índice único en MongoDB para prevenir registros repetidos.

Las pruebas locales no requieren conectarse a Atlas:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
