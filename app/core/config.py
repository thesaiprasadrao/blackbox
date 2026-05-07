from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Local LLM API"
    ENV: str = "dev"

    # URL where Ollama is running
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # How long to wait for Ollama to respond to a generate/chat request (seconds)
    # Long generations can take a while on slow hardware — raise this if you hit timeouts
    OLLAMA_TIMEOUT: float = 120.0

    class Config:
        # Load from a .env file if it exists — env vars always win over defaults
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
