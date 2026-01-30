from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.generate import router as generate_router
from app.core.auth import generate_api_key, hash_api_key
from app.core.config import settings
from app.core.exceptions import ModelNotFound, OllamaUnavailable
from app.db.database import create_api_key, get_api_key_count, init_db

app = FastAPI()


@app.on_event("startup")
def startup_event():
    init_db()
    
    if get_api_key_count() == 0:
        admin_key = generate_api_key()
        key_hash = hash_api_key(admin_key)
        create_api_key(key_hash, "admin")
        print("=" * 60)
        print("ADMIN API KEY (save this, it will not be shown again):")
        print(admin_key)
        print("=" * 60)


@app.exception_handler(OllamaUnavailable)
async def ollama_unavailable_handler(request: Request, exc: OllamaUnavailable):
    return JSONResponse(
        status_code=503,
        content={"error": str(exc)}
    )


@app.exception_handler(ModelNotFound)
async def model_not_found_handler(request: Request, exc: ModelNotFound):
    return JSONResponse(
        status_code=400,
        content={"error": str(exc)}
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)}
    )


app.include_router(generate_router)


@app.get("/health")
def health():
    return {"status": "ok"}
