from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application configuration settings"""

    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # Application Settings
    app_name: str = "ClaRA RAG System"
    debug: bool = True
    upload_dir: str = "./uploads"
    vector_db_dir: str = "./vector_db"

    # Model Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.7
    max_tokens: int = 2000

    # ClaRA Settings
    enable_clarifications: bool = True
    max_clarification_questions: int = 3
    similarity_threshold: float = 0.7
    top_k_documents: int = 5

    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings"""
    settings = Settings()

    # Create necessary directories
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.vector_db_dir, exist_ok=True)

    return settings


settings = get_settings()
