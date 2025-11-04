"""
Text Processing Module

This module provides text processing functionality for the RAG system,
including intelligent chunking with overlap and code-aware splitting.
"""

from .chunker import TextChunker
from .preprocessor import TextPreprocessor

__all__ = [
    "TextChunker",
    "TextPreprocessor"
]