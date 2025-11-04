import asyncio
import os
import tempfile
from datetime import datetime
from pathlib import Path
import pytest
import pytest_asyncio

from app.disk_data_lake import DiskDataLake
from app.data_lake_interface import (
    DataLakeEntry,
    DataType,
    NotFoundError,
    ValidationError
)


class TestDiskDataLake:
    """Test suite for DiskDataLake implementation."""
    
    @pytest_asyncio.fixture
    async def temp_data_lake(self):
        """Create a temporary data lake for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_lake = DiskDataLake(temp_dir)
            yield data_lake
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, temp_data_lake):
        """Test basic store and retrieve operations."""
        entry = await temp_data_lake.store(
            name="test_schema.sql",
            content="CREATE TABLE test (id INT);",
            data_type=DataType.SCHEMA,
            metadata={"version": "1.0", "author": "test"}
        )
        
        assert entry.id is not None
        assert entry.name == "test_schema.sql"
        assert entry.data_type == DataType.SCHEMA
        assert entry.content == "CREATE TABLE test (id INT);"
        assert entry.metadata["version"] == "1.0"
        assert entry.created_at is not None
        assert entry.file_path == f"{DataType.SCHEMA.value}{os.sep}test_schema.sql"
        
        # Test retrieval
        retrieved = await temp_data_lake.retrieve(entry.id)
        assert retrieved.id == entry.id
        assert retrieved.name == entry.name
        assert retrieved.content == entry.content
        assert retrieved.data_type == entry.data_type
    
    @pytest.mark.asyncio
    async def test_store_with_subpath(self, temp_data_lake):
        """Test storing data with subpath."""
        entry = await temp_data_lake.store(
            name="macro.vba",
            content="Sub TestMacro()\\n    MsgBox 'Hello'\\nEnd Sub",
            data_type=DataType.MACRO,
            subpath="finance/2023-10-27"
        )
        
        assert entry.file_path == f"{DataType.MACRO.value}{os.sep}finance{os.sep}2023-10-27{os.sep}macro.vba"
        
        # Test retrieval by path
        retrieved_by_path = await temp_data_lake.retrieve_by_path(entry.file_path)
        assert retrieved_by_path.id == entry.id
        assert retrieved_by_path.content == entry.content
    
    @pytest.mark.asyncio
    async def test_list_operations(self, temp_data_lake):
        """Test listing operations."""
        # Store different types of data
        await temp_data_lake.store("schema1.sql", "CREATE TABLE a();", DataType.SCHEMA)
        await temp_data_lake.store("macro1.vba", "Sub Test()", DataType.MACRO)
        await temp_data_lake.store("schema2.sql", "CREATE TABLE b();", DataType.SCHEMA)
        
        # List all entries
        all_entries = await temp_data_lake.list()
        assert len(all_entries) == 3
        
        # List by type
        schema_entries = await temp_data_lake.list(data_type=DataType.SCHEMA)
        assert len(schema_entries) == 2
        assert all(entry.data_type == DataType.SCHEMA for entry in schema_entries)
        
        macro_entries = await temp_data_lake.list(data_type=DataType.MACRO)
        assert len(macro_entries) == 1
        assert macro_entries[0].data_type == DataType.MACRO
    
    @pytest.mark.asyncio
    async def test_search_operations(self, temp_data_lake):
        """Test search functionality."""
        await temp_data_lake.store(
            "user_schema.sql", 
            "CREATE TABLE users (id INT, name VARCHAR);", 
            DataType.SCHEMA,
            metadata={"description": "User table schema"}
        )
        await temp_data_lake.store(
            "user_macro.vba",
            "Sub ProcessUsers()\\n    ' Process user data\\nEnd Sub",
            DataType.MACRO
        )
        
        # Search for "user"
        user_results = await temp_data_lake.search("user")
        assert len(user_results) == 2
        
        # Search for "CREATE TABLE"
        table_results = await temp_data_lake.search("CREATE TABLE")
        assert len(table_results) == 1
        assert "users" in table_results[0].content
        
        # Search by data type
        macro_results = await temp_data_lake.search("user", data_type=DataType.MACRO)
        assert len(macro_results) == 1
        assert macro_results[0].data_type == DataType.MACRO
    
    @pytest.mark.asyncio
    async def test_update_operations(self, temp_data_lake):
        """Test update functionality."""
        entry = await temp_data_lake.store(
            "test.sql",
            "SELECT * FROM old_table;",
            DataType.SCHEMA,
            metadata={"version": "1.0"}
        )
        
        # Update content
        updated_entry = await temp_data_lake.update(
            entry.id,
            content="SELECT * FROM new_table;",
            metadata={"version": "2.0"}
        )
        
        assert updated_entry.content == "SELECT * FROM new_table;"
        assert updated_entry.metadata["version"] == "2.0"
        assert updated_entry.updated_at is not None
        assert updated_entry.updated_at > updated_entry.created_at
        
        # Verify persistence
        retrieved = await temp_data_lake.retrieve(entry.id)
        assert retrieved.content == "SELECT * FROM new_table;"
        assert retrieved.metadata["version"] == "2.0"
    
    @pytest.mark.asyncio
    async def test_delete_operations(self, temp_data_lake):
        """Test delete functionality."""
        entry = await temp_data_lake.store(
            "to_delete.sql",
            "DROP TABLE test;",
            DataType.SCHEMA
        )
        
        # Verify entry exists
        await temp_data_lake.retrieve(entry.id)
        
        # Delete entry
        delete_result = await temp_data_lake.delete(entry.id)
        assert delete_result is True
        
        # Verify entry is gone
        with pytest.raises(NotFoundError):
            await temp_data_lake.retrieve(entry.id)
    
    @pytest.mark.asyncio
    async def test_get_stats(self, temp_data_lake):
        """Test statistics functionality."""
        # Add some test data
        await temp_data_lake.store("schema1.sql", "CREATE TABLE a();", DataType.SCHEMA)
        await temp_data_lake.store("macro1.vba", "Sub Test()", DataType.MACRO)
        await temp_data_lake.store("schema2.sql", "CREATE TABLE b();", DataType.SCHEMA)
        
        stats = await temp_data_lake.get_stats()
        
        assert stats["total_entries"] == 3
        assert stats["entries_by_type"][DataType.SCHEMA.value] == 2
        assert stats["entries_by_type"][DataType.MACRO.value] == 1
        assert stats["total_size_bytes"] > 0
        assert stats["total_size_mb"] >= 0  # Can be 0.0 for very small files
        assert stats["created_entries"] == 3  # All entries are newly created
    
    @pytest.mark.asyncio
    async def test_validation_errors(self, temp_data_lake):
        """Test input validation."""
        # Test empty name
        with pytest.raises(ValidationError):
            await temp_data_lake.store("", "content", DataType.SCHEMA)
        
        # Test None content
        with pytest.raises(ValidationError):
            await temp_data_lake.store("test.sql", None, DataType.SCHEMA)
        
        # Test directory traversal in subpath
        with pytest.raises(ValidationError):
            await temp_data_lake.store("test.sql", "content", DataType.SCHEMA, subpath="../dangerous")
    
    @pytest.mark.asyncio
    async def test_not_found_errors(self, temp_data_lake):
        """Test not found errors."""
        # Test retrieve non-existent entry
        with pytest.raises(NotFoundError):
            await temp_data_lake.retrieve("non-existent-id")
        
        # Test retrieve by non-existent path
        with pytest.raises(NotFoundError):
            await temp_data_lake.retrieve_by_path("non/existent/path.sql")
        
        # Test update non-existent entry
        with pytest.raises(NotFoundError):
            await temp_data_lake.update("non-existent-id", content="new content")
    
    @pytest.mark.asyncio
    async def test_persistence_across_instances(self, temp_data_lake):
        """Test that data persists across data lake instances."""
        # Store data in first instance
        entry = await temp_data_lake.store(
            "persistent.sql",
            "SELECT * FROM persistent_table;",
            DataType.SCHEMA
        )
        
        # Create new instance with same base path
        new_data_lake = DiskDataLake(temp_data_lake.base_path)
        
        # Verify data is accessible in new instance
        retrieved = await new_data_lake.retrieve(entry.id)
        assert retrieved.id == entry.id
        assert retrieved.content == entry.content
        
        # Verify listing works in new instance
        entries = await new_data_lake.list()
        assert len(entries) == 1
        assert entries[0].id == entry.id


if __name__ == "__main__":
    # Run a quick manual test
    async def manual_test():
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            data_lake = DiskDataLake(temp_dir)
            
            # Store some test data
            entry = await data_lake.store(
                name="test_schema.sql",
                content="CREATE TABLE test (id INT, name VARCHAR(100));",
                data_type=DataType.SCHEMA,
                metadata={"version": "1.0", "database": "test_db"}
            )
            
            print(f"Stored entry: {entry.id}")
            print(f"Name: {entry.name}")
            print(f"Type: {entry.data_type.value}")
            print(f"Path: {entry.file_path}")
            
            # Retrieve and verify
            retrieved = await data_lake.retrieve(entry.id)
            print(f"Retrieved content: {retrieved.content}")
            
            # Get stats
            stats = await data_lake.get_stats()
            print(f"Stats: {stats}")
    
    asyncio.run(manual_test())