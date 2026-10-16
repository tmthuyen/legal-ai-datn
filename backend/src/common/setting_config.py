from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "legal-ai"
    app_version: str = "0.1.0"
    app_port: int = 8090
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password_not_set"
    neo4j_database: str = "legalai"

    # Embedding model configurations
    embedding_model_name: str = "darklethelong/vnlegal-lal"
    embedding_device: str = "cpu"
    embedding_batch_size: int = 4
    chroma_path: Path = Path("data/chroma")
    chroma_collection: str = "legal_articles"
    vector_backend: Literal["neo4j", "chroma"] = "chroma"
    vector_index_name: str = "article_embeddings_idx"

    # Reasoning model (fine-tuned citation inference) configurations
    hf_base_model: str = "ntphuc149/ViLegalQwen2.5-1.5B-Base"
    hf_model_id: str = "tmtdev/ViLegalQwen2.5-CitationInference-V1"
    hf_revision: str = Field(
        default="main",
        validation_alias=AliasChoices("HF_REVISION", "REVISION"),
    )

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.development", ".env.production"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
