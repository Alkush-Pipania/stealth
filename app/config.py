from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Existing settings
    PROJECT_NAME: str = "Stealth API"
    VERSION: str = "1.0.0"
    ALLOWED_ORIGINS: list = ["*"]
    
    # LLM API Keys
    GOOGLE_API_KEY: str
    # LlamaParse
    LLAMA_CLOUD_API_KEY: str
    
    # Neo4j Configuration
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str
    
    # Pinecone Configuration
    PINECONE_API_KEY: str
    PINECONE_HOST_URL: str 
    pinecone_environment : str = "us-east-1"
    INDEX: str
    
    # Embedding Configuration (Gemini)
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"  # Gemini embedding with MRL support
    EMBEDDING_DIM: int = 3072  # gemini-embedding-001 supports 768, 1536, or 3072 dimensions (default 3072)
    
    # Chunking Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Add lowercase aliases for compatibility
    @property
    def chunk_size(self):
        return self.CHUNK_SIZE
    
    @property
    def chunk_overlap(self):
        return self.CHUNK_OVERLAP
    
    # Azure Configuration (Optional - not needed for public URLs)
    DOCUMENT_CONTAINER : str = ""
    AZURE_STORAGE_ACCOUNT_NAME : str = ""
    BLOBSERVICE_SAS_URL : str = ""
    

    
    # Optional: Redis (if using Celery)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    model_config = ConfigDict(
        env_file=".env",
        extra="allow"
    )

@lru_cache()
def get_settings():
    return Settings()

settings = Settings()