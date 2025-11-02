from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class DataType(Enum):
    """Enum for different types of data that can be stored in the data lake."""
    SCHEMA = "schema"
    MACRO = "macro"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    LOGS = "logs"
    OTHER = "other"


@dataclass
class DataLakeEntry:
    """Represents a single entry in the data lake."""
    id: str
    name: str
    data_type: DataType
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None
    file_path: Optional[str] = None


class DataLakeInterface(ABC):
    """
    Abstract interface for data lake operations.
    
    This interface provides methods for storing, retrieving, and managing
    various types of enterprise data artifacts. Implementations can store
    data in different backends (disk, S3, database, etc.).
    """
    
    @abstractmethod
    async def store(
        self,
        name: str,
        content: str,
        data_type: DataType,
        metadata: Optional[Dict[str, Any]] = None,
        subpath: Optional[str] = None
    ) -> DataLakeEntry:
        """
        Store data in the data lake.
        
        Args:
            name: Name of the data item
            content: The content to store
            data_type: Type of data being stored
            metadata: Additional metadata about the data
            subpath: Optional subpath within the data lake
            
        Returns:
            DataLakeEntry representing the stored item
            
        Raises:
            DataLakeError: If storage operation fails
        """
        pass
    
    @abstractmethod
    async def retrieve(self, entry_id: str) -> DataLakeEntry:
        """
        Retrieve data from the data lake by ID.
        
        Args:
            entry_id: Unique identifier for the data item
            
        Returns:
            DataLakeEntry containing the requested data
            
        Raises:
            NotFoundError: If entry doesn't exist
            DataLakeError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def retrieve_by_path(self, path: str) -> DataLakeEntry:
        """
        Retrieve data from the data lake by file path.
        
        Args:
            path: File path within the data lake
            
        Returns:
            DataLakeEntry containing the requested data
            
        Raises:
            NotFoundError: If entry doesn't exist
            DataLakeError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def list(
        self,
        data_type: Optional[DataType] = None,
        subpath: Optional[str] = None,
        recursive: bool = True
    ) -> List[DataLakeEntry]:
        """
        List entries in the data lake.
        
        Args:
            data_type: Optional filter by data type
            subpath: Optional subpath to filter by
            recursive: Whether to search recursively in subdirectories
            
        Returns:
            List of DataLakeEntry objects matching the criteria
            
        Raises:
            DataLakeError: If listing operation fails
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        data_type: Optional[DataType] = None,
        subpath: Optional[str] = None
    ) -> List[DataLakeEntry]:
        """
        Search for entries in the data lake.
        
        Args:
            query: Search query string
            data_type: Optional filter by data type
            subpath: Optional subpath to search within
            
        Returns:
            List of DataLakeEntry objects matching the search criteria
            
        Raises:
            DataLakeError: If search operation fails
        """
        pass
    
    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        """
        Delete an entry from the data lake.
        
        Args:
            entry_id: Unique identifier for the data item
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            DataLakeError: If deletion operation fails
        """
        pass
    
    @abstractmethod
    async def update(
        self,
        entry_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DataLakeEntry:
        """
        Update an existing entry in the data lake.
        
        Args:
            entry_id: Unique identifier for the data item
            content: New content (if updating)
            metadata: New metadata (if updating)
            
        Returns:
            Updated DataLakeEntry
            
        Raises:
            NotFoundError: If entry doesn't exist
            DataLakeError: If update operation fails
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the data lake.
        
        Returns:
            Dictionary containing data lake statistics
            
        Raises:
            DataLakeError: If stats retrieval fails
        """
        pass


class DataLakeError(Exception):
    """Base exception for data lake operations."""
    pass


class NotFoundError(DataLakeError):
    """Exception raised when a requested entry is not found."""
    pass


class ValidationError(DataLakeError):
    """Exception raised when input validation fails."""
    pass