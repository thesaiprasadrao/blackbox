import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import verify_api_key
from app.db.database import log_request
from app.services.ollama_client import generate_text

router = APIRouter()


class GenerateRequest(BaseModel):
    model: str
    prompt: str
    temperature: float | None = None
    max_tokens: int | None = None


class GenerateResponse(BaseModel):
    output: str
    tokens_used: int | None
    latency_ms: int


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest, api_key_id: int = Depends(verify_api_key)):
    start_time = time.time()
    
    output, tokens_used = await generate_text(
        model=request.model,
        prompt=request.prompt,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )
    
    end_time = time.time()
    latency_ms = int((end_time - start_time) * 1000)
    
    response = GenerateResponse(
        output=output,
        tokens_used=tokens_used,
        latency_ms=latency_ms
    )
    
    log_request(
        api_key_id=api_key_id,
        endpoint="/generate",
        model=request.model,
        tokens_used=tokens_used,
        latency_ms=latency_ms
    )
    
    return response
    
    return response
