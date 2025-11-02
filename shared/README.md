# Data Lake Module

A flexible, async data lake implementation for storing and managing enterprise code artifacts and documentation.

## Overview

The data lake module provides a clean interface for storing, retrieving, and managing various types of enterprise data artifacts. It includes both an abstract interface and a disk-based implementation, making it easy to extend to other storage backends in the future (S3, databases, etc.).

## Features

- **Async/Await Support**: Fully async implementation for high performance
- **Multiple Data Types**: Support for schemas, macros, configurations, documentation, logs, and more
- **Metadata Management**: Store rich metadata alongside content
- **Search Functionality**: Full-text search across content and metadata
- **Version Control**: Track creation and update timestamps
- **Flexible Storage**: Disk-based implementation with easy extension to other backends
- **Type Safety**: Full type hints and data validation
- **Error Handling**: Comprehensive error types for different failure scenarios

## Installation

The data lake module is part of the shared package. Install dependencies:

```bash
pip install aiofiles pytest pytest-asyncio
```

## Quick Start

```python
import asyncio
from shared import DiskDataLake, DataType

async def main():
    # Create a data lake instance
    data_lake = DiskDataLake("/path/to/data/lake")
    
    # Store a database schema
    entry = await data_lake.store(
        name="user_schema.sql",
        content="CREATE TABLE users (id INT, name VARCHAR(100));",
        data_type=DataType.SCHEMA,
        metadata={"version": "1.0", "database": "production"}
    )
    
    # Retrieve the entry
    retrieved = await data_lake.retrieve(entry.id)
    print(f"Retrieved: {retrieved.content}")
    
    # Search for content
    results = await data_lake.search("CREATE TABLE users")
    print(f"Found {len(results)} results")

asyncio.run(main())
```

## API Reference

### DataLakeInterface

The abstract interface that defines all data lake operations:

#### Core Methods

- `store(name, content, data_type, metadata, subpath)`: Store new data
- `retrieve(entry_id)`: Retrieve data by ID  
- `retrieve_by_path(path)`: Retrieve data by file path
- `list(data_type, subpath, recursive)`: List entries with filters
- `search(query, data_type, subpath)`: Search for entries
- `delete(entry_id)`: Delete an entry
- `update(entry_id, content, metadata)`: Update existing entry
- `get_stats()`: Get data lake statistics

### Data Types

```python
class DataType(Enum):
    SCHEMA = "schema"
    MACRO = "macro" 
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    LOGS = "logs"
    OTHER = "other"
```

### DataLakeEntry

Represents a single data lake entry:

```python
@dataclass
class DataLakeEntry:
    id: str
    name: str
    data_type: DataType
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None
    file_path: Optional[str] = None
```

## Usage Examples

### Storing Different Data Types

```python
# Database schema
schema_entry = await data_lake.store(
    name="schema.sql",
    content="CREATE TABLE users (id INT, name VARCHAR);",
    data_type=DataType.SCHEMA,
    metadata={"version": "2.1"}
)

# Excel macro with subpath
macro_entry = await data_lake.store(
    name="macro.vba",
    content="Sub ProcessData()\\n    ' Process data\\nEnd Sub",
    data_type=DataType.MACRO,
    subpath="finance/2023-10-27",
    metadata={"author": "finance_team"}
)

# Configuration
config_entry = await data_lake.store(
    name="config.json",
    content='{"service": "api", "version": "1.2.3"}',
    data_type=DataType.CONFIGURATION
)
```

### Search and Discovery

```python
# Search by content
user_schemas = await data_lake.search("CREATE TABLE users")

# Search by data type
all_macros = await data_lake.list(data_type=DataType.MACRO)

# Search within subpath
finance_macros = await data_lake.search("term", subpath="finance")
```

### Updates and Deletions

```python
# Update content and metadata
updated = await data_lake.update(
    entry.id,
    content="-- New version\\nCREATE TABLE new_table ();",
    metadata={"version": "2.0", "updated_by": "admin"}
)

# Delete entry
success = await data_lake.delete(entry.id)
```

### Statistics and Monitoring

```python
stats = await data_lake.get_stats()
print(f"Total entries: {stats['total_entries']}")
print(f"Total size: {stats['total_size_mb']} MB")
print(f"By type: {stats['entries_by_type']}")
```

## Error Handling

The module provides specific exception types:

```python
from shared import DataLakeError, NotFoundError, ValidationError

try:
    entry = await data_lake.retrieve("non-existent-id")
except NotFoundError:
    print("Entry not found")
except ValidationError as e:
    print(f"Invalid input: {e}")
except DataLakeError as e:
    print(f"Data lake error: {e}")
```

## Storage Structure

The disk implementation uses the following structure:

```
data_lake/
├── .metadata/           # Metadata files (JSON)
│   ├── entry1.json
│   └── entry2.json
├── schema/              # Database schemas
│   └── user_schema.sql
├── macro/               # Excel/VBA macros
│   └── finance/
│       └── 2023-10-27/
│           └── macro.vba
├── configuration/       # Config files
└── documentation/       # Documentation
```

## Testing

Run the comprehensive test suite:

```bash
python -m pytest shared/tests/test_data_lake.py -v
```

The tests cover:
- Basic CRUD operations
- Search functionality
- Validation and error handling
- Persistence across instances
- Statistics and metadata

## Extending the Module

To implement a different storage backend, extend the `DataLakeInterface`:

```python
class S3DataLake(DataLakeInterface):
    async def store(self, name, content, data_type, metadata, subpath):
        # S3 implementation
        pass
    
    async def retrieve(self, entry_id):
        # S3 retrieval
        pass
    
    # Implement other methods...
```

## Performance Considerations

- **Async Operations**: All I/O operations are async for non-blocking performance
- **Efficient Search**: Search operations work on metadata indices for speed
- **Caching**: Consider implementing caching for frequently accessed entries
- **Batch Operations**: For large-scale operations, consider batch implementations

## Future Enhancements

Planned improvements include:
- S3/Cloud storage implementations
- Full-text search with indexing (Elasticsearch/Whoosh)
- Access control and permissions
- Compression for large files
- Streaming for very large content
- Data retention policies
- Backup and restore functionality

## Integration with Enterprise Archaeologist

This data lake module is designed to work seamlessly with the Enterprise Code Archaeologist system, providing storage for:

- Database schemas discovered during code analysis
- Excel macros and financial models
- Configuration files from various services
- Documentation and knowledge base articles
- Historical code snapshots
- Analysis results and reports

The async nature makes it perfect for integration with FastAPI services and other async components in the system.