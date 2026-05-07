import httpx

from app.core.config import settings
from app.core.exceptions import ModelNotFound, OllamaUnavailable


async def generate_text(
    model: str,
    prompt: str,
    temperature: float | None,
    max_tokens: int | None
) -> tuple[str, int | None]:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    options = {}
    if temperature is not None:
        options["temperature"] = temperature
    if max_tokens is not None:
        options["num_predict"] = max_tokens
    
    if options:
        payload["options"] = options
    
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    
    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
            response = await client.post(url, json=payload)
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise OllamaUnavailable(f"Cannot connect to Ollama at {settings.OLLAMA_BASE_URL}") from e

    if response.status_code == 404:
        raise ModelNotFound(f"Model '{model}' not found")

    if response.status_code != 200:
        raise RuntimeError(f"Ollama API error: {response.status_code} - {response.text}")

    data = response.json()

    generated_text = data.get("response", "")
    token_count = data.get("eval_count")
    
    return generated_text, token_count


async def generate_chat(
    model: str,
    messages: list[dict],
    temperature: float | None,
    max_tokens: int | None,
) -> tuple[str, int | None]:
    """
    Chat variant — uses Ollama's /api/chat endpoint which accepts messages[]
    (role + content pairs) instead of a single prompt string.
    Same auth, same error handling as generate_text.
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }

    options = {}
    if temperature is not None:
        options["temperature"] = temperature
    if max_tokens is not None:
        options["num_predict"] = max_tokens
    if options:
        payload["options"] = options

    url = f"{settings.OLLAMA_BASE_URL}/api/chat"

    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
            response = await client.post(url, json=payload)
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise OllamaUnavailable(f"Cannot connect to Ollama at {settings.OLLAMA_BASE_URL}") from e

    if response.status_code == 404:
        raise ModelNotFound(f"Model '{model}' not found")

    if response.status_code != 200:
        raise RuntimeError(f"Ollama API error: {response.status_code} - {response.text}")

    data = response.json()

    # Ollama chat response: data["message"]["content"] holds the assistant reply
    generated_text = data.get("message", {}).get("content", "")
    token_count = data.get("eval_count")

    return generated_text, token_count
