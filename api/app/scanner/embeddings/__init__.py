"""
Embeddings Module

This module provides embedding functionality for the RAG system,
supporting both local GGUF models and external embedding services.
"""

from .embedding_interface import EmbeddingInterface
from .local_embedding import LocalEmbedding
from .embedding_factory import EmbeddingFactory

__all__ = [
    "EmbeddingInterface",
    "LocalEmbedding", 
    "EmbeddingFactory"
]