"""Configuration management for Glance backend."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PORT: int = 8000
    API_KEY: str = "dev-api-key-change-in-production"
    
    # AWS
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # Bedrock Models
    BEDROCK_NOVA_LITE_MODEL_ID: str = "amazon.nova-lite-v1:0"
    BEDROCK_EMBEDDING_MODEL_ID: str = "amazon.nova-embeddings-v1:0"
    EMBEDDING_DIMENSIONS: int = 1024
    
    # RDS PostgreSQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "glance_db"
    DB_USER: str = "glance_admin"
    DB_PASSWORD: str = "password"
    DB_POOL_SIZE: int = 10
    
    # OpenSearch
    OPENSEARCH_HOST: str = "localhost"
    OPENSEARCH_PORT: int = 9200
    OPENSEARCH_USE_SSL: bool = False
    OPENSEARCH_VERIFY_CERTS: bool = False
    OPENSEARCH_INDEX: str = "product_embeddings"
    OPENSEARCH_AWS_REGION: str = "us-east-1"
    
    # Application Settings
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    IMAGE_DOWNLOAD_TIMEOUT: int = 30
    SEARCH_TOP_K: int = 10
    SEARCH_FINAL_LIMIT: int = 3
    RRF_K: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    JSON_LOGGING: bool = True
    
    @property
    def database_url(self) -> str:
        """Construct database URL from components."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def opensearch_url(self) -> str:
        """Construct OpenSearch URL."""
        protocol = "https" if self.OPENSEARCH_USE_SSL else "http"
        return f"{protocol}://{self.OPENSEARCH_HOST}:{self.OPENSEARCH_PORT}"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
