from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Stealth API"
    VERSION: str = "1.0.0"
    ALLOWED_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"

settings = Settings()