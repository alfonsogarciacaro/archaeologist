"""
RAG (Retrieval-Augmented Generation) Engine

This module provides the RAG engine implementation using the vector database
for semantic search capabilities in the Enterprise Code Archaeologist.
"""

import logging
from typing import List, Dict, Any, Optional
from .vector_db import Document, SearchResult, VectorDatabaseInterface
from .vector_db_factory import get_vector_db
from ..config import get_settings

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Retrieval-Augmented Generation Engine for semantic search.
    
    This engine uses the vector database to perform semantic searches
    across the enterprise codebase and documentation.
    """
    
    def __init__(self):
        self.vector_db: Optional[VectorDatabaseInterface] = None
        self.settings = get_settings()
    
    async def initialize(self) -> None:
        """Initialize the RAG engine by connecting to the vector database"""
        try:
            # Get the vector database instance
            self.vector_db = await get_vector_db()
            
            # Double-check that we got a valid instance
            if self.vector_db is None:
                raise RuntimeError("Failed to get vector database instance from factory")
            
            # Ensure default collections exist
            collections = await self.vector_db.list_collections()
            code_collection = f"{self.settings.VECTORDB_COLLECTION_PREFIX}_code"
            docs_collection = f"{self.settings.VECTORDB_COLLECTION_PREFIX}_docs"
            
            if code_collection not in collections:
                await self.vector_db.create_collection(
                    name=code_collection,
                    metadata={"description": "Code snippets and functions"}
                )
            
            if docs_collection not in collections:
                await self.vector_db.create_collection(
                    name=docs_collection,
                    metadata={"description": "Documentation and comments"}
                )
            
            logger.info("RAG Engine initialized successfully")
        except Exception as e:
            # Reset vector_db to None on failure to ensure consistent state
            self.vector_db = None
            logger.error(f"Failed to initialize RAG Engine: {str(e)}")
            raise
    
    async def search_code(
        self,
        query: str,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Search for code related to the query.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of search results containing relevant code
        """
        if not self.vector_db:
            await self.initialize()
            # Double-check after initialization
            if not self.vector_db:
                raise RuntimeError("Failed to initialize vector database for code search")
        
        collection_name = f"{self.settings.VECTORDB_COLLECTION_PREFIX}_code"
        return await self.vector_db.search(
            collection_name=collection_name,
            query=query,
            limit=limit
        )
    
    async def search_documentation(
        self,
        query: str,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Search for documentation related to the query.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of search results containing relevant documentation
        """
        if not self.vector_db:
            await self.initialize()
            # Double-check after initialization
            if not self.vector_db:
                raise RuntimeError("Failed to initialize vector database for documentation search")
        
        collection_name = f"{self.settings.VECTORDB_COLLECTION_PREFIX}_docs"
        return await self.vector_db.search(
            collection_name=collection_name,
            query=query,
            limit=limit
        )
    
    async def add_code_document(
        self,
        document: Document
    ) -> str:
        """
        Add a code document to the vector database.
        
        Args:
            document: Document to add
            
        Returns:
            ID of the added document
        """
        if not self.vector_db:
            await self.initialize()
            # Double-check after initialization
            if not self.vector_db:
                raise RuntimeError("Failed to initialize vector database for adding code document")
        
        collection_name = f"{self.settings.VECTORDB_COLLECTION_PREFIX}_code"
        ids = await self.vector_db.add_documents(
            collection_name=collection_name,
            documents=[document]
        )
        return ids[0]
    
    async def add_documentation(
        self,
        document: Document
    ) -> str:
        """
        Add a documentation document to the vector database.
        
        Args:
            document: Document to add
            
        Returns:
            ID of the added document
        """
        if not self.vector_db:
            await self.initialize()
            # Double-check after initialization
            if not self.vector_db:
                raise RuntimeError("Failed to initialize vector database for adding documentation")
        
        collection_name = f"{self.settings.VECTORDB_COLLECTION_PREFIX}_docs"
        ids = await self.vector_db.add_documents(
            collection_name=collection_name,
            documents=[document]
        )
        return ids[0]
    
    async def hybrid_search(
        self, 
        query: str, 
        limit: int = 10
    ) -> Dict[str, List[SearchResult]]:
        """
        Perform a hybrid search across both code and documentation.
        
        Args:
            query: Search query
            limit: Maximum number of results per collection
            
        Returns:
            Dictionary with 'code' and 'docs' keys containing respective results
        """
        code_results = await self.search_code(query, limit)
        docs_results = await self.search_documentation(query, limit)
        
        return {
            "code": code_results,
            "docs": docs_results
        }


# Singleton instance for easy access
_rag_engine: Optional[RAGEngine] = None


async def get_rag_engine() -> RAGEngine:
    """
    Get the singleton RAG engine instance.
    
    Returns:
        RAGEngine: The singleton instance
    """
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
        await _rag_engine.initialize()
    return _rag_engine