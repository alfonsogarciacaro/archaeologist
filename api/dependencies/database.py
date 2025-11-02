"""
Database dependencies for FastAPI.

This module provides dependency injection for the database instance
and related utilities.
"""

from typing import AsyncGenerator
from fastapi import Depends

from db import DatabaseAbc, create_database
from app.config import get_settings


# Global database instance
_db_instance: DatabaseAbc = None


async def get_database() -> AsyncGenerator[DatabaseAbc, None]:
    """Get database instance as a FastAPI dependency."""
    global _db_instance
    
    if _db_instance is None:
        settings = get_settings()
        _db_instance = create_database(
            db_type="sqlite",
            db_path=settings.database_url.replace("sqlite:///", "")
        )
        await _db_instance.initialize()
    
    try:
        yield _db_instance
    except Exception:
        # Database error handling if needed
        pass


async def close_database() -> None:
    """Close database connection - called on application shutdown."""
    global _db_instance
    if _db_instance:
        await _db_instance.close()
        _db_instance = None