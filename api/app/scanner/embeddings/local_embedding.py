"""
Local Embedding Implementation

This module provides a local embedding implementation using GGUF models
with llama.cpp, offering fast and private text embeddings.
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    logging.warning("llama-cpp-python not available, falling back to sentence-transformers")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from .embedding_interface import EmbeddingInterface

logger = logging.getLogger(__name__)


class LocalEmbedding(EmbeddingInterface):
    """
    Local embedding implementation using GGUF models with llama.cpp.
    
    This implementation provides fast, private embeddings using quantized
    models that run entirely on CPU, making it ideal for code archaeology.
    """
    
    def __init__(
        self,
        model_path: str,
        model_name: str = "BAAI/bge-small-en-v1.5",
        embedding_dimension: int = 384,
        max_context_length: int = 512,
        n_threads: Optional[int] = None
    ):
        """
        Initialize the local embedding model.
        
        Args:
            model_path: Path to the GGUF model file
            model_name: Name of the embedding model
            embedding_dimension: Dimension of the embedding vectors
            max_context_length: Maximum context length for embeddings
            n_threads: Number of CPU threads to use (auto-detect if None)
        """
        self.model_path = Path(model_path)
        self.model_name = model_name
        self.embedding_dimension = embedding_dimension
        self.max_context_length = max_context_length
        self.n_threads = n_threads or os.cpu_count() or 4
        
        self.model = None
        self.fallback_model = None
        self.using_fallback = False
        
        logger.info(f"Initialized LocalEmbedding with model: {model_name}")
        logger.info(f"Model path: {model_path}")
        logger.info(f"Embedding dimension: {embedding_dimension}")
        logger.info(f"CPU threads: {self.n_threads}")
    
    async def initialize(self) -> None:
        """Initialize the embedding model"""
        start_time = time.time()
        
        # Try to load GGUF model with llama.cpp
        if LLAMA_AVAILABLE and self.model_path.exists():
            try:
                logger.info(f"Loading GGUF model from {self.model_path}")
                self.model = Llama(
                    model_path=str(self.model_path),
                    embedding=True,
                    n_ctx=self.max_context_length,
                    n_threads=self.n_threads,
                    verbose=False
                )
                
                # Test the model
                test_embedding = self.model.embed("test")
                if len(test_embedding) != self.embedding_dimension:
                    raise ValueError(f"Expected embedding dimension {self.embedding_dimension}, got {len(test_embedding)}")
                
                logger.info(f"Successfully loaded GGUF model in {time.time() - start_time:.2f}s")
                return
                
            except Exception as e:
                logger.error(f"Failed to load GGUF model: {e}")
                logger.info("Falling back to sentence-transformers")
        
        # Fallback to sentence-transformers
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Loading sentence-transformers model: {self.model_name}")
                self.fallback_model = SentenceTransformer(self.model_name)
                self.using_fallback = True
                
                # Test the model
                test_embedding = self.fallback_model.encode("test")
                if len(test_embedding) != self.embedding_dimension:
                    raise ValueError(f"Expected embedding dimension {self.embedding_dimension}, got {len(test_embedding)}")
                
                logger.info(f"Successfully loaded sentence-transformers model in {time.time() - start_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Failed to load sentence-transformers model: {e}")
                raise RuntimeError(f"Failed to initialize any embedding model: {e}")
        else:
            raise RuntimeError("No embedding backend available. Install llama-cpp-python or sentence-transformers.")
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (one per input text)
        """
        if not texts:
            return []
        
        start_time = time.time()
        
        if self.using_fallback:
            # Use sentence-transformers
            embeddings = self.fallback_model.encode(
                texts,
                batch_size=32,
                normalize_embeddings=True,
                convert_to_numpy=True
            )
            result = [embedding.tolist() for embedding in embeddings]
        else:
            # Use llama.cpp GGUF model
            result = []
            for text in texts:
                # Truncate text if too long
                if len(text) > self.max_context_length * 4:  # Rough estimate
                    text = text[:self.max_context_length * 4]
                
                embedding = self.model.embed(text)
                result.append(embedding)
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Embedded {len(texts)} texts in {elapsed_time:.3f}s ({len(texts)/elapsed_time:.1f} texts/sec)")
        
        return result
    
    async def embed_single(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding vector
        """
        embeddings = await self.embed([text])
        return embeddings[0] if embeddings else []
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors"""
        return self.embedding_dimension
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model"""
        return {
            "model_name": self.model_name,
            "model_path": str(self.model_path),
            "embedding_dimension": self.embedding_dimension,
            "max_context_length": self.max_context_length,
            "n_threads": self.n_threads,
            "using_fallback": self.using_fallback,
            "backend": "sentence-transformers" if self.using_fallback else "llama.cpp",
            "model_loaded": self.model is not None or self.fallback_model is not None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the embedding model
        
        Returns:
            Dictionary containing health check results
        """
        try:
            start_time = time.time()
            test_text = "This is a test for embedding generation."
            embedding = await self.embed_single(test_text)
            elapsed_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "embedding_dimension": len(embedding),
                "response_time_ms": int(elapsed_time * 1000),
                "model_info": self.get_model_info()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model_info": self.get_model_info()
            }