"""
POST /v1/completions

OpenAI-compatible legacy completions endpoint. Some older clients and
libraries (like LangChain's LLM class) use this instead of chat/completions.
Accepts a plain prompt string instead of messages[].
"""

import time
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import verify_api_key
from app.db.database import log_request
from app.services.ollama_client import generate_text

router = APIRouter()


# ── Request / Response models (mirrors OpenAI schema) ────────────────────────

class CompletionRequest(BaseModel):
    model: str
    prompt: str
    temperature: float | None = None
    max_tokens: int | None = None


class CompletionChoice(BaseModel):
    text: str
    index: int
    finish_reason: str


class Usage(BaseModel):
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None


class CompletionResponse(BaseModel):
    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: list[CompletionChoice]
    usage: Usage


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/v1/completions", response_model=CompletionResponse)
async def completions(
    request: CompletionRequest,
    api_key_id: int = Depends(verify_api_key)
):
    start_time = time.time()

    output, tokens_used = await generate_text(
        model=request.model,
        prompt=request.prompt,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    latency_ms = int((time.time() - start_time) * 1000)

    log_request(
        api_key_id=api_key_id,
        endpoint="/v1/completions",
        model=request.model,
        tokens_used=tokens_used,
        latency_ms=latency_ms,
    )

    return CompletionResponse(
        id=f"cmpl-{uuid.uuid4().hex}",
        created=int(start_time),
        model=request.model,
        choices=[
            CompletionChoice(
                text=output,
                index=0,
                finish_reason="stop",
            )
        ],
        usage=Usage(
            prompt_tokens=None,
            completion_tokens=tokens_used,
            total_tokens=tokens_used,
        ),
    )
