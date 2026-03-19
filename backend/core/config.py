from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_PATH), extra="ignore")

    APP_ENV: str = "development"
    DATABASE_URL: str = ""
    JWT_PRIVATE_KEY: str = ""
    JWT_PUBLIC_KEY: str = ""
    ACCESS_TOKEN_TTL_MINUTES: int = 
    REFRESH_TOKEN_TTL_DAYS: int = 
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = ""
    DYNAMODB_TABLE: str = ""
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    RATE_LIMIT_AUTHENTICATED: str = "100/minute"
    RATE_LIMIT_ANONYMOUS: str = "20/minute"


@lru_cache
def get_settings() -> Settings:
    return Settings()
