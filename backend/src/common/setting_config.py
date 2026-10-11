from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "movie-recommendation-ai-service"
    app_version: str = "0.1.0"
    app_port: int = 8082
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    neo4j_uri: str = "neo4j://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "123456"
    neo4j_database: str = "legalai"


    model_config = SettingsConfigDict(
        env_file=(".env", ".env.development", ".env.production"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
