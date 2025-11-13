from pydantic_settings import BaseSettings
from typing import List
import os
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Stealth Graph RAG API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    ALLOWED_ORIGINS: List[str] = []

    # Azure Blob Storage
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_ACCOUNT_NAME: str = ""
    AZURE_STORAGE_ACCOUNT_KEY: str = ""
    AZURE_STORAGE_CONTAINER_NAME: str = "documents"

    # LlamaParse
    LLAMA_CLOUD_API_KEY: str = ""

    # Google Gemini
    GOOGLE_API_KEY: str = ""
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"  # 768 dimensions
    GEMINI_EMBEDDING_DIMENSION: int = 768

    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = ""
    PINECONE_INDEX_NAME: str = "graph-rag-embeddings"
    PINECONE_DIMENSION: int = 768
    PINECONE_METRIC: str = "cosine"

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = ""
    NEO4J_DATABASE: str = "neo4j"

    # Processing Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_WORKERS: int = 4

    # Multi-modal Settings
    ENABLE_IMAGE_EXTRACTION: bool = True
    IMAGE_DESCRIPTION_MODEL: str = "gemini-1.5-flash"

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set CORS origins based on environment
        if not self.ALLOWED_ORIGINS:
            if self.ENVIRONMENT == "production":
                # In production, set specific origins via environment variable
                origins_str = os.getenv("ALLOWED_ORIGINS", "")
                self.ALLOWED_ORIGINS = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
                if not self.ALLOWED_ORIGINS:
                    logger.warning("No ALLOWED_ORIGINS set in production environment. CORS will block all origins.")
            else:
                # Development: allow localhost variations
                self.ALLOWED_ORIGINS = [
                    "http://localhost:3000",
                    "http://localhost:8000",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:8000"
                ]

    def validate_required_settings(self) -> None:
        """Validate that all required settings are present"""
        required_settings = {
            "AZURE_STORAGE_CONNECTION_STRING": self.AZURE_STORAGE_CONNECTION_STRING,
            "LLAMA_CLOUD_API_KEY": self.LLAMA_CLOUD_API_KEY,
            "GOOGLE_API_KEY": self.GOOGLE_API_KEY,
            "PINECONE_API_KEY": self.PINECONE_API_KEY,
            "NEO4J_PASSWORD": self.NEO4J_PASSWORD,
        }

        missing = [key for key, value in required_settings.items() if not value]

        if missing:
            error_msg = f"Missing required environment variables: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("All required environment variables are set")

settings = Settings()