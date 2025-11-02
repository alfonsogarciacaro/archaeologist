"""
Database factory for creating database instances.

This module provides a factory pattern for creating database instances
based on configuration, making it easy to switch between implementations.
"""

from typing import Dict, Type
from .base import DatabaseAbc
from .sqlite import SQLiteDatabase


class DatabaseFactory:
    """Factory for creating database instances."""
    
    _databases: Dict[str, Type[DatabaseAbc]] = {
        "sqlite": SQLiteDatabase,
    }
    
    @classmethod
    def create_database(cls, db_type: str = "sqlite", **kwargs) -> DatabaseAbc:
        """Create a database instance based on type."""
        if db_type not in cls._databases:
            raise ValueError(f"Unsupported database type: {db_type}. "
                           f"Supported types: {list(cls._databases.keys())}")
        
        database_class = cls._databases[db_type]
        return database_class(**kwargs)
    
    @classmethod
    def register_database(cls, db_type: str, database_class: Type[DatabaseAbc]) -> None:
        """Register a new database type."""
        cls._databases[db_type] = database_class


# Convenience function for creating databases
def create_database(db_type: str = "sqlite", **kwargs) -> DatabaseAbc:
    """Create a database instance."""
    return DatabaseFactory.create_database(db_type, **kwargs)