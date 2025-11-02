"""
SQLite implementation of the database abstraction layer.

This module provides a lightweight SQLite implementation suitable for
development and small-scale deployments.
"""

import sqlite3
import json
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import asyncio
from aiosqlite import connect, Connection

from .base import DatabaseAbc
from api.models.database import (
    User, 
    Investigation, 
    KnowledgeGap, 
    SystemConfig,
    InvestigationSession,
    InvestigationStatus,
    KnowledgeGapType,
    UserStats,
    SystemStats
)


class SQLiteDatabase(DatabaseAbc):
    """SQLite implementation of the database interface."""
    
    def __init__(self, db_path: str = "archaeologist.db"):
        self.db_path = db_path
        self._conn: Optional[Connection] = None
    
    async def initialize(self) -> None:
        """Initialize SQLite database and create tables."""
        self._conn = await connect(self.db_path)
        
        # Enable foreign key constraints
        await self._conn.execute("PRAGMA foreign_keys = ON")
        
        # Create tables
        await self._create_tables()
        
        # Insert default configuration
        await self._insert_default_config()
    
    async def close(self) -> None:
        """Close database connection."""
        if self._conn:
            await self._conn.close()
    
    async def _create_tables(self) -> None:
        """Create all necessary database tables."""
        
        # Users table
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        
        # Investigations table
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS investigations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                impact_data TEXT,
                component_count INTEGER,
                knowledge_gap_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                execution_time_ms INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # Knowledge gaps table
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_gaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                investigation_id INTEGER NOT NULL,
                component_name TEXT NOT NULL,
                gap_type TEXT NOT NULL,
                description TEXT NOT NULL,
                suggested_action TEXT NOT NULL,
                confidence_score REAL,
                is_resolved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (investigation_id) REFERENCES investigations (id) ON DELETE CASCADE
            )
        """)
        
        # System config table
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                is_sensitive BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sessions table
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for performance
        await self._conn.execute("CREATE INDEX IF NOT EXISTS idx_investigations_user_id ON investigations (user_id)")
        await self._conn.execute("CREATE INDEX IF NOT EXISTS idx_investigations_status ON investigations (status)")
        await self._conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_gaps_investigation_id ON knowledge_gaps (investigation_id)")
        await self._conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions (session_token)")
        await self._conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id)")
        
        await self._conn.commit()
    
    async def _insert_default_config(self) -> None:
        """Insert default system configuration."""
        default_configs = [
            ("max_investigation_time_seconds", "300", "Maximum time for investigation execution", False),
            ("max_components_per_investigation", "100", "Maximum components to analyze", False),
            ("knowledge_gap_confidence_threshold", "0.7", "Minimum confidence for knowledge gaps", False),
            ("session_timeout_hours", "24", "Session timeout in hours", False),
            ("enable_anonymous_investigations", "false", "Allow investigations without authentication", False),
        ]
        
        for key, value, description, is_sensitive in default_configs:
            await self.set_config_value(key, value)
    
    # User management
    async def create_user(self, username: str, email: str, hashed_password: str) -> User:
        """Create a new user."""
        cursor = await self._conn.execute(
            "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
            (username, email, hashed_password)
        )
        await self._conn.commit()
        
        user_id = cursor.lastrowid
        return await self.get_user_by_id(user_id)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        cursor = await self._conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
        row = await cursor.fetchone()
        return User(**row) if row else None
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        cursor = await self._conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return User(**row) if row else None
    
    # Investigation management
    async def create_investigation(
        self, 
        user_id: int, 
        query: str, 
        impact_data: Dict[str, Any]
    ) -> Investigation:
        """Create a new investigation record."""
        impact_json = json.dumps(impact_data) if impact_data else None
        component_count = len(impact_data.get('components', [])) if impact_data else 0
        
        cursor = await self._conn.execute(
            """INSERT INTO investigations 
               (user_id, query, impact_data, component_count, status, started_at) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, query, impact_json, component_count, InvestigationStatus.RUNNING, datetime.utcnow())
        )
        await self._conn.commit()
        
        investigation_id = cursor.lastrowid
        return await self.get_investigation_by_id(investigation_id)
    
    async def get_investigation_by_id(self, investigation_id: int) -> Optional[Investigation]:
        """Get investigation by ID."""
        cursor = await self._conn.execute(
            "SELECT * FROM investigations WHERE id = ?",
            (investigation_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            return None
            
        # Convert to dict and handle JSON fields
        data = dict(row)
        if data['impact_data']:
            data['impact_data'] = json.loads(data['impact_data'])
        
        return Investigation(**data)
    
    async def get_user_investigations(self, user_id: int, limit: int = 10) -> List[Investigation]:
        """Get user's recent investigations."""
        cursor = await self._conn.execute(
            """SELECT * FROM investigations 
               WHERE user_id = ? 
               ORDER BY created_at DESC 
               LIMIT ?""",
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        
        investigations = []
        for row in rows:
            data = dict(row)
            if data['impact_data']:
                data['impact_data'] = json.loads(data['impact_data'])
            investigations.append(Investigation(**data))
        
        return investigations
    
    async def update_investigation_status(
        self, 
        investigation_id: int, 
        status: str
    ) -> bool:
        """Update investigation status."""
        update_fields = {"status": status}
        
        if status == InvestigationStatus.COMPLETED:
            update_fields["completed_at"] = datetime.utcnow()
        elif status == InvestigationStatus.FAILED:
            update_fields["completed_at"] = datetime.utcnow()
        
        # Calculate execution time if completed
        if status in [InvestigationStatus.COMPLETED, InvestigationStatus.FAILED]:
            cursor = await self._conn.execute(
                "SELECT started_at FROM investigations WHERE id = ?",
                (investigation_id,)
            )
            row = await cursor.fetchone()
            if row and row['started_at']:
                started_at = datetime.fromisoformat(row['started_at'])
                execution_time = int((datetime.utcnow() - started_at).total_seconds() * 1000)
                update_fields["execution_time_ms"] = execution_time
        
        # Build dynamic update query
        set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
        values = list(update_fields.values()) + [investigation_id]
        
        await self._conn.execute(
            f"UPDATE investigations SET {set_clause} WHERE id = ?",
            values
        )
        await self._conn.commit()
        
        return True
    
    # Knowledge gap management
    async def create_knowledge_gap(
        self, 
        investigation_id: int,
        component_name: str,
        gap_type: str,
        description: str,
        suggested_action: str
    ) -> KnowledgeGap:
        """Create a knowledge gap record."""
        cursor = await self._conn.execute(
            """INSERT INTO knowledge_gaps 
               (investigation_id, component_name, gap_type, description, suggested_action) 
               VALUES (?, ?, ?, ?, ?)""",
            (investigation_id, component_name, gap_type, description, suggested_action)
        )
        await self._conn.commit()
        
        knowledge_gap_id = cursor.lastrowid
        
        # Update investigation gap count
        await self._conn.execute(
            """UPDATE investigations 
               SET knowledge_gap_count = (
                   SELECT COUNT(*) FROM knowledge_gaps 
                   WHERE investigation_id = ?
               )
               WHERE id = ?""",
            (investigation_id, investigation_id)
        )
        await self._conn.commit()
        
        # Return the created gap
        cursor = await self._conn.execute(
            "SELECT * FROM knowledge_gaps WHERE id = ?",
            (knowledge_gap_id,)
        )
        row = await cursor.fetchone()
        return KnowledgeGap(**row)
    
    async def get_investigation_knowledge_gaps(
        self, 
        investigation_id: int
    ) -> List[KnowledgeGap]:
        """Get knowledge gaps for an investigation."""
        cursor = await self._conn.execute(
            "SELECT * FROM knowledge_gaps WHERE investigation_id = ? ORDER BY created_at DESC",
            (investigation_id,)
        )
        rows = await cursor.fetchall()
        return [KnowledgeGap(**row) for row in rows]
    
    # System configuration
    async def get_config_value(self, key: str) -> Optional[str]:
        """Get configuration value."""
        cursor = await self._conn.execute(
            "SELECT value FROM system_config WHERE key = ?",
            (key,)
        )
        row = await cursor.fetchone()
        return row['value'] if row else None
    
    async def set_config_value(self, key: str, value: str) -> bool:
        """Set configuration value."""
        await self._conn.execute(
            """INSERT OR REPLACE INTO system_config 
               (key, value, updated_at) VALUES (?, ?, ?)""",
            (key, value, datetime.utcnow())
        )
        await self._conn.commit()
        return True
    
    # Session management
    async def create_session(
        self, 
        user_id: int, 
        session_token: str, 
        expires_at: datetime
    ) -> InvestigationSession:
        """Create a user session."""
        cursor = await self._conn.execute(
            """INSERT INTO sessions 
               (user_id, session_token, expires_at) 
               VALUES (?, ?, ?)""",
            (user_id, session_token, expires_at)
        )
        await self._conn.commit()
        
        session_id = cursor.lastrowid
        return await self.get_session_by_token(session_token)
    
    async def get_session_by_token(self, session_token: str) -> Optional[InvestigationSession]:
        """Get session by token."""
        cursor = await self._conn.execute(
            "SELECT * FROM sessions WHERE session_token = ? AND is_active = TRUE",
            (session_token,)
        )
        row = await cursor.fetchone()
        
        if not row:
            return None
            
        # Check if session has expired
        if datetime.fromisoformat(row['expires_at']) < datetime.utcnow():
            await self.delete_session(session_token)
            return None
        
        # Update last accessed
        await self._conn.execute(
            "UPDATE sessions SET last_accessed = ? WHERE session_token = ?",
            (datetime.utcnow(), session_token)
        )
        await self._conn.commit()
        
        return InvestigationSession(**row)
    
    async def delete_session(self, session_token: str) -> bool:
        """Delete session."""
        await self._conn.execute(
            "UPDATE sessions SET is_active = FALSE WHERE session_token = ?",
            (session_token,)
        )
        await self._conn.commit()
        return True
    
    # Analytics
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics."""
        # Total investigations
        cursor = await self._conn.execute(
            "SELECT COUNT(*) as count FROM investigations WHERE user_id = ?",
            (user_id,)
        )
        total_investigations = (await cursor.fetchone())['count']
        
        # Completed investigations
        cursor = await self._conn.execute(
            "SELECT COUNT(*) as count FROM investigations WHERE user_id = ? AND status = ?",
            (user_id, InvestigationStatus.COMPLETED)
        )
        completed_investigations = (await cursor.fetchone())['count']
        
        # Average execution time
        cursor = await self._conn.execute(
            """SELECT AVG(execution_time_ms) as avg_time 
               FROM investigations 
               WHERE user_id = ? AND execution_time_ms IS NOT NULL""",
            (user_id,)
        )
        avg_time_row = await cursor.fetchone()
        avg_execution_time = avg_time_row['avg_time'] if avg_time_row else None
        
        # Knowledge gaps identified
        cursor = await self._conn.execute(
            """SELECT COUNT(*) as count 
               FROM knowledge_gaps kg
               JOIN investigations i ON kg.investigation_id = i.id
               WHERE i.user_id = ?""",
            (user_id,)
        )
        knowledge_gaps = (await cursor.fetchone())['count']
        
        # Last investigation date
        cursor = await self._conn.execute(
            "SELECT MAX(created_at) as last_date FROM investigations WHERE user_id = ?",
            (user_id,)
        )
        last_row = await cursor.fetchone()
        last_investigation = last_row['last_date'] if last_row else None
        
        return UserStats(
            total_investigations=total_investigations,
            completed_investigations=completed_investigations,
            avg_execution_time_ms=avg_execution_time,
            knowledge_gaps_identified=knowledge_gaps,
            last_investigation_date=last_investigation
        ).dict()
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics."""
        # Total users
        cursor = await self._conn.execute(
            "SELECT COUNT(*) as count FROM users WHERE is_active = TRUE"
        )
        total_users = (await cursor.fetchone())['count']
        
        # Total and active investigations
        cursor = await self._conn.execute("SELECT COUNT(*) as count FROM investigations")
        total_investigations = (await cursor.fetchone())['count']
        
        cursor = await self._conn.execute(
            "SELECT COUNT(*) as count FROM investigations WHERE status = ?",
            (InvestigationStatus.RUNNING,)
        )
        active_investigations = (await cursor.fetchone())['count']
        
        # Knowledge gaps
        cursor = await self._conn.execute("SELECT COUNT(*) as count FROM knowledge_gaps")
        total_knowledge_gaps = (await cursor.fetchone())['count']
        
        # Average investigation time
        cursor = await self._conn.execute(
            "SELECT AVG(execution_time_ms) as avg_time FROM investigations WHERE execution_time_ms IS NOT NULL"
        )
        avg_time_row = await cursor.fetchone()
        avg_investigation_time = avg_time_row['avg_time'] if avg_time_row else None
        
        return SystemStats(
            total_users=total_users,
            total_investigations=total_investigations,
            active_investigations=active_investigations,
            total_knowledge_gaps=total_knowledge_gaps,
            avg_investigation_time_ms=avg_investigation_time,
            most_quied_components=None  # TODO: Implement component frequency analysis
        ).dict()