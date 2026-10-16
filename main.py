from fastapi import FastAPI

app = FastAPI(
    title="Proy Andrea",
    description="API de agenda médica",
    version="1.0.0",
)


@app.get("/")
def inicio() -> dict[str, str]:
    return {"mensaje": "API de agenda médica funcionando"}
