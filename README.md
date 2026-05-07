# BlackBox - Local LLM API Server

> *Because clouds are overrated*

A self-hosted LLM inference server that acts as a **drop-in replacement for the OpenAI API**. Point any OpenAI-compatible client at it, paste your BlackBox API key, and it just works — privately, locally, for free.

Built with FastAPI + Ollama + SQLite.

---

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) installed and running
- At least one model pulled: `ollama pull llama3`

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Ollama

```bash
ollama serve
```

### 3. (Optional) Configure via .env

```bash
cp .env.example .env
# edit .env if your Ollama runs somewhere other than localhost:11434
```

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

On first startup the server creates an admin API key and prints it **once**:

```
============================================================
ADMIN API KEY (save this, it will not be shown again):
YOUR-KEY-HERE
============================================================
```

Save it. You'll use it as your `Authorization: Bearer <key>` header, and to create additional keys.

---

## Using with OpenAI clients

Any library that lets you set a custom `base_url` will work with zero other changes.

**Python (openai SDK):**
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000",   # point at BlackBox
    api_key="YOUR-BLACKBOX-API-KEY",
)

response = client.chat.completions.create(
    model="llama3",       # any model you have pulled in Ollama
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

**curl:**
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer YOUR-KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## API Endpoints

### OpenAI-compatible (use these with existing clients)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/chat/completions` | Chat endpoint — accepts `messages[]` |
| `POST` | `/v1/completions` | Legacy completion — accepts a `prompt` string |
| `GET` | `/v1/models` | List models available in Ollama |

### Key management

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/keys` | Create a new API key |
| `GET` | `/v1/keys` | List all keys (metadata only, no raw keys) |
| `DELETE` | `/v1/keys/{id}` | Revoke a key by ID |

**Create a key:**
```bash
curl -X POST http://localhost:8000/v1/keys \
  -H "Authorization: Bearer YOUR-ADMIN-KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-laptop"}'
```
Returns the raw key once — store it, it's not shown again.

### Observability

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/usage` | Query request logs with optional filters |
| `GET` | `/health` | Server + Ollama reachability check |

**Usage filters** (all optional query params):
- `api_key_id` — filter by key ID
- `model` — filter by model name
- `date_from` / `date_to` — ISO date strings, e.g. `2026-05-01`
- `limit` — max rows (default 100, max 1000)

```bash
curl "http://localhost:8000/v1/usage?model=llama3&limit=20" \
  -H "Authorization: Bearer YOUR-KEY"
```

### Legacy (original endpoint)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/generate` | Direct prompt → text (non-OpenAI shape) |

---

## Configuration

Copy `.env.example` to `.env` and set any of these:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Where Ollama is running |
| `OLLAMA_TIMEOUT` | `120.0` | Seconds to wait for a generation response |
| `ENV` | `dev` | Environment name |

---

## Project Structure

```
blackbox/
├── app/
│   ├── main.py                  # FastAPI app, startup, exception handlers
│   ├── api/
│   │   ├── generate.py          # Legacy /generate endpoint
│   │   └── v1/
│   │       ├── chat.py          # POST /v1/chat/completions
│   │       ├── completions.py   # POST /v1/completions
│   │       ├── models.py        # GET  /v1/models
│   │       ├── keys.py          # Key management CRUD
│   │       └── usage.py         # GET  /v1/usage
│   ├── core/
│   │   ├── auth.py              # Bearer token verification
│   │   ├── config.py            # Settings (env vars, .env file)
│   │   └── exceptions.py        # Custom exceptions
│   ├── db/
│   │   └── database.py          # SQLite schema + all queries
│   └── services/
│       └── ollama_client.py     # Async Ollama HTTP client
├── .env.example                 # Config template
├── requirements.txt
└── blackbox.db                  # Created on first run
```

---

## Error codes

| Code | Meaning |
|------|---------|
| `401` | Missing or invalid API key |
| `403` | Key has been revoked |
| `400` | Bad request (model not found, invalid input) |
| `503` | Ollama is unreachable |
| `500` | Internal server error |

---

**Made with for developers who prefer local over cloud**
