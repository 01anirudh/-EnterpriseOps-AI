"""
Application configuration using Pydantic Settings.
Reads from .env file automatically.
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache

# Always resolve .env relative to this file (backend/.env)
_ENV_FILE = Path(__file__).parent / ".env"


class Settings(BaseSettings):
    # LLM
    GOOGLE_API_KEY: str = Field(default="", description="Google Gemini API key")
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key (alternative)")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://enterpriseops:enterpriseops_secret@localhost:5432/enterpriseops"
    )
    DATABASE_SYNC_URL: str = Field(
        default="postgresql://enterpriseops:enterpriseops_secret@localhost:5432/enterpriseops"
    )

    # Redis / Celery
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/1")

    # Qdrant
    QDRANT_HOST: str = Field(default="localhost")
    QDRANT_PORT: int = Field(default=6333)
    QDRANT_COLLECTION: str = Field(default="enterprise_docs")

    # JWT
    JWT_SECRET_KEY: str = Field(default="change_this_in_production")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)

    # Gmail
    GMAIL_CREDENTIALS_FILE: str = Field(default="credentials/gmail_credentials.json")
    GMAIL_TOKEN_FILE: str = Field(default="credentials/gmail_token.json")
    GMAIL_SENDER_EMAIL: str = Field(default="")

    # Slack
    SLACK_BOT_TOKEN: str = Field(default="")
    SLACK_DEFAULT_CHANNEL: str = Field(default="#general")

    # GitHub
    GITHUB_TOKEN: str = Field(default="")
    GITHUB_REPO: str = Field(default="")

    # App
    ENVIRONMENT: str = Field(default="development")
    ALLOWED_ORIGINS: str = Field(default="http://localhost:5173,http://localhost:3000")
    UPLOAD_DIR: str = Field(default="documents/uploads")
    REPORTS_DIR: str = Field(default="documents/reports")

    # Embeddings
    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION: int = Field(default=384)

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def mock_gmail(self) -> bool:
        return not self.GMAIL_SENDER_EMAIL

    @property
    def mock_slack(self) -> bool:
        return not self.SLACK_BOT_TOKEN

    @property
    def mock_github(self) -> bool:
        return not self.GITHUB_TOKEN

    class Config:
        env_file = _ENV_FILE
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
