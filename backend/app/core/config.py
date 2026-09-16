from typing import Annotated, Any

from pydantic import BeforeValidator, PostgresDsn, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_ignore_empty=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "Latium AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Security & JWT
    SECRET_KEY: str = (
        "insecure-dev-secret-key-change-in-production-use-strong-random-bytes"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN_MAX: int = 10
    RATE_LIMIT_REGISTER_MAX: int = 5
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Halt initialization if production environment is configured with default or weak secret key."""
        if self.ENVIRONMENT.lower() in ("production", "prod") and (
            "insecure" in self.SECRET_KEY.lower() or len(self.SECRET_KEY) < 32
        ):
            raise ValueError(
                "CRITICAL SECURITY HAZARD: Running in production environment with an insecure "
                "or weak SECRET_KEY. Please provide a cryptographically secure key of at least 32 bytes."
            )
        return self

    # LLM Settings
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None

    # Model Roles configuration
    TUTOR_MODEL: str = "claude-3-5-sonnet-20241022"
    EVALUATOR_MODEL: str = "gpt-4o"
    ROUTER_MODEL: str = "llama-3.1-70b-versatile"

    # PostgreSQL
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "latium_user"
    POSTGRES_PASSWORD: str = "latium_password"
    POSTGRES_DB: str = "latium_db"
    DATABASE_URL: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            # Ensure using asyncpg driver if specified as postgresql://
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace(
                    "postgresql://", "postgresql+asyncpg://", 1
                )
            return self.DATABASE_URL
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_redis_url(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # CORS
    CORS_ORIGINS: Annotated[list[str], BeforeValidator(parse_cors)] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://localhost:8001",
    ]


settings = Settings()
