"""
Embedding Interface

This module defines the abstract interface for embedding implementations,
providing a contract that all embedding providers must follow.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class EmbeddingInterface(ABC):
    """
    Abstract interface for embedding providers.
    
    This interface defines the contract that all embedding implementations
    must follow, ensuring consistency and making it easy to swap providers.
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the embedding model"""
        pass
    
    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (one per input text)
        """
        pass
    
    @abstractmethod
    async def embed_single(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding vector
        """
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors
        
        Returns:
            Dimension of the embedding vectors
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the embedding model
        
        Returns:
            Dictionary containing model information
        """
        pass
    
    async def embed_batch(
        self, 
        texts: List[str], 
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts in batches
        
        Args:
            texts: List of text strings to embed
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of embedding vectors (one per input text)
        """
        if not texts:
            return []
        
        logger.info(f"Embedding {len(texts)} texts in batches of {batch_size}")
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.debug(f"Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
            
            batch_embeddings = await self.embed(batch)
            all_embeddings.extend(batch_embeddings)
        
        logger.info(f"Successfully generated {len(all_embeddings)} embeddings")
        return all_embeddings