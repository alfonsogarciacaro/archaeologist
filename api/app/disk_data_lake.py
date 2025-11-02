import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiofiles
import aiofiles.os

from .data_lake_interface import (
    DataLakeInterface,
    DataLakeEntry,
    DataType,
    DataLakeError,
    NotFoundError,
    ValidationError
)


class DiskDataLake(DataLakeInterface):
    """
    Disk-based implementation of the DataLakeInterface.
    
    Stores data as files in a directory structure with accompanying
    metadata files for efficient querying and management.
    """
    
    def __init__(self, base_path: str):
        """
        Initialize the disk data lake.
        
        Args:
            base_path: Base directory path for the data lake storage
        """
        self.base_path = Path(base_path)
        self.metadata_dir = self.base_path / ".metadata"
        self.data_type_dirs = {
            data_type: self.base_path / data_type.value 
            for data_type in DataType
        }
        
    async def _ensure_directories(self):
        """Ensure all necessary directories exist."""
        directories = [self.base_path, self.metadata_dir] + list(self.data_type_dirs.values())
        for directory in directories:
            try:
                await aiofiles.os.makedirs(directory, exist_ok=True)
            except OSError as e:
                raise DataLakeError(f"Failed to create directory {directory}: {e}")
    
    def _generate_id(self) -> str:
        """Generate a unique ID for a data lake entry."""
        return str(uuid.uuid4())
    
    def _get_file_path(self, data_type: DataType, subpath: Optional[str], name: str) -> Path:
        """Get the file path for a data entry."""
        base_dir = self.data_type_dirs[data_type]
        if subpath:
            base_dir = base_dir / subpath
        return base_dir / name
    
    def _get_metadata_path(self, entry_id: str) -> Path:
        """Get the metadata file path for an entry."""
        return self.metadata_dir / f"{entry_id}.json"
    
    async def _validate_inputs(
        self, 
        name: str, 
        content: str, 
        data_type: DataType, 
        subpath: Optional[str]
    ):
        """Validate input parameters."""
        if not name or not name.strip():
            raise ValidationError("Name cannot be empty")
        if content is None:
            raise ValidationError("Content cannot be None")
        if not isinstance(data_type, DataType):
            raise ValidationError("data_type must be a DataType enum value")
        if subpath:
            # Validate subpath doesn't contain directory traversal
            if ".." in subpath or subpath.startswith("/"):
                raise ValidationError("Invalid subpath: directory traversal not allowed")
    
    async def store(
        self,
        name: str,
        content: str,
        data_type: DataType,
        metadata: Optional[Dict[str, Any]] = None,
        subpath: Optional[str] = None
    ) -> DataLakeEntry:
        """Store data in the data lake."""
        await self._ensure_directories()
        await self._validate_inputs(name, content, data_type, subpath)
        
        entry_id = self._generate_id()
        file_path = self._get_file_path(data_type, subpath, name)
        metadata_path = self._get_metadata_path(entry_id)
        
        # Ensure subdirectories exist
        file_dir = file_path.parent
        try:
            await aiofiles.os.makedirs(file_dir, exist_ok=True)
        except OSError as e:
            raise DataLakeError(f"Failed to create subdirectory {file_dir}: {e}")
        
        # Write the content file
        try:
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
        except OSError as e:
            raise DataLakeError(f"Failed to write content file {file_path}: {e}")
        
        # Create metadata
        entry_metadata = metadata or {}
        entry_metadata.update({
            "original_name": name,
            "data_type": data_type.value,
            "subpath": subpath,
            "file_size": len(content.encode('utf-8'))
        })
        
        # Create data lake entry
        entry = DataLakeEntry(
            id=entry_id,
            name=name,
            data_type=data_type,
            content=content,
            metadata=entry_metadata,
            created_at=datetime.now(),
            file_path=str(file_path.relative_to(self.base_path))
        )
        
        # Write metadata file
        try:
            metadata_dict = {
                "id": entry.id,
                "name": entry.name,
                "data_type": entry.data_type.value,
                "metadata": entry.metadata,
                "created_at": entry.created_at.isoformat(),
                "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
                "file_path": entry.file_path
            }
            async with aiofiles.open(metadata_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(metadata_dict, indent=2))
        except OSError as e:
            # If metadata write fails, try to clean up the content file
            try:
                await aiofiles.os.remove(file_path)
            except OSError:
                pass
            raise DataLakeError(f"Failed to write metadata file {metadata_path}: {e}")
        
        return entry
    
    async def _load_metadata(self, entry_id: str) -> Dict[str, Any]:
        """Load metadata for an entry."""
        metadata_path = self._get_metadata_path(entry_id)
        try:
            async with aiofiles.open(metadata_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
        except FileNotFoundError:
            raise NotFoundError(f"Entry with ID {entry_id} not found")
        except (OSError, json.JSONDecodeError) as e:
            raise DataLakeError(f"Failed to load metadata for {entry_id}: {e}")
    
    async def retrieve(self, entry_id: str) -> DataLakeEntry:
        """Retrieve data from the data lake by ID."""
        metadata_dict = await self._load_metadata(entry_id)
        
        # Load content from file
        file_path = self.base_path / metadata_dict["file_path"]
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
        except FileNotFoundError:
            raise NotFoundError(f"Content file not found for entry {entry_id}")
        except OSError as e:
            raise DataLakeError(f"Failed to read content file {file_path}: {e}")
        
        # Reconstruct entry
        return DataLakeEntry(
            id=metadata_dict["id"],
            name=metadata_dict["name"],
            data_type=DataType(metadata_dict["data_type"]),
            content=content,
            metadata=metadata_dict["metadata"],
            created_at=datetime.fromisoformat(metadata_dict["created_at"]),
            updated_at=datetime.fromisoformat(metadata_dict["updated_at"]) if metadata_dict["updated_at"] else None,
            file_path=metadata_dict["file_path"]
        )
    
    async def retrieve_by_path(self, path: str) -> DataLakeEntry:
        """Retrieve data from the data lake by file path."""
        # Find the metadata file corresponding to this path
        async for metadata_file in self._list_metadata_files():
            metadata_dict = await self._load_single_metadata(metadata_file)
            if metadata_dict and metadata_dict.get("file_path") == path:
                return await self.retrieve(metadata_dict["id"])
        
        raise NotFoundError(f"No entry found with path: {path}")
    
    async def _list_metadata_files(self):
        """List all metadata files."""
        try:
            for file_path in self.metadata_dir.glob("*.json"):
                yield file_path
        except OSError as e:
            raise DataLakeError(f"Failed to list metadata files: {e}")
    
    async def _load_single_metadata(self, metadata_path: Path) -> Optional[Dict[str, Any]]:
        """Load a single metadata file."""
        try:
            async with aiofiles.open(metadata_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
        except (OSError, json.JSONDecodeError):
            return None
    
    async def list(
        self,
        data_type: Optional[DataType] = None,
        subpath: Optional[str] = None,
        recursive: bool = True
    ) -> List[DataLakeEntry]:
        """List entries in the data lake."""
        entries = []
        
        async for metadata_file in self._list_metadata_files():
            metadata_dict = await self._load_single_metadata(metadata_file)
            if not metadata_dict:
                continue
            
            # Apply filters
            if data_type and metadata_dict["data_type"] != data_type.value:
                continue
            
            if subpath:
                file_path = metadata_dict.get("file_path", "")
                if not file_path.startswith(subpath):
                    continue
            
            # Create entry (without loading content for efficiency)
            entry = DataLakeEntry(
                id=metadata_dict["id"],
                name=metadata_dict["name"],
                data_type=DataType(metadata_dict["data_type"]),
                content="",  # Not loaded for list operation
                metadata=metadata_dict["metadata"],
                created_at=datetime.fromisoformat(metadata_dict["created_at"]),
                updated_at=datetime.fromisoformat(metadata_dict["updated_at"]) if metadata_dict["updated_at"] else None,
                file_path=metadata_dict["file_path"]
            )
            entries.append(entry)
        
        return entries
    
    async def search(
        self,
        query: str,
        data_type: Optional[DataType] = None,
        subpath: Optional[str] = None
    ) -> List[DataLakeEntry]:
        """Search for entries in the data lake."""
        # For now, implement simple text search in content and metadata
        # In a more sophisticated implementation, this could use full-text search
        query_lower = query.lower()
        matching_entries = []
        
        entries = await self.list(data_type, subpath, True)
        
        for entry in entries:
            # Load content for searching
            try:
                full_entry = await self.retrieve(entry.id)
                
                # Search in name, content, and metadata
                search_text = [
                    entry.name.lower(),
                    full_entry.content.lower(),
                    json.dumps(full_entry.metadata).lower()
                ]
                
                if any(query_lower in text for text in search_text):
                    matching_entries.append(full_entry)
            except DataLakeError:
                # Skip entries that can't be loaded
                continue
        
        return matching_entries
    
    async def delete(self, entry_id: str) -> bool:
        """Delete an entry from the data lake."""
        metadata_dict = await self._load_metadata(entry_id)
        file_path = self.base_path / metadata_dict["file_path"]
        metadata_path = self._get_metadata_path(entry_id)
        
        # Delete content file and metadata file
        content_deleted = True
        metadata_deleted = True
        
        try:
            await aiofiles.os.remove(file_path)
        except FileNotFoundError:
            content_deleted = False
        except OSError as e:
            raise DataLakeError(f"Failed to delete content file {file_path}: {e}")
        
        try:
            await aiofiles.os.remove(metadata_path)
        except FileNotFoundError:
            metadata_deleted = False
        except OSError as e:
            raise DataLakeError(f"Failed to delete metadata file {metadata_path}: {e}")
        
        return content_deleted or metadata_deleted
    
    async def update(
        self,
        entry_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DataLakeEntry:
        """Update an existing entry in the data lake."""
        # Load current entry
        current_entry = await self.retrieve(entry_id)
        
        # Update content if provided
        if content is not None:
            if not current_entry.file_path:
                raise DataLakeError(f"File path missing for entry {entry_id}")
            file_path = self.base_path / current_entry.file_path
            try:
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(content)
            except OSError as e:
                raise DataLakeError(f"Failed to update content file {file_path}: {e}")
            current_entry.content = content
        
        # Update metadata if provided
        if metadata is not None:
            current_entry.metadata.update(metadata)
        
        current_entry.updated_at = datetime.now()
        
        # Update metadata file
        metadata_dict = {
            "id": current_entry.id,
            "name": current_entry.name,
            "data_type": current_entry.data_type.value,
            "metadata": current_entry.metadata,
            "created_at": current_entry.created_at.isoformat(),
            "updated_at": current_entry.updated_at.isoformat(),
            "file_path": current_entry.file_path
        }
        
        metadata_path = self._get_metadata_path(entry_id)
        try:
            async with aiofiles.open(metadata_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(metadata_dict, indent=2))
        except OSError as e:
            raise DataLakeError(f"Failed to update metadata file {metadata_path}: {e}")
        
        return current_entry
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the data lake."""
        entries = await self.list()
        
        stats = {
            "total_entries": len(entries),
            "entries_by_type": {},
            "total_size_bytes": 0,
            "created_entries": 0,
            "updated_entries": 0
        }
        
        for entry in entries:
            # Count by type
            type_name = entry.data_type.value
            stats["entries_by_type"][type_name] = stats["entries_by_type"].get(type_name, 0) + 1
            
            # Count file sizes
            file_size = entry.metadata.get("file_size", 0)
            stats["total_size_bytes"] += file_size
            
            # Count created vs updated
            if entry.updated_at:
                stats["updated_entries"] += 1
            else:
                stats["created_entries"] += 1
        
        # Convert bytes to human readable
        stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)
        
        return stats