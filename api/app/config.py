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

        self.VECTORDB_HOST = os.getenv("VECTORDB_HOST", "localhost")
        self.VECTORDB_PORT = int(os.getenv("VECTORDB_PORT", "6333"))
        self.VECTORDB_URL = f"http://{self.VECTORDB_HOST}:{self.VECTORDB_PORT}"

        # Vector Database Configuration
        self.VECTORDB_TYPE = os.getenv("VECTORDB_TYPE", "qdrant")
        self.VECTORDB_COLLECTION_PREFIX = os.getenv("VECTORDB_COLLECTION_PREFIX", "archaeologist")

        # RAG Configuration (now integrated)
        self.EMBEDDING_TYPE = os.getenv("EMBEDDING_TYPE", "local")
        self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        self.EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", "./models/bge-small-en-v1.5.gguf")
        self.EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))
        self.MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "512"))
        self.EMBEDDING_THREADS = os.getenv("EMBEDDING_THREADS")  # None for auto-detect

        # Chunking Configuration
        self.CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
        self.CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
        self.MIN_CHUNK_SIZE = int(os.getenv("MIN_CHUNK_SIZE", "100"))
        self.MAX_EMBEDDING_BATCH_SIZE = int(os.getenv("MAX_EMBEDDING_BATCH_SIZE", "32"))

        # LLM Configuration (now integrated)
        self.LLM_API_URL = os.getenv("LLM_API_URL")
        self.LLM_API_KEY = os.getenv("LLM_API_KEY")
        self.LLM_MODEL = os.getenv("LLM_MODEL", "llama2")
        self.LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
        
        # Database Configuration
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///archaeologist.db")
        self.database_type = os.getenv("DATABASE_TYPE", "sqlite")
        
        # JWT Configuration
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 15))
        self.JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", 7))
        self.JWT_ISSUER = os.getenv("JWT_ISSUER", "archaeologist-api")
        self.JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "archaeologist-ui")
        
        # Telemetry Configuration
        self.OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "archaeologist-api")
        self.OTEL_SERVICE_VERSION = os.getenv("OTEL_SERVICE_VERSION", "1.0.0")
        self.OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        self.OTEL_EXPORTER_OTLP_PROTOCOL = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
        self.OTEL_RESOURCE_ATTRIBUTES = os.getenv("OTEL_RESOURCE_ATTRIBUTES", f"service.name={self.OTEL_SERVICE_NAME},service.version={self.OTEL_SERVICE_VERSION},deployment.environment={self.NODE_ENV}")
        
        # Redis Configuration
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        self.REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
        self.REDIS_DB = int(os.getenv("REDIS_DB", "0"))
        self.REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

        # Job Queue Configuration
        self.JOB_QUEUE_NAME = os.getenv("JOB_QUEUE_NAME", "archaeologist_jobs")
        self.JOB_RESULT_TTL = int(os.getenv("JOB_RESULT_TTL", "86400"))  # 24 hours
        self.JOB_TIMEOUT = int(os.getenv("JOB_TIMEOUT", "3600"))  # 1 hour
        self.JOB_POLL_INTERVAL = int(os.getenv("JOB_POLL_INTERVAL", "5"))  # seconds

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
