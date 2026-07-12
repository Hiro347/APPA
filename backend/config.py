import os
from pathlib import Path
from dotenv import load_dotenv

# Load env file from the project root if it exists
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_NAME: str = "APPA (Analisa Pasar Pintar & Akurat)"
    
    # Qdrant Database Settings
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", 6333))
    QDRANT_COLLECTION: str = "regulations"
    
    # Hugging Face Settings
    HF_MODEL_ID: str = os.getenv("HF_MODEL_ID", "Qwen/Qwen2.5-7B-Instruct")
    HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "")
    
    # Search API Settings
    SEARCH_API_KEY: str = os.getenv("SEARCH_API_KEY", "")
    
    # Relational Database Settings
    # Store SQLite db file inside the backend data directory
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/appa.db")

settings = Settings()
