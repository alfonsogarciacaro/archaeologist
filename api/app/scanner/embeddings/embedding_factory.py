"""
Embedding Factory

This module provides a factory for creating embedding instances,
allowing for easy switching between different embedding providers.
"""

from typing import Optional
import logging
from .embedding_interface import EmbeddingInterface
from .local_embedding import LocalEmbedding

logger = logging.getLogger(__name__)


class EmbeddingFactory:
    """
    Factory class for creating embedding instances.
    
    This factory provides a centralized way to create and configure
    embedding instances based on the configuration.
    """
    
    _instance: Optional['EmbeddingFactory'] = None
    _embedding: Optional[EmbeddingInterface] = None
    
    def __new__(cls) -> 'EmbeddingFactory':
        """Singleton pattern to ensure only one factory instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def get_embedding(cls, config) -> EmbeddingInterface:
        """
        Get the configured embedding instance.
        
        Args:
            config: Configuration object with embedding settings
            
        Returns:
            EmbeddingInterface: The configured embedding instance
            
        Raises:
            ValueError: If the embedding type is not supported
        """
        if cls._embedding is None:
            factory = cls()
            cls._embedding = await factory._create_embedding(config)
        
        return cls._embedding
    
    async def _create_embedding(self, config) -> EmbeddingInterface:
        """
        Create an embedding instance based on the configuration.
        
        Args:
            config: Configuration object with embedding settings
            
        Returns:
            EmbeddingInterface: The created embedding instance
            
        Raises:
            ValueError: If the embedding type is not supported
        """
        embedding_type = getattr(config, 'EMBEDDING_TYPE', 'local').lower()
        
        if embedding_type == "local":
            logger.info("Creating local embedding model")
            embedding = LocalEmbedding(
                model_path=getattr(config, 'EMBEDDING_MODEL_PATH', '/app/models/bge-small-en-v1.5.gguf'),
                model_name=getattr(config, 'EMBEDDING_MODEL', 'BAAI/bge-small-en-v1.5'),
                embedding_dimension=getattr(config, 'EMBEDDING_DIMENSION', 384),
                max_context_length=getattr(config, 'MAX_CONTEXT_LENGTH', 512),
                n_threads=getattr(config, 'EMBEDDING_THREADS', None)
            )
        else:
            raise ValueError(f"Unsupported embedding type: {embedding_type}")
        
        # Initialize the embedding model
        await embedding.initialize()
        
        return embedding
    
    @classmethod
    async def reset(cls) -> None:
        """
        Reset the factory and embedding instance.
        
        This is useful for testing or when changing configurations.
        """
        cls._embedding = None
        cls._instance = None


async def get_embedding(config) -> EmbeddingInterface:
    """
    Convenience function to get the configured embedding instance.
    
    Args:
        config: Configuration object with embedding settings
        
    Returns:
        EmbeddingInterface: The configured embedding instance
    """
    return await EmbeddingFactory.get_embedding(config)