"""
Vector Database Factory

This module provides a factory for creating vector database instances,
allowing for easy switching between different vector database implementations.
"""

from typing import Optional
import logging
from .vector_db import VectorDatabaseInterface
from .qdrant_adapter import QdrantAdapter
from ..config import get_settings

logger = logging.getLogger(__name__)


class VectorDatabaseFactory:
    """
    Factory class for creating vector database instances.
    
    This factory provides a centralized way to create and configure
    vector database instances based on the configuration.
    """
    
    _instance: Optional['VectorDatabaseFactory'] = None
    _vector_db: Optional[VectorDatabaseInterface] = None
    
    def __new__(cls) -> 'VectorDatabaseFactory':
        """Singleton pattern to ensure only one factory instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def get_vector_db(cls) -> VectorDatabaseInterface:
        """
        Get the configured vector database instance.
        
        Returns:
            VectorDatabaseInterface: The configured vector database instance
            
        Raises:
            ValueError: If the vector database type is not supported
        """
        if cls._vector_db is None:
            settings = get_settings()
            factory = cls()
            cls._vector_db = await factory._create_vector_db(settings)
        
        return cls._vector_db
    
    async def _create_vector_db(self, settings) -> VectorDatabaseInterface:
        """
        Create a vector database instance based on the configuration.
        
        Args:
            settings: Application settings
            
        Returns:
            VectorDatabaseInterface: The created vector database instance
            
        Raises:
            ValueError: If the vector database type is not supported
        """
        vector_db_type = settings.VECTORDB_TYPE.lower()
        
        if vector_db_type == "qdrant":
            logger.info("Creating Qdrant adapter")
            vector_db = QdrantAdapter(
                host=settings.VECTORDB_HOST,
                port=settings.VECTORDB_PORT
            )
        else:
            raise ValueError(f"Unsupported vector database type: {vector_db_type}")
        
        # Connect to the vector database
        await vector_db.connect()
        
        return vector_db
    
    @classmethod
    async def reset(cls) -> None:
        """
        Reset the factory and disconnect from the vector database.
        
        This is useful for testing or when changing configurations.
        """
        if cls._vector_db:
            await cls._vector_db.disconnect()
            cls._vector_db = None
        
        cls._instance = None


async def get_vector_db() -> VectorDatabaseInterface:
    """
    Convenience function to get the configured vector database instance.
    
    Returns:
        VectorDatabaseInterface: The configured vector database instance
    """
    return await VectorDatabaseFactory.get_vector_db()