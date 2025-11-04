"""
Vector Database Interface Abstraction

This module provides an abstract interface for vector database operations,
allowing for easy switching between different vector database implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel


class Document(BaseModel):
    """Represents a document to be stored in the vector database"""
    id: str
    content: str
    metadata: Dict[str, Any] = {}


class SearchResult(BaseModel):
    """Represents a search result from the vector database"""
    document: Document
    score: float
    metadata: Dict[str, Any] = {}


class VectorDatabaseInterface(ABC):
    """
    Abstract interface for vector database operations.
    
    This interface defines the contract that all vector database implementations
    must follow, ensuring consistency and making it easy to swap implementations.
    """
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the vector database"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the vector database"""
        pass
    
    @abstractmethod
    async def create_collection(self, name: str, **kwargs) -> None:
        """Create a new collection in the vector database"""
        pass
    
    @abstractmethod
    async def delete_collection(self, name: str) -> None:
        """Delete a collection from the vector database"""
        pass
    
    @abstractmethod
    async def list_collections(self) -> List[str]:
        """List all collections in the vector database"""
        pass
    
    @abstractmethod
    async def add_documents(
        self, 
        collection_name: str, 
        documents: List[Document]
    ) -> List[str]:
        """
        Add documents to a collection
        
        Args:
            collection_name: Name of the collection
            documents: List of documents to add
            
        Returns:
            List of document IDs that were added
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query: str,
        limit: int = 10,
        **kwargs
    ) -> List[SearchResult]:
        """
        Search for documents in a collection
        
        Args:
            collection_name: Name of the collection
            query: Search query
            limit: Maximum number of results to return
            **kwargs: Additional search parameters
            
        Returns:
            List of search results
        """
        pass
    
    @abstractmethod
    async def similarity_search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        **kwargs
    ) -> List[SearchResult]:
        """
        Search for similar documents using vector similarity
        
        Args:
            collection_name: Name of the collection
            query_vector: Query vector for similarity search
            limit: Maximum number of results to return
            **kwargs: Additional search parameters
            
        Returns:
            List of search results
        """
        pass
    
    @abstractmethod
    async def get_document(
        self,
        collection_name: str,
        document_id: str
    ) -> Optional[Document]:
        """
        Get a specific document by ID
        
        Args:
            collection_name: Name of the collection
            document_id: ID of the document to retrieve
            
        Returns:
            The document if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update_document(
        self,
        collection_name: str,
        document_id: str,
        document: Document
    ) -> bool:
        """
        Update a document in the collection
        
        Args:
            collection_name: Name of the collection
            document_id: ID of the document to update
            document: Updated document
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_document(
        self,
        collection_name: str,
        document_id: str
    ) -> bool:
        """
        Delete a document from the collection
        
        Args:
            collection_name: Name of the collection
            document_id: ID of the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def count_documents(self, collection_name: str) -> int:
        """
        Count the number of documents in a collection
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Number of documents in the collection
        """
        pass