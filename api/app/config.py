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
        self.WEB_PORT = int(os.getenv("WEB_PORT", 8000))
        self.SCANNER_PORT = int(os.getenv("SCANNER_PORT", 8002))

        # Service URLs
        self.SCANNER_URL = os.getenv("SCANNER_URL")
        if self.SCANNER_URL is None:
            raise ValueError("SCANNER_URL environment variable is required")
        
        self.VECTORDB_HOST = os.getenv("VECTORDB_HOST")
        if self.VECTORDB_HOST is None:
            raise ValueError("VECTORDB_HOST environment variable is required")

        self.VECTORDB_PORT = int(os.getenv("VECTORDB_PORT", 8001))
        if self.VECTORDB_PORT is None:
            raise ValueError("VECTORDB_PORT environment variable is required")
        
        self.VECTORDB_URL = f"http://{self.VECTORDB_HOST}:{self.VECTORDB_PORT}"
        
        # Vector Database Configuration
        self.VECTORDB_TYPE = os.getenv("VECTORDB_TYPE", "qdrant")
        self.VECTORDB_COLLECTION_PREFIX = os.getenv("VECTORDB_COLLECTION_PREFIX", "archaeologist")
        
        # LLM Configuration
        self.LLM_API_URL = os.getenv("LLM_API_URL")
        self.LLM_API_KEY = os.getenv("LLM_API_KEY")
        self.LLM_MODEL = os.getenv("LLM_MODEL")
        self.LLM_PROVIDER = os.getenv("LLM_PROVIDER")
        
        if self.LLM_API_URL is None:
            raise ValueError("LLM_API_URL environment variable is required")
        
        # Database Configuration
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///archaeologist.db")
        self.database_type = os.getenv("DATABASE_TYPE", "sqlite")
        
        # JWT Configuration
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 15))
        self.JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", 7))
        
        # Telemetry Configuration
        self.OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "archaeologist-api")
        self.OTEL_SERVICE_VERSION = os.getenv("OTEL_SERVICE_VERSION", "1.0.0")
        self.OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        self.OTEL_EXPORTER_OTLP_PROTOCOL = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
        self.OTEL_RESOURCE_ATTRIBUTES = os.getenv("OTEL_RESOURCE_ATTRIBUTES", f"service.name={self.OTEL_SERVICE_NAME},service.version={self.OTEL_SERVICE_VERSION},deployment.environment={self.NODE_ENV}")
        
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
