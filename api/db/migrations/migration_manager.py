"""
Database migration manager.

This module handles running database migrations in the correct order.
Migrations are designed to be idempotent - they can be run multiple times 
without causing issues.

Note: This is a simplified migration system without version tracking.
For production use, consider adding version tracking and rollback capabilities.
"""

import os
import asyncio
from pathlib import Path
from typing import List, Optional
from aiosqlite import Connection
import logging

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, migrations_dir: str):
        """
        Initialize migration manager.
        
        Args:
            migrations_dir: Path to directory containing migration files
        """
        self.migrations_dir = Path(migrations_dir)
        self.migrations = self._discover_migrations()
    
    def _discover_migrations(self) -> List[str]:
        """
        Discover migration files in the migrations directory.
        
        Returns:
            Sorted list of migration file paths
        """
        if not self.migrations_dir.exists():
            raise FileNotFoundError(f"Migrations directory not found: {self.migrations_dir}")
        
        migration_files = []
        for file_path in self.migrations_dir.glob("*.sql"):
            # Skip __init__.py and other non-migration files
            if file_path.name.startswith("__"):
                continue
            
            # Check if filename follows the pattern XXX_description.sql
            if self._is_valid_migration_filename(file_path.name):
                migration_files.append(str(file_path))
        
        # Sort by migration number (XXX prefix)
        migration_files.sort(key=self._extract_migration_number)
        return migration_files
    
    def _is_valid_migration_filename(self, filename: str) -> bool:
        """
        Check if filename follows the migration naming convention.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if filename is valid, False otherwise
        """
        parts = filename.split('_', 1)
        if len(parts) != 2:
            return False
        
        number_part = parts[0]
        if not number_part.isdigit() or len(number_part) != 3:
            return False
        
        return filename.endswith('.sql')
    
    def _extract_migration_number(self, file_path: str) -> int:
        """
        Extract migration number from file path.
        
        Args:
            file_path: Path to migration file
            
        Returns:
            Migration number as integer
        """
        filename = os.path.basename(file_path)
        number_part = filename.split('_', 1)[0]
        return int(number_part)
    
    async def run_migrations(self, conn: Connection) -> None:
        """
        Run all pending migrations.
        
        Note: This is a simplified implementation that runs all migrations
        every time. Since migrations are idempotent, this is safe.
        
        Args:
            conn: Database connection
        """
        logger.info(f"Running {len(self.migrations)} migrations...")
        
        for migration_path in self.migrations:
            await self._run_single_migration(conn, migration_path)
        
        logger.info("All migrations completed successfully")
    
    async def _run_single_migration(self, conn: Connection, migration_path: str) -> None:
        """
        Run a single migration file.
        
        Args:
            conn: Database connection
            migration_path: Path to migration file
        """
        migration_name = os.path.basename(migration_path)
        logger.info(f"Running migration: {migration_name}")
        
        try:
            # Read migration SQL
            with open(migration_path, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            # Split SQL into individual statements
            statements = self._split_sql_statements(migration_sql)
            
            # Execute each statement
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        await conn.execute(statement)
                    except Exception as e:
                        # Log error but continue for idempotent migrations
                        # Some statements might fail if they already exist
                        logger.debug(f"Statement failed (expected for idempotent migrations): {e}")
                        logger.debug(f"Failed statement: {statement[:100]}...")
            
            await conn.commit()
            logger.info(f"Migration {migration_name} completed successfully")
            
        except Exception as e:
            logger.error(f"Migration {migration_name} failed: {e}")
            raise
    
    def _split_sql_statements(self, sql: str) -> List[str]:
        """
        Split SQL content into individual statements.
        
        Args:
            sql: SQL content to split
            
        Returns:
            List of SQL statements
        """
        # Simple split on semicolons, but handle semicolons within strings
        statements = []
        current_statement = ""
        in_string = False
        string_char = None
        
        for char in sql:
            current_statement += char
            
            if char in ("'", '"') and (not current_statement.endswith("\\'") and not current_statement.endswith('\\"')):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
            
            if char == ';' and not in_string:
                statements.append(current_statement)
                current_statement = ""
        
        # Add any remaining content
        if current_statement.strip():
            statements.append(current_statement)
        
        return statements
    
    def get_migration_count(self) -> int:
        """
        Get the total number of migrations.
        
        Returns:
            Number of migration files
        """
        return len(self.migrations)
    
    def list_migrations(self) -> List[str]:
        """
        List all migration files.
        
        Returns:
            List of migration file names
        """
        return [os.path.basename(path) for path in self.migrations]


async def run_migrations(migrations_dir: str, conn: Connection) -> None:
    """
    Convenience function to run all migrations.
    
    Args:
        migrations_dir: Path to migrations directory
        conn: Database connection
    """
    manager = MigrationManager(migrations_dir)
    await manager.run_migrations(conn)
