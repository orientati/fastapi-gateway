from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "FastAPI Gateway"
    SERVICE_VERSION: str = "0.1.0"
    DATABASE_URL: str = "sqlite:///./database.db"
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASS: str = "guest"
    RABBITMQ_CONNECTION_RETRIES: int = 5
    RABBITMQ_CONNECTION_RETRY_DELAY: int = 5
    SERVICE_PORT: int = 8000
    ENVIRONMENT: str = "development"
    SENTRY_DSN: str = ""
    SENTRY_RELEASE: str = "0.1.0"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    API_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: list[str] = ["*"]

    #### ROUTES              # noqa: E266
    TOKEN_SERVICE_URL: str = "http://token:8002"
    USERS_SERVICE_URL: str = "http://users:8003"
    SCHOOLS_SERVICE_URL: str = "http://schools:8004"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="GATEWAY_"  # Prefisso di tutte le variabili (es. GATEWAY_DATABASE_URL)
    )


settings = Settings()
