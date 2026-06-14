"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Enterprise AI Workflow Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = "change-this-super-secret-key-in-production-32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/enterprise_ai_db"
    SYNC_DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/enterprise_ai_db"

    # AI Models
    GROQ_API_KEY: str = "your-groq-api-key"
    GROQ_MODEL: str = "llama3-8b-8192"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Vector DB
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma_db"
    FAISS_INDEX_PATH: str = "./data/faiss_index"

    # File Storage
    UPLOAD_DIR: str = "./data/uploads"
    MAX_FILE_SIZE_MB: int = 50

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def allowed_origins_list(self) -> List[str]:
        return self.ALLOWED_ORIGINS


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
