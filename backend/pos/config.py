"""
Configuration management for FastAPI POS system
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # FastAPI
    app_name: str = "BlueOlive POS"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/blueolive"
    )
    
    # Django DRF Backend
    drf_base_url: str = os.getenv("DRF_BASE_URL", "http://localhost:8000/api")
    drf_timeout: int = int(os.getenv("DRF_TIMEOUT", "30"))
    
    # CORS Settings
    allowed_origins: list[str] = [
        "http://localhost:3000",  # Next.js frontend
        "http://localhost:8000",  # Django backend
        "http://localhost:8001",  # FastAPI POS
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8001",
    ]
    
    # FastAPI Server
    fastapi_host: str = os.getenv("FASTAPI_HOST", "127.0.0.1")
    fastapi_port: int = int(os.getenv("FASTAPI_PORT", "8001"))
    
    # Cache Settings
    enable_cache: bool = os.getenv("ENABLE_CACHE", "True").lower() == "true"
    cache_ttl: int = int(os.getenv("CACHE_TTL", "300"))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
