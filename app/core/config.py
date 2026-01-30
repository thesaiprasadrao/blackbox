from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Local LLM API"
    ENV: str = "dev"
    OLLAMA_BASE_URL: str = "http://localhost:11434"


settings = Settings()
