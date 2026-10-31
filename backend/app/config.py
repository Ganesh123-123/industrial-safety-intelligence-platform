import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Root directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Industrial Safety Event Intelligence Platform"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{BASE_DIR / 'industrial_safety.db'}"
    )
    
    # Paths
    DATA_DIR: Path = BASE_DIR / "data"
    GENERATED_DATA_DIR: Path = BASE_DIR / "data" / "generated"
    EVALUATION_DATA_DIR: Path = BASE_DIR / "data" / "evaluation"
    DOCS_DIR: Path = BASE_DIR / "docs"
    
    # Generator defaults
    DEFAULT_SEED: int = 20261022
    DEFAULT_STARTER_EVENTS: int = 2500
    DEFAULT_FULL_EVENTS: int = 50000
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Ensure directories exist
settings.GENERATED_DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.EVALUATION_DATA_DIR.mkdir(parents=True, exist_ok=True)
