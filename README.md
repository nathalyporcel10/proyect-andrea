# Proy Andrea

API para el proyecto de agenda médica desarrollado con FastAPI y MongoDB.

## Requisitos

- Python 3.10 o superior.
- Una instancia de MongoDB Atlas.

## Instalación local

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Crea un archivo `.env` local para la configuración. No subas ese archivo a
GitHub: contiene secretos y está excluido mediante `.gitignore`.

## Ejecutar

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

La documentación de FastAPI estará en <http://127.0.0.1:8000/docs>.
