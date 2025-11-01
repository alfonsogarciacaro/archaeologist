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
        self.SCANNER_PORT = int(os.getenv("SCANNER_PORT"))
        if os.getenv("SCANNER_PORT") is None:
            raise ValueError("SCANNER_PORT environment variable is required")
        
        # Paths
        self.MOCK_ENTERPRISE_PATH = "/app/mock_enterprise"

@lru_cache()
def get_settings():
    return Settings()