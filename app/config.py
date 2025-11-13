from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Stealth Graph RAG API"
    VERSION: str = "1.0.0"
    ALLOWED_ORIGINS: List[str] = ["*"]

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

settings = Settings()