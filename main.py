import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError, PyMongoError

from api.routes.patients import router as patients_router
from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para administrar pacientes y sus consultas médicas.",
)


@app.middleware("http")
async def fix_vercel_path(request: Request, call_next):
    query_string = request.scope.get("query_string", b"").decode("utf-8")
    if "__path=" in query_string:
        from urllib.parse import parse_qs, urlencode
        qs = parse_qs(query_string)
        if "__path" in qs:
            original_path = qs.pop("__path")[0]
            request.scope["path"] = original_path or "/"
            request.scope["query_string"] = urlencode(qs, doseq=True).encode("utf-8")
    else:
        path = request.scope.get("path", "")
        for prefix in ("/api/index.py", "/api/index"):
            if path == prefix:
                request.scope["path"] = "/"
                break
            elif path.startswith(prefix + "/"):
                request.scope["path"] = path[len(prefix):]
                break
    return await call_next(request)


app.include_router(patients_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["Inicio"])
def inicio() -> dict[str, str]:
    return {"mensaje": f"{settings.app_name} está funcionando"}


@app.get("/health", tags=["Inicio"])
def health() -> dict[str, str]:
    return {"estado": "ok"}


@app.exception_handler(DuplicateKeyError)
async def duplicate_key_handler(
    _: Request, __: DuplicateKeyError
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": "Ya existe un paciente registrado con esa CI."},
    )


@app.exception_handler(PyMongoError)
async def database_error_handler(_: Request, exc: PyMongoError) -> JSONResponse:
    logger.error(
        "Error al comunicarse con MongoDB",
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(
        status_code=503,
        content={"detail": f"Error BD: {type(exc).__name__} - {str(exc)}"},
    )
