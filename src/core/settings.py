from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pydantic import SecretStr

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    DATABASE_URL: SecretStr

    JWT_SECRET_KEY: SecretStr
    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESJ_TOKEN_EXPIRE_DAYS: int = 7
    
@lru_cache
def get_settings() -> Settings:
    return Settings()