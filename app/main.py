from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import httpx

from app.api.generate import router as generate_router
from app.api.v1.chat import router as chat_router               # OpenAI /v1/chat/completions
from app.api.v1.completions import router as completions_router  # OpenAI /v1/completions
from app.api.v1.keys import router as keys_router                # key management CRUD
from app.api.v1.models import router as models_router            # OpenAI /v1/models
from app.api.v1.usage import router as usage_router              # usage logs
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

# OpenAI-compatible v1 endpoints — clients can point base_url here
app.include_router(chat_router)
app.include_router(completions_router)
app.include_router(models_router)
app.include_router(keys_router)   # key management (create / list / revoke)
app.include_router(usage_router)  # usage logs


@app.get("/health")
async def health():
    # Check if Ollama is reachable, not just that this server is up
    ollama_status = "ok"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code != 200:
                ollama_status = f"error (status {resp.status_code})"
    except (httpx.ConnectError, httpx.TimeoutException):
        ollama_status = "unreachable"

    return {
        "status": "ok" if ollama_status == "ok" else "degraded",
        "ollama": ollama_status,
    }
