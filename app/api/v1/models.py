"""
GET /v1/models

OpenAI-compatible model listing endpoint. Many clients (like the official
OpenAI Python SDK) call this on startup to verify the connection and
discover available models. We proxy the request to Ollama and reformat
the response to match OpenAI's shape.
"""

import time

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import verify_api_key
from app.core.config import settings
from app.core.exceptions import OllamaUnavailable

router = APIRouter()


# ── Response model (mirrors OpenAI schema) ────────────────────────────────────

class ModelInfo(BaseModel):
    id: str           # model name, e.g. "llama3"
    object: str = "model"
    created: int      # unix timestamp (Ollama doesn't provide this, we use now)
    owned_by: str = "ollama"


class ModelsResponse(BaseModel):
    object: str = "list"
    data: list[ModelInfo]


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("/v1/models", response_model=ModelsResponse)
async def list_models(api_key_id: int = Depends(verify_api_key)):
    url = f"{settings.OLLAMA_BASE_URL}/api/tags"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise OllamaUnavailable(f"Cannot connect to Ollama at {settings.OLLAMA_BASE_URL}") from e

    if response.status_code != 200:
        raise OllamaUnavailable(f"Ollama returned unexpected status: {response.status_code}")

    ollama_models = response.json().get("models", [])
    now = int(time.time())

    # Reformat Ollama model list into OpenAI model objects
    models = [
        ModelInfo(id=m["name"], created=now)
        for m in ollama_models
    ]

    return ModelsResponse(data=models)
