from pathlib import Path
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables and .env file.
    All settings are top-level for simplicity.
    """

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    PROJECT_NAME: str = "Ekam-Query"

    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://user:pass@localhost:5432/db"
    )  # type: ignore [reportAssignmentType]
    DATABASE_POOL_SIZE: int = 10
    DATABASE_ECHO: bool = False

    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_BATCH_SIZE: int = 32

    CACHE_TTL_SECONDS: int = 300
    CACHE_MAX_SIZE: int = 1000


settings = Settings()
