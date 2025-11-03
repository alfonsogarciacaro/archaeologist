"""
RAG Service

This module provides the main RAG (Retrieval-Augmented Generation) service
for document ingestion and semantic search.
"""

import time
import logging
import hashlib
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from app.embeddings.embedding_factory import get_embedding
from app.text_processing.chunker import TextChunker
from app.text_processing.preprocessor import TextPreprocessor
from app.config import get_settings
from .models import (
    IngestRequest,
    IngestResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    HealthCheckResponse
)

from ..tools.vector_db_factory import get_vector_db
from ..tools.vector_db import Document

logger = logging.getLogger(__name__)


class RAGService:
    """
    Main RAG service for document ingestion and semantic search.
    
    This service handles:
    - Document preprocessing and chunking
    - Embedding generation
    - Vector database operations
    - Semantic search
    """
    
    def __init__(self):
        """Initialize RAG service"""
        self.settings = get_settings()
        self.embedding_model = None
        self.vector_db = None
        self.chunker = None
        self.preprocessor = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize RAG service components"""
        if self._initialized:
            return
        
        start_time = time.time()
        logger.info("Initializing RAG service...")
        
        try:
            # Initialize embedding model
            logger.info("Initializing embedding model...")
            self.embedding_model = await get_embedding(self.settings)
            logger.info(f"Embedding model initialized: {self.embedding_model.get_model_info()}")
            
            # Initialize vector database
            logger.info("Initializing vector database...")
            self.vector_db = await get_vector_db()
            logger.info(f"Vector database initialized: {type(self.vector_db).__name__}")
            
            # Initialize text processor
            logger.info("Initializing text processor...")
            self.chunker = TextChunker(
                chunk_size=self.settings.CHUNK_SIZE,
                chunk_overlap=self.settings.CHUNK_OVERLAP,
                min_chunk_size=self.settings.MIN_CHUNK_SIZE
            )
            
            self.preprocessor = TextPreprocessor(
                remove_comments=False,  # Keep comments for context
                normalize_whitespace=True,
                preserve_structure=True
            )
            
            self._initialized = True
            elapsed_time = time.time() - start_time
            logger.info(f"RAG service initialized successfully in {elapsed_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise
    
    def _normalize_collection_name(self, project: str, file_name: str) -> str:
        """
        Generate normalized collection name.
        
        Args:
            project: Project name
            file_name: File name
            
        Returns:
            Normalized collection name
        """
        # Remove file extension and normalize
        base_name = Path(file_name).stem
        normalized_base = re.sub(r'[^a-zA-Z0-9_]', '_', base_name.lower())
        normalized_project = re.sub(r'[^a-zA-Z0-9_]', '_', project.lower())
        
        # Create collection name
        collection_name = f"{self.settings.VECTORDB_COLLECTION_PREFIX}_{normalized_project}_{normalized_base}"
        
        # Ensure it doesn't exceed typical collection name limits
        if len(collection_name) > 100:
            # Hash the file name part if too long
            file_hash = hashlib.md5(file_name.encode()).hexdigest()[:8]
            collection_name = f"{self.settings.VECTORDB_COLLECTION_PREFIX}_{normalized_project}_{file_hash}"
        
        return collection_name
    
    async def ingest_document(self, request: IngestRequest) -> IngestResponse:
        """
        Ingest a document into the RAG system.
        
        Args:
            request: Ingest request containing document data
            
        Returns:
            Ingest response with statistics
        """
        start_time = time.time()
        
        logger.info(f"Starting ingestion for file: {request.file_name} (project: {request.project})")
        logger.info(f"Content length: {len(request.content)} characters")
        
        try:
            # Ensure service is initialized
            await self.initialize()
            
            # Step 1: Preprocess text
            logger.info("Step 1: Preprocessing text...")
            preprocess_start = time.time()
            preprocess_result = self.preprocessor.preprocess(
                content=request.content,
                file_name=request.file_name
            )
            preprocess_time = time.time() - preprocess_start
            logger.info(f"Text preprocessing completed in {preprocess_time:.3f}s")
            
            # Step 2: Create chunks
            logger.info("Step 2: Creating chunks...")
            chunk_start = time.time()
            chunks = self.chunker.chunk_document(
                content=preprocess_result['content'],
                file_name=request.file_name,
                metadata={
                    "project": request.project,
                    "timestamp": request.timestamp,
                    "original_length": len(request.content),
                    "preprocessing_stats": preprocess_result
                }
            )
            chunk_time = time.time() - chunk_start
            chunking_stats = self.chunker.get_chunking_stats(chunks)
            logger.info(f"Created {len(chunks)} chunks in {chunk_time:.3f}s")
            
            if not chunks:
                logger.warning("No chunks created from document")
                return IngestResponse(
                    chunks_created=0,
                    collection_name="",
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    chunk_ids=[],
                    embedding_stats={"error": "No chunks created"},
                    chunking_stats=chunking_stats
                )
            
            # Step 3: Generate embeddings
            logger.info("Step 3: Generating embeddings...")
            embed_start = time.time()
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = await self.embedding_model.embed_batch(
                texts=chunk_texts,
                batch_size=self.settings.MAX_EMBEDDING_BATCH_SIZE
            )
            embed_time = time.time() - embed_start
            
            embedding_stats = {
                "total_embeddings": len(embeddings),
                "embedding_time_ms": int(embed_time * 1000),
                "avg_embedding_time_ms": int((embed_time * 1000) / len(embeddings)),
                "model_info": self.embedding_model.get_model_info()
            }
            logger.info(f"Generated {len(embeddings)} embeddings in {embed_time:.3f}s")
            
            # Step 4: Store in vector database
            logger.info("Step 4: Storing in vector database...")
            store_start = time.time()
            
            # Create collection name
            collection_name = self._normalize_collection_name(request.project, request.file_name)
            logger.info(f"Using collection: {collection_name}")
            
            # Create collection if it doesn't exist
            await self.vector_db.create_collection(
                name=collection_name,
                vector_size=self.embedding_model.get_embedding_dimension()
            )
            
            # Create documents for vector database
            documents = []
            chunk_ids = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Update chunk metadata with embedding info
                chunk.metadata.update({
                    "embedding_index": i,
                    "embedding_dimension": len(embedding),
                    "ingestion_timestamp": time.time()
                })
                
                document = Document(
                    id=chunk.chunk_id,
                    content=chunk.text,
                    metadata=chunk.metadata
                )
                documents.append(document)
                chunk_ids.append(chunk.chunk_id)
            
            # Add documents to vector database
            await self.vector_db.add_documents(collection_name, documents)
            store_time = time.time() - store_start
            
            logger.info(f"Stored {len(documents)} documents in {store_time:.3f}s")
            
            # Calculate total processing time
            total_time = time.time() - start_time
            
            logger.info(f"Document ingestion completed successfully:")
            logger.info(f"  - File: {request.file_name}")
            logger.info(f"  - Project: {request.project}")
            logger.info(f"  - Chunks: {len(chunks)}")
            logger.info(f"  - Collection: {collection_name}")
            logger.info(f"  - Total time: {total_time:.3f}s")
            
            return IngestResponse(
                chunks_created=len(chunks),
                collection_name=collection_name,
                processing_time_ms=int(total_time * 1000),
                chunk_ids=chunk_ids,
                embedding_stats=embedding_stats,
                chunking_stats=chunking_stats
            )
            
        except Exception as e:
            logger.error(f"Error during document ingestion: {e}")
            total_time = time.time() - start_time
            
            return IngestResponse(
                chunks_created=0,
                collection_name="",
                processing_time_ms=int(total_time * 1000),
                chunk_ids=[],
                embedding_stats={"error": str(e)},
                chunking_stats={"error": str(e)}
            )
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Perform semantic search on ingested documents.
        
        Args:
            request: Search request
            
        Returns:
            Search response with results
        """
        start_time = time.time()
        
        logger.info(f"Performing semantic search: '{request.query}'")
        if request.project:
            logger.info(f"Limiting search to project: {request.project}")
        
        try:
            # Ensure service is initialized
            await self.initialize()
            
            # Get all collections if no project specified
            if request.project:
                # Find collections for the specific project
                all_collections = await self.vector_db.list_collections()
                project_collections = [
                    col for col in all_collections 
                    if col.startswith(f"{self.settings.VECTORDB_COLLECTION_PREFIX}_{request.project}_")
                ]
            else:
                # Use all collections
                project_collections = await self.vector_db.list_collections()
            
            if not project_collections:
                logger.warning("No collections found for search")
                return SearchResponse(
                    results=[],
                    total_found=0,
                    query_time_ms=int((time.time() - start_time) * 1000),
                    query=request.query
                )
            
            logger.info(f"Searching in {len(project_collections)} collections")
            
            # Generate query embedding
            query_embedding = await self.embedding_model.embed_single(request.query)
            
            # Search across all relevant collections
            all_results = []
            for collection_name in project_collections:
                try:
                    search_results = await self.vector_db.similarity_search(
                        collection_name=collection_name,
                        query_vector=query_embedding,
                        limit=request.limit
                    )
                    
                    # Convert to our format and filter by threshold
                    for result in search_results:
                        if result.score >= request.score_threshold:
                            search_result = SearchResult(
                                chunk_id=result.document.id,
                                content=result.document.content,
                                score=result.score,
                                metadata=result.document.metadata
                            )
                            all_results.append(search_result)
                            
                except Exception as e:
                    logger.warning(f"Error searching collection {collection_name}: {e}")
                    continue
            
            # Sort by score and limit results
            all_results.sort(key=lambda x: x.score, reverse=True)
            all_results = all_results[:request.limit]
            
            query_time = time.time() - start_time
            
            logger.info(f"Search completed: {len(all_results)} results in {query_time:.3f}s")
            
            return SearchResponse(
                results=all_results,
                total_found=len(all_results),
                query_time_ms=int(query_time * 1000),
                query=request.query
            )
            
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            query_time = time.time() - start_time
            
            return SearchResponse(
                results=[],
                total_found=0,
                query_time_ms=int(query_time * 1000),
                query=request.query
            )
    
    async def health_check(self) -> HealthCheckResponse:
        """
        Perform health check on RAG service.
        
        Returns:
            Health check response
        """
        try:
            await self.initialize()
            
            # Check embedding model
            embedding_health = await self.embedding_model.health_check()
            
            # Check vector database
            collections = await self.vector_db.list_collections()
            vector_db_info = {
                "type": type(self.vector_db).__name__,
                "collections_count": len(collections)
            }
            
            return HealthCheckResponse(
                status="healthy" if embedding_health["status"] == "healthy" else "degraded",
                embedding_model=embedding_health,
                vector_db=vector_db_info,
                collections=collections
            )
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthCheckResponse(
                status="unhealthy",
                embedding_model={"error": str(e)},
                vector_db={"error": str(e)},
                collections=[]
            )


# Global RAG service instance
_rag_service = None


async def get_rag_service() -> RAGService:
    """
    Get the global RAG service instance.
    
    Returns:
        RAG service instance
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
        await _rag_service.initialize()
    return _rag_service