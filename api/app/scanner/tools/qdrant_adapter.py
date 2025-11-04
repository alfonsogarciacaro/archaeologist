"""
Qdrant Adapter Implementation

This module provides a Qdrant implementation of the VectorDatabaseInterface,
allowing the application to use Qdrant as its vector database backend.
"""

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from typing import List, Dict, Any, Optional
import logging
import uuid
from .vector_db import (
    VectorDatabaseInterface, 
    Document, 
    SearchResult
)

logger = logging.getLogger(__name__)


class QdrantAdapter(VectorDatabaseInterface):
    """
    Qdrant implementation of the VectorDatabaseInterface.
    
    This adapter provides a concrete implementation of the vector database
    interface using Qdrant as the underlying storage engine.
    """
    
    def __init__(self, host: str = "localhost", port: int = 6333):
        """
        Initialize the Qdrant adapter.
        
        Args:
            host: Qdrant server host
            port: Qdrant server port
        """
        self.host = host
        self.port = port
        self.client = None
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to the Qdrant server"""
        try:
            # Connect to Qdrant server
            self.client = QdrantClient(host=self.host, port=self.port)
            # Test connection
            self.client.get_collections()
            self._connected = True
            logger.info(f"Connected to Qdrant at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from the Qdrant server"""
        if self.client:
            self.client = None
            self._connected = False
            logger.info("Disconnected from Qdrant")
    
    def _ensure_connected(self) -> None:
        """Ensure the client is connected to Qdrant"""
        if not self._connected or not self.client:
            raise RuntimeError("Not connected to Qdrant. Call connect() first.")
    
    async def create_collection(self, name: str, **kwargs) -> None:
        """Create a new collection in Qdrant"""
        self._ensure_connected()
        try:
            # Check if collection already exists
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if name in collection_names:
                logger.info(f"Collection '{name}' already exists")
                return
            
            # Create new collection with default vector size (can be overridden)
            vector_size = kwargs.get("vector_size", 1536)  # Default for OpenAI embeddings
            distance = kwargs.get("distance", Distance.COSINE)
            
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=vector_size, distance=distance)
            )
            logger.info(f"Created collection: {name}")
        except Exception as e:
            logger.error(f"Failed to create collection '{name}': {str(e)}")
            raise
    
    async def delete_collection(self, name: str) -> None:
        """Delete a collection from Qdrant"""
        self._ensure_connected()
        try:
            self.client.delete_collection(collection_name=name)
            logger.info(f"Deleted collection: {name}")
        except Exception as e:
            logger.error(f"Failed to delete collection '{name}': {str(e)}")
            raise
    
    async def list_collections(self) -> List[str]:
        """List all collections in Qdrant"""
        self._ensure_connected()
        try:
            collections = self.client.get_collections().collections
            return [collection.name for collection in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {str(e)}")
            raise
    
    async def add_documents(
        self, 
        collection_name: str, 
        documents: List[Document]
    ) -> List[str]:
        """Add documents to a Qdrant collection"""
        self._ensure_connected()
        try:
            # Prepare points for Qdrant
            points = []
            ids = []
            
            for doc in documents:
                # Generate UUID if not provided
                point_id = doc.id if doc.id else str(uuid.uuid4())
                ids.append(point_id)
                
                # Create point with metadata
                point = models.PointStruct(
                    id=point_id,
                    vector=self._get_document_vector(doc),  # This would need embedding
                    payload={
                        "content": doc.content,
                        "metadata": doc.metadata
                    }
                )
                points.append(point)
            
            # Add points to collection
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"Added {len(documents)} documents to collection '{collection_name}'")
            return ids
        except Exception as e:
            logger.error(f"Failed to add documents to collection '{collection_name}': {str(e)}")
            raise
    
    async def search(
        self,
        collection_name: str,
        query: str,
        limit: int = 10,
        **kwargs
    ) -> List[SearchResult]:
        """Search for documents in a Qdrant collection"""
        self._ensure_connected()
        try:
            # Convert query to vector (this would need embedding)
            query_vector = self._get_query_vector(query)
            
            # Search the collection
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                **kwargs
            )
            
            # Convert Qdrant results to SearchResult objects
            search_results = []
            for hit in search_result:
                document = Document(
                    id=str(hit.id),
                    content=hit.payload.get("content", ""),
                    metadata=hit.payload.get("metadata", {})
                )
                search_result = SearchResult(
                    document=document,
                    score=hit.score,
                    metadata={}
                )
                search_results.append(search_result)
            
            logger.info(f"Found {len(search_results)} results for query in collection '{collection_name}'")
            return search_results
        except Exception as e:
            logger.error(f"Failed to search collection '{collection_name}': {str(e)}")
            raise
    
    async def similarity_search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        **kwargs
    ) -> List[SearchResult]:
        """Search for similar documents using vector similarity in Qdrant"""
        self._ensure_connected()
        try:
            # Search the collection with vector
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                **kwargs
            )
            
            # Convert Qdrant results to SearchResult objects
            search_results = []
            for hit in search_result:
                document = Document(
                    id=str(hit.id),
                    content=hit.payload.get("content", ""),
                    metadata=hit.payload.get("metadata", {})
                )
                search_result = SearchResult(
                    document=document,
                    score=hit.score,
                    metadata={}
                )
                search_results.append(search_result)
            
            logger.info(f"Found {len(search_results)} similar results in collection '{collection_name}'")
            return search_results
        except Exception as e:
            logger.error(f"Failed to perform similarity search in collection '{collection_name}': {str(e)}")
            raise
    
    async def get_document(
        self,
        collection_name: str,
        document_id: str
    ) -> Optional[Document]:
        """Get a specific document by ID from Qdrant"""
        self._ensure_connected()
        try:
            # Get the document
            points = self.client.retrieve(
                collection_name=collection_name,
                ids=[document_id]
            )
            
            if points:
                point = points[0]
                document = Document(
                    id=str(point.id),
                    content=point.payload.get("content", ""),
                    metadata=point.payload.get("metadata", {})
                )
                return document
            
            return None
        except Exception as e:
            logger.error(f"Failed to get document '{document_id}' from collection '{collection_name}': {str(e)}")
            raise
    
    async def update_document(
        self,
        collection_name: str,
        document_id: str,
        document: Document
    ) -> bool:
        """Update a document in the Qdrant collection"""
        self._ensure_connected()
        try:
            # Update the document payload
            self.client.set_payload(
                collection_name=collection_name,
                payload={
                    "content": document.content,
                    "metadata": document.metadata
                },
                points=[document_id]
            )
            
            logger.info(f"Updated document '{document_id}' in collection '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to update document '{document_id}' in collection '{collection_name}': {str(e)}")
            return False
    
    async def delete_document(
        self,
        collection_name: str,
        document_id: str
    ) -> bool:
        """Delete a document from the Qdrant collection"""
        self._ensure_connected()
        try:
            # Delete the document
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(points=[document_id])
            )
            
            logger.info(f"Deleted document '{document_id}' from collection '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document '{document_id}' from collection '{collection_name}': {str(e)}")
            return False
    
    async def count_documents(self, collection_name: str) -> int:
        """Count the number of documents in a Qdrant collection"""
        self._ensure_connected()
        try:
            count = self.client.count(collection_name=collection_name).count
            logger.info(f"Collection '{collection_name}' contains {count} documents")
            return count
        except Exception as e:
            logger.error(f"Failed to count documents in collection '{collection_name}': {str(e)}")
            raise
    
    def _get_document_vector(self, document: Document) -> List[float]:
        """
        Get vector representation of a document.
        
        This is a placeholder that would need to be implemented with actual
        embedding logic (e.g., using OpenAI embeddings or another embedding service).
        """
        # TODO: Implement actual embedding logic
        # For now, return a dummy vector of the right size
        return [0.0] * 1536  # Default size for OpenAI embeddings
    
    def _get_query_vector(self, query: str) -> List[float]:
        """
        Get vector representation of a query.
        
        This is a placeholder that would need to be implemented with actual
        embedding logic (e.g., using OpenAI embeddings or another embedding service).
        """
        # TODO: Implement actual embedding logic
        # For now, return a dummy vector of the right size
        return [0.0] * 1536  # Default size for OpenAI embeddings