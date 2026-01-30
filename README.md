# 🖤 BlackBox - Local LLM API Server

> *Because clouds are overrated*

A self-hosted, production-ready(under construction) LLM inference server that exposes a clean REST API for local language models. Built with FastAPI and Ollama, providing OpenAI-style endpoints without the costs, rate limits, or vendor lock-in.

## 🎯 Features

- **🔐 API Key Authentication**: Secure access with Bearer token authentication and SHA-256 hashed keys
- **📊 Usage Tracking**: Automatic logging of requests, token usage, and latency metrics
- **⚡ Fast Inference**: Powered by Ollama for efficient local model execution
- **🛡️ Error Handling**: Graceful handling of connection failures, missing models, and rate limiting
- **💾 SQLite Database**: Lightweight data persistence for API keys and request logs
- **🚀 Auto-provisioning**: Generates admin API key on first startup
- **📈 Performance Metrics**: Tracks latency and token counts per request

## 📋 Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) installed and running on `http://localhost:11434`
- At least one Ollama model pulled (e.g., `ollama pull llama2`)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install fastapi uvicorn httpx pydantic-settings
```

### 2. Start Ollama

```bash
ollama serve
```

### 3. Run the Server

```bash
cd app
uvicorn main:app --reload
```

On first startup, an admin API key will be generated and displayed in the console. **Save this key** - it won't be shown again!

```
============================================================
ADMIN API KEY (save this, it will not be shown again):
YOUR-GENERATED-API-KEY-HERE
============================================================
```

### 4. Make Your First Request

```bash
curl -X POST http://localhost:8000/generate \
  -H "Authorization: Bearer YOUR-API-KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "prompt": "Explain quantum computing in simple terms",
    "temperature": 0.7,
    "max_tokens": 200
  }'
```

## 📡 API Endpoints

### `POST /generate`

Generate text completion from a prompt.

**Request Body:**
```json
{
  "model": "llama2",
  "prompt": "Your prompt here",
  "temperature": 0.7,
  "max_tokens": 500
}
```

**Response:**
```json
{
  "output": "Generated text...",
  "tokens_used": 150,
  "latency_ms": 1234
}
```

**Authentication:** Required via `Authorization: Bearer <your-api-key>` header

### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

## 🏗️ Architecture

```
┌─────────────────────┐
│  Client Application │
└──────────┬──────────┘
           │ REST/JSON
           ▼
┌─────────────────────┐
│   FastAPI Server    │
│  ┌───────────────┐  │
│  │ Auth Layer    │  │
│  ├───────────────┤  │
│  │ Request Log   │  │
│  ├───────────────┤  │
│  │ API Routes    │  │
│  └───────────────┘  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Ollama Runtime     │
│  (Local Models)     │
└─────────────────────┘
```

## 📂 Project Structure

```
blackbox/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── api/
│   │   └── generate.py      # Text generation endpoint
│   ├── core/
│   │   ├── auth.py          # API key authentication
│   │   ├── config.py        # Configuration settings
│   │   └── exceptions.py    # Custom exceptions
│   ├── db/
│   │   └── database.py      # SQLite database operations
│   └── services/
│       └── ollama_client.py # Ollama API client
├── blackbox.db              # SQLite database (created on first run)
├── prd.txt                  # Product Requirements Document
└── README.md
```

## 🔧 Configuration

Configuration is managed via environment variables in [app/core/config.py](app/core/config.py):

- `APP_NAME`: Application name (default: "Local LLM API")
- `ENV`: Environment (default: "dev")
- `OLLAMA_BASE_URL`: Ollama API endpoint (default: "http://localhost:11434")

## 💾 Database Schema

### `api_keys` Table
- `id`: Primary key
- `key_hash`: SHA-256 hash of the API key
- `name`: Human-readable name
- `created_at`: ISO 8601 timestamp
- `revoked`: Boolean flag for key revocation

### `requests` Table
- `id`: Primary key
- `api_key_id`: Foreign key to api_keys
- `endpoint`: API endpoint called
- `model`: Model name used
- `tokens_used`: Token count (nullable)
- `latency_ms`: Request latency in milliseconds
- `timestamp`: ISO 8601 timestamp

## 🛡️ Security Features

- **Hashed API Keys**: Keys are stored as SHA-256 hashes, never in plaintext
- **Bearer Token Auth**: Industry-standard authentication header
- **Key Revocation**: API keys can be marked as revoked
- **Request Validation**: Pydantic models for input validation

## 🎯 Use Cases

- Local AI development without API costs
- Privacy-focused LLM applications
- Offline AI inference
- AI backend for multiple projects
- Prototyping and experimentation
- Internal tooling and automation

## 🚨 Error Codes

- `401`: Missing or invalid API key
- `403`: Revoked API key
- `400`: Model not found
- `503`: Ollama service unavailable
- `500`: Internal server error

## 🤝 Contributing

This is a production-ready local LLM server designed for simplicity and reliability. Contributions are welcome!

## 📄 License

Open source - use it, modify it, deploy it however you like.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Ollama](https://ollama.ai)
- Inspired by the need for local-first AI infrastructure

---

**Made with 🖤 for developers who prefer local over cloud**
