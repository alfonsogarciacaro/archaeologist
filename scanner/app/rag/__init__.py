"""
RAG Module

This module provides RAG (Retrieval-Augmented Generation) functionality
for the scanner service, including document ingestion and semantic search.
"""

from .rag_service import RAGService, get_rag_service
from .models import (
    IngestRequest,
    IngestResponse,
    SearchRequest,
    SearchResponse,
    SearchResult as RAGSearchResult
)

__all__ = [
    "RAGService",
    "get_rag_service",
    "IngestRequest",
    "IngestResponse", 
    "SearchRequest",
    "SearchResponse",
    "RAGSearchResult"
]