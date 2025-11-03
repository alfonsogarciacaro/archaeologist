"""
RAG Models

This module contains Pydantic models for RAG requests and responses.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class IngestRequest(BaseModel):
    """Request model for document ingestion"""
    file_name: str = Field(..., description="Name of the file being ingested")
    project: str = Field(..., description="Project name the file belongs to")
    content: str = Field(..., description="Content of the file")
    file_type: str = Field(..., description="Type of file (python, javascript, sql, etc.)")
    timestamp: str = Field(..., description="Timestamp of the file")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_name": "user_service.py",
                "project": "financial_reports",
                "content": "def get_user(user_id): ...",
                "file_type": "python",
                "timestamp": "2023-10-27T10:30:00Z",
                "metadata": {"author": "dev-team", "version": "1.2.0"}
            }
        }


class IngestResponse(BaseModel):
    """Response model for document ingestion"""
    chunks_created: int = Field(..., description="Number of chunks created")
    collection_name: str = Field(..., description="Name of the collection used")
    processing_time_ms: int = Field(..., description="Total processing time in milliseconds")
    chunk_ids: List[str] = Field(..., description="List of chunk IDs created")
    embedding_stats: Dict[str, Any] = Field(..., description="Embedding generation statistics")
    chunking_stats: Dict[str, Any] = Field(..., description="Text chunking statistics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "chunks_created": 5,
                "collection_name": "archaeologist_financial_reports_user_service_py",
                "processing_time_ms": 1250,
                "chunk_ids": ["chunk_0", "chunk_1", "chunk_2", "chunk_3", "chunk_4"],
                "embedding_stats": {
                    "total_embeddings": 5,
                    "avg_embedding_time_ms": 45,
                    "model_info": {"model_name": "BAAI/bge-small-en-v1.5", "backend": "llama.cpp"}
                },
                "chunking_stats": {
                    "total_chunks": 5,
                    "total_tokens": 1250,
                    "avg_tokens_per_chunk": 250
                }
            }
        }


class SearchRequest(BaseModel):
    """Request model for semantic search"""
    query: str = Field(..., description="Search query")
    project: Optional[str] = Field(None, description="Project to search within (optional)")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    score_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "user authentication logic",
                "project": "financial_reports",
                "limit": 10,
                "score_threshold": 0.7
            }
        }


class SearchResult(BaseModel):
    """Single search result"""
    chunk_id: str = Field(..., description="ID of the chunk")
    content: str = Field(..., description="Content of the chunk")
    score: float = Field(..., description="Similarity score")
    metadata: Dict[str, Any] = Field(..., description="Chunk metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "chunk_2",
                "content": "def authenticate_user(username, password): ...",
                "score": 0.85,
                "metadata": {
                    "file_name": "user_service.py",
                    "file_type": "python",
                    "project": "financial_reports",
                    "chunk_index": 2
                }
            }
        }


class SearchResponse(BaseModel):
    """Response model for semantic search"""
    results: List[SearchResult] = Field(..., description="Search results")
    total_found: int = Field(..., description="Total number of results found")
    query_time_ms: int = Field(..., description="Time taken for search in milliseconds")
    query: str = Field(..., description="Original search query")
    
    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "chunk_id": "chunk_2",
                        "content": "def authenticate_user(username, password): ...",
                        "score": 0.85,
                        "metadata": {
                            "file_name": "user_service.py",
                            "file_type": "python",
                            "project": "financial_reports"
                        }
                    }
                ],
                "total_found": 1,
                "query_time_ms": 150,
                "query": "user authentication logic"
            }
        }


class HealthCheckResponse(BaseModel):
    """Response model for RAG service health check"""
    status: str = Field(..., description="Health status")
    embedding_model: Dict[str, Any] = Field(..., description="Embedding model information")
    vector_db: Dict[str, Any] = Field(..., description="Vector database information")
    collections: List[str] = Field(..., description="Available collections")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "embedding_model": {
                    "model_name": "BAAI/bge-small-en-v1.5",
                    "backend": "llama.cpp",
                    "embedding_dimension": 384
                },
                "vector_db": {
                    "type": "qdrant",
                    "host": "localhost",
                    "port": 6333
                },
                "collections": [
                    "archaeologist_financial_reports_user_service_py",
                    "archaeologist_financial_reports_database_sql"
                ]
            }
        }