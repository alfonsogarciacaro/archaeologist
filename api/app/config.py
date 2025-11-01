import os
from functools import lru_cache

class Settings:
    def __init__(self):
        # Environment
        self.NODE_ENV = os.getenv("NODE_ENV")
        if self.NODE_ENV is None:
            raise ValueError("NODE_ENV environment variable is required")
        
        self.COMPOSE_PROJECT_NAME = os.getenv("COMPOSE_PROJECT_NAME")
        if self.COMPOSE_PROJECT_NAME is None:
            raise ValueError("COMPOSE_PROJECT_NAME environment variable is required")
        
        # Ports
        self.WEB_PORT = int(os.getenv("WEB_PORT"))
        self.SCANNER_PORT = int(os.getenv("SCANNER_PORT"))
        self.CHROMADB_PORT = int(os.getenv("CHROMADB_PORT"))
        self.UI_DEV_PORT = int(os.getenv("UI_DEV_PORT"))
        
        # Service URLs
        self.SCANNER_URL = os.getenv("SCANNER_URL")
        if self.SCANNER_URL is None:
            raise ValueError("SCANNER_URL environment variable is required")
        
        self.CHROMADB_HOST = os.getenv("CHROMADB_HOST")
        if self.CHROMADB_HOST is None:
            raise ValueError("CHROMADB_HOST environment variable is required")
        
        self.CHROMADB_SERVER_HTTP_PORT = int(os.getenv("CHROMADB_SERVER_HTTP_PORT"))
        if self.CHROMADB_SERVER_HTTP_PORT is None:
            raise ValueError("CHROMADB_SERVER_HTTP_PORT environment variable is required")
        
        self.CHROMADB_URL = f"http://{self.CHROMADB_HOST}:{self.CHROMADB_SERVER_HTTP_PORT}"
        
        # LLM Configuration
        self.LLM_API_URL = os.getenv("LLM_API_URL")
        if self.LLM_API_URL is None:
            raise ValueError("LLM_API_URL environment variable is required")
        
        # Paths
        self.MOCK_ENTERPRISE_PATH = "/app/mock_enterprise"
        
    @property
    def is_development(self) -> bool:
        return self.NODE_ENV == "development"
        
    @property
    def is_production(self) -> bool:
        return self.NODE_ENV == "production"

@lru_cache()
def get_settings():
    return Settings()