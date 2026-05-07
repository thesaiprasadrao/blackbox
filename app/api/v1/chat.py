"""
POST /v1/chat/completions

OpenAI-compatible chat endpoint. Accepts the standard messages[] format
that OpenAI clients send, converts it to an Ollama prompt, and returns
a response shaped exactly like the OpenAI API would.
"""

import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import verify_api_key
from app.db.database import log_request
from app.services.ollama_client import generate_chat

router = APIRouter()


# ── Request / Response models (mirrors OpenAI schema) ────────────────────────

class Message(BaseModel):
    role: str    # "system", "user", or "assistant"
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: list[Message]
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False          # we don't support streaming yet, always False


class ChatChoice(BaseModel):
    index: int
    message: Message
    finish_reason: str


class Usage(BaseModel):
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None


class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]
    usage: Usage


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completions(
    request: ChatRequest,
    api_key_id: int = Depends(verify_api_key)
):
    # Streaming not supported yet — tell the client clearly
    if request.stream:
        raise HTTPException(
            status_code=400,
            detail={"error": {"message": "Streaming is not supported yet.", "type": "invalid_request_error", "code": "streaming_not_supported"}}
        )

    start_time = time.time()

    # Convert messages list to plain dicts for the Ollama client
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    output, tokens_used = await generate_chat(
        model=request.model,
        messages=messages,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    latency_ms = int((time.time() - start_time) * 1000)

    # Log the request for usage tracking
    log_request(
        api_key_id=api_key_id,
        endpoint="/v1/chat/completions",
        model=request.model,
        tokens_used=tokens_used,
        latency_ms=latency_ms,
    )

    # Build OpenAI-shaped response
    return ChatResponse(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        created=int(start_time),
        model=request.model,
        choices=[
            ChatChoice(
                index=0,
                message=Message(role="assistant", content=output),
                finish_reason="stop",
            )
        ],
        usage=Usage(
            prompt_tokens=None,       # Ollama doesn't break this out separately
            completion_tokens=tokens_used,
            total_tokens=tokens_used,
        ),
    )
