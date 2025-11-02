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
    Project,
    ProjectUser,
    ProjectRole,
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
    
    def _get_connection(self) -> Connection:
        """Get the database connection, raising an error if not initialized."""
        if self._conn is None:
            raise RuntimeError("Database connection not initialized. Call initialize() first.")
        return self._conn
    
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
        conn = self._get_connection()
        
        # Users table
        await conn.execute("""
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
        
        # Projects table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                repository_paths TEXT,  -- JSON array of repository paths
                is_active BOOLEAN DEFAULT TRUE,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # Project users table (many-to-many relationship)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS project_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(project_id, user_id),
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # Investigations table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS investigations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                project_id INTEGER,
                query TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                impact_data TEXT,
                component_count INTEGER,
                knowledge_gap_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                execution_time_ms INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE SET NULL
            )
        """)
        
        # Knowledge gaps table
        await conn.execute("""
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
        await conn.execute("""
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
        await conn.execute("""
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
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_investigations_user_id ON investigations (user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_investigations_project_id ON investigations (project_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_investigations_status ON investigations (status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_gaps_investigation_id ON knowledge_gaps (investigation_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions (session_token)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_created_by ON projects (created_by)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_is_active ON projects (is_active)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_project_users_project_id ON project_users (project_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_project_users_user_id ON project_users (user_id)")
        
        await conn.commit()
    
    async def _insert_default_config(self) -> None:
        """Insert default system configuration."""
        conn = self._get_connection()
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
        conn = self._get_connection()
        cursor = await conn.execute(
            "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
            (username, email, hashed_password)
        )
        await conn.commit()
        
        user_id = cursor.lastrowid
        if user_id is None:
            raise RuntimeError("Failed to retrieve last inserted user ID.")

        user = await self.get_user_by_id(user_id)
        if user is None:
            raise RuntimeError("Failed to retrieve user after creation.")
        
        return user
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        conn = self._get_connection()
        cursor = await conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
        row = await cursor.fetchone()
        return User(**row) if row else None
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        conn = self._get_connection()
        cursor = await conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return User(**row) if row else None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        conn = self._get_connection()
        cursor = await conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )
        row = await cursor.fetchone()
        return User(**row) if row else None
    
    # Project management
    async def create_project(
        self, 
        name: str, 
        description: Optional[str], 
        repository_paths: Optional[List[str]], 
        created_by: int
    ) -> Project:
        """Create a new project."""
        conn = self._get_connection()
        repo_paths_json = json.dumps(repository_paths) if repository_paths else None
        cursor = await conn.execute(
            """INSERT INTO projects 
               (name, description, repository_paths, created_by) 
               VALUES (?, ?, ?, ?)""",
            (name, description, repo_paths_json, created_by)
        )
        await conn.commit()
        
        project_id = cursor.lastrowid
        if project_id is None:
            raise RuntimeError("Failed to retrieve last inserted project ID.")
        
        # Add creator as project owner
        await self.add_user_to_project(project_id, created_by, "owner")
        
        project = await self.get_project_by_id(project_id)
        if project is None:
            raise RuntimeError("Failed to retrieve project after creation.")
        
        return project
    
    async def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """Get project by ID."""
        conn = self._get_connection()
        cursor = await conn.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            return None
        
        data = dict(row)
        if data['repository_paths']:
            data['repository_paths'] = json.loads(data['repository_paths'])
        
        return Project(**data)
    
    async def get_user_projects(self, user_id: int) -> List[Project]:
        """Get all projects accessible to a user."""
        conn = self._get_connection()
        cursor = await conn.execute(
            """SELECT p.* FROM projects p
               JOIN project_users pu ON p.id = pu.project_id
               WHERE pu.user_id = ? AND pu.is_active = TRUE AND p.is_active = TRUE
               ORDER BY p.updated_at DESC""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        
        projects = []
        for row in rows:
            data = dict(row)
            if data['repository_paths']:
                data['repository_paths'] = json.loads(data['repository_paths'])
            projects.append(Project(**data))
        
        return projects
    
    async def update_project(self, project_id: int, **kwargs) -> bool:
        """Update project details."""
        if not kwargs:
            return True
        
        conn = self._get_connection()
        
        # Handle JSON field
        if 'repository_paths' in kwargs:
            kwargs['repository_paths'] = json.dumps(kwargs['repository_paths'])
        
        kwargs['updated_at'] = datetime.utcnow()
        
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [project_id]
        
        await conn.execute(
            f"UPDATE projects SET {set_clause} WHERE id = ?",
            values
        )
        await conn.commit()
        
        return True
    
    async def delete_project(self, project_id: int) -> bool:
        """Delete a project."""
        conn = self._get_connection()
        await conn.execute(
            "UPDATE projects SET is_active = FALSE WHERE id = ?",
            (project_id,)
        )
        await conn.commit()
        return True
    
    # Project user management
    async def add_user_to_project(
        self, 
        project_id: int, 
        user_id: int, 
        role: str
    ) -> ProjectUser:
        """Add a user to a project with a specific role."""
        conn = self._get_connection()
        cursor = await conn.execute(
            "INSERT OR REPLACE INTO project_users (project_id, user_id, role) VALUES (?, ?, ?)",
            (project_id, user_id, role)
        )
        await conn.commit()
        
        project_user_id = cursor.lastrowid
        
        cursor = await conn.execute(
            "SELECT * FROM project_users WHERE id = ?",
            (project_user_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise RuntimeError("Failed to retrieve project user after addition.")

        return ProjectUser(**row)
    
    async def remove_user_from_project(self, project_id: int, user_id: int) -> bool:
        """Remove a user from a project."""
        conn = self._get_connection()
        await conn.execute(
            "UPDATE project_users SET is_active = FALSE WHERE project_id = ? AND user_id = ?",
            (project_id, user_id)
        )
        await conn.commit()
        return True
    
    async def get_project_users(self, project_id: int) -> List[ProjectUser]:
        """Get all users in a project."""
        conn = self._get_connection()
        cursor = await conn.execute(
            "SELECT * FROM project_users WHERE project_id = ? AND is_active = TRUE",
            (project_id,)
        )
        rows = await cursor.fetchall()
        return [ProjectUser(**row) for row in rows]
    
    async def get_user_project_role(self, project_id: int, user_id: int) -> Optional[str]:
        """Get a user's role in a specific project."""
        conn = self._get_connection()
        cursor = await conn.execute(
            "SELECT role FROM project_users WHERE project_id = ? AND user_id = ? AND is_active = TRUE",
            (project_id, user_id)
        )
        row = await cursor.fetchone()
        return row['role'] if row else None
    
    async def update_user_project_role(
        self, 
        project_id: int, 
        user_id: int, 
        role: str
    ) -> bool:
        """Update a user's role in a project."""
        conn = self._get_connection()
        await conn.execute(
            "UPDATE project_users SET role = ? WHERE project_id = ? AND user_id = ?",
            (role, project_id, user_id)
        )
        await conn.commit()
        return True
    
    # Investigation management
    async def create_investigation(
        self, 
        user_id: int, 
        query: str, 
        impact_data: Dict[str, Any],
        project_id: Optional[int] = None
    ) -> Investigation:
        """Create a new investigation record."""
        conn = self._get_connection()
        impact_json = json.dumps(impact_data) if impact_data else None
        component_count = len(impact_data.get('components', [])) if impact_data else 0
        
        cursor = await conn.execute(
            """INSERT INTO investigations 
               (user_id, project_id, query, impact_data, component_count, status, started_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, project_id, query, impact_json, component_count, InvestigationStatus.RUNNING, datetime.utcnow())
        )
        await conn.commit()
        
        investigation_id = cursor.lastrowid
        if investigation_id is None:
            raise RuntimeError("Failed to retrieve last inserted investigation ID.")
        
        investigation = await self.get_investigation_by_id(investigation_id)
        if investigation is None:
            raise RuntimeError("Failed to retrieve investigation after creation.")
        
        return investigation
    
    async def get_investigation_by_id(self, investigation_id: int) -> Optional[Investigation]:
        """Get investigation by ID."""
        conn = self._get_connection()
        cursor = await conn.execute(
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
    
    async def get_user_investigations(
        self, 
        user_id: int, 
        project_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Investigation]:
        """Get user's recent investigations, optionally filtered by project."""
        conn = self._get_connection()
        if project_id:
            cursor = await conn.execute(
                """SELECT * FROM investigations 
                   WHERE user_id = ? AND project_id = ?
                   ORDER BY created_at DESC 
                   LIMIT ?""",
                (user_id, project_id, limit)
            )
        else:
            cursor = await conn.execute(
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
    
    async def get_project_investigations(
        self, 
        project_id: int, 
        limit: int = 10
    ) -> List[Investigation]:
        """Get investigations for a specific project."""
        conn = self._get_connection()
        cursor = await conn.execute(
            """SELECT * FROM investigations 
               WHERE project_id = ?
               ORDER BY created_at DESC 
               LIMIT ?""",
            (project_id, limit)
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
        conn = self._get_connection()
        update_fields = {"status": status}
        
        if status == InvestigationStatus.COMPLETED:
            update_fields["completed_at"] = datetime.utcnow()
        elif status == InvestigationStatus.FAILED:
            update_fields["completed_at"] = datetime.utcnow()
        
        # Calculate execution time if completed
        if status in [InvestigationStatus.COMPLETED, InvestigationStatus.FAILED]:
            cursor = await conn.execute(
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
        
        await conn.execute(
            f"UPDATE investigations SET {set_clause} WHERE id = ?",
            values
        )
        await conn.commit()
        
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
        conn = self._get_connection()
        cursor = await conn.execute(
            """INSERT INTO knowledge_gaps 
               (investigation_id, component_name, gap_type, description, suggested_action) 
               VALUES (?, ?, ?, ?, ?)""",
            (investigation_id, component_name, gap_type, description, suggested_action)
        )
        await conn.commit()
        
        knowledge_gap_id = cursor.lastrowid
        
        # Update investigation gap count
        await conn.execute(
            """UPDATE investigations 
               SET knowledge_gap_count = (
                   SELECT COUNT(*) FROM knowledge_gaps 
                   WHERE investigation_id = ?
               )
               WHERE id = ?""",
            (investigation_id, investigation_id)
        )
        await conn.commit()
        
        # Return the created gap
        cursor = await conn.execute(
            "SELECT * FROM knowledge_gaps WHERE id = ?",
            (knowledge_gap_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise RuntimeError("Failed to retrieve knowledge gap after creation.")
        return KnowledgeGap(**row)
    
    async def get_investigation_knowledge_gaps(
        self, 
        investigation_id: int
    ) -> List[KnowledgeGap]:
        """Get knowledge gaps for an investigation."""
        conn = self._get_connection()
        cursor = await conn.execute(
            "SELECT * FROM knowledge_gaps WHERE investigation_id = ? ORDER BY created_at DESC",
            (investigation_id,)
        )
        rows = await cursor.fetchall()
        return [KnowledgeGap(**row) for row in rows]
    
    # System configuration
    async def get_config_value(self, key: str) -> Optional[str]:
        """Get configuration value."""
        conn = self._get_connection()
        cursor = await conn.execute(
            "SELECT value FROM system_config WHERE key = ?",
            (key,)
        )
        row = await cursor.fetchone()
        return row['value'] if row else None
    
    async def set_config_value(self, key: str, value: str) -> bool:
        """Set configuration value."""
        conn = self._get_connection()
        await conn.execute(
            """INSERT OR REPLACE INTO system_config 
               (key, value, updated_at) VALUES (?, ?, ?)""",
            (key, value, datetime.utcnow())
        )
        await conn.commit()
        return True
    
    # Session management
    async def create_session(
        self, 
        user_id: int, 
        session_token: str, 
        expires_at: datetime
    ) -> InvestigationSession:
        """Create a user session."""
        conn = self._get_connection()
        cursor = await conn.execute(
            """INSERT INTO sessions 
               (user_id, session_token, expires_at) 
               VALUES (?, ?, ?)""",
            (user_id, session_token, expires_at)
        )
        await conn.commit()
        
        session_id = cursor.lastrowid
        if session_id is None:
            raise RuntimeError("Failed to retrieve last inserted session ID.")
        session = await self.get_session_by_token(session_token)
        if session is None:
            raise RuntimeError("Failed to retrieve session after creation.")

        return session

    async def get_session_by_token(self, session_token: str) -> Optional[InvestigationSession]:
        """Get session by token."""
        conn = self._get_connection()
        cursor = await conn.execute(
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
        await conn.execute(
            "UPDATE sessions SET last_accessed = ? WHERE session_token = ?",
            (datetime.utcnow(), session_token)
        )
        await conn.commit()
        
        return InvestigationSession(**row)
    
    async def delete_session(self, session_token: str) -> bool:
        """Delete session."""
        conn = self._get_connection()
        await conn.execute(
            "UPDATE sessions SET is_active = FALSE WHERE session_token = ?",
            (session_token,)
        )
        await conn.commit()
        return True
    
    # Analytics
    async def get_user_stats(self, user_id: int, project_id: Optional[int] = None) -> Dict[str, Any]:
        """Get user statistics, optionally filtered by project."""
        conn = self._get_connection()
        
        # Total investigations
        if project_id:
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM investigations WHERE user_id = ? AND project_id = ?",
                (user_id, project_id)
            )
        else:
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM investigations WHERE user_id = ?",
                (user_id,)
            )
        row = await cursor.fetchone()
        total_investigations = row['count'] if row else 0
        
        # Completed investigations
        if project_id:
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM investigations WHERE user_id = ? AND project_id = ? AND status = ?",
                (user_id, project_id, InvestigationStatus.COMPLETED)
            )
        else:
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM investigations WHERE user_id = ? AND status = ?",
                (user_id, InvestigationStatus.COMPLETED)
            )
        row = await cursor.fetchone()
        completed_investigations = row['count'] if row else 0

        # Average execution time
        if project_id:
            cursor = await conn.execute(
                """SELECT AVG(execution_time_ms) as avg_time 
                   FROM investigations 
                   WHERE user_id = ? AND project_id = ? AND execution_time_ms IS NOT NULL""",
                (user_id, project_id)
            )
        else:
            cursor = await conn.execute(
                """SELECT AVG(execution_time_ms) as avg_time 
                   FROM investigations 
                   WHERE user_id = ? AND execution_time_ms IS NOT NULL""",
                (user_id,)
            )
        avg_time_row = await cursor.fetchone()
        avg_execution_time = avg_time_row['avg_time'] if avg_time_row else None
        
        # Knowledge gaps identified
        if project_id:
            cursor = await conn.execute(
                """SELECT COUNT(*) as count 
                   FROM knowledge_gaps kg
                   JOIN investigations i ON kg.investigation_id = i.id
                   WHERE i.user_id = ? AND i.project_id = ?""",
                (user_id, project_id)
            )
        else:
            cursor = await conn.execute(
                """SELECT COUNT(*) as count 
                   FROM knowledge_gaps kg
                   JOIN investigations i ON kg.investigation_id = i.id
                   WHERE i.user_id = ?""",
                (user_id,)
            )
        row = await cursor.fetchone()
        knowledge_gaps = row['count'] if row else 0

        # Last investigation date
        if project_id:
            cursor = await conn.execute(
                "SELECT MAX(created_at) as last_date FROM investigations WHERE user_id = ? AND project_id = ?",
                (user_id, project_id)
            )
        else:
            cursor = await conn.execute(
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
        ).model_dump()
    
    async def get_project_stats(self, project_id: int) -> Dict[str, Any]:
        """Get project-specific statistics."""
        conn = self._get_connection()
        
        # Total investigations
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM investigations WHERE project_id = ?",
            (project_id,)
        )
        row = await cursor.fetchone()
        total_investigations = row['count'] if row else 0

        # Active investigations
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM investigations WHERE project_id = ? AND status = ?",
            (project_id, InvestigationStatus.RUNNING)
        )
        row = await cursor.fetchone()
        active_investigations = row['count'] if row else 0

        # Knowledge gaps
        cursor = await conn.execute(
            """SELECT COUNT(*) as count 
               FROM knowledge_gaps kg
               JOIN investigations i ON kg.investigation_id = i.id
               WHERE i.project_id = ?""",
            (project_id,)
        )
        row = await cursor.fetchone()
        total_knowledge_gaps = row['count'] if row else 0

        # Average investigation time
        cursor = await conn.execute(
            """SELECT AVG(execution_time_ms) as avg_time 
               FROM investigations 
               WHERE project_id = ? AND execution_time_ms IS NOT NULL""",
            (project_id,)
        )
        avg_time_row = await cursor.fetchone()
        avg_investigation_time = avg_time_row['avg_time'] if avg_time_row else None
        
        # Project users
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM project_users WHERE project_id = ? AND is_active = TRUE",
            (project_id,)
        )
        row = await cursor.fetchone()
        total_users = row['count'] if row else 0

        return {
            "total_investigations": total_investigations,
            "active_investigations": active_investigations,
            "total_knowledge_gaps": total_knowledge_gaps,
            "avg_investigation_time_ms": avg_investigation_time,
            "total_users": total_users
        }
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics."""
        conn = self._get_connection()
        
        # Total users
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM users WHERE is_active = TRUE"
        )
        row = await cursor.fetchone()
        total_users = row['count'] if row else 0

        # Total and active investigations
        cursor = await conn.execute("SELECT COUNT(*) as count FROM investigations")
        row = await cursor.fetchone()
        total_investigations = row['count'] if row else 0
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM investigations WHERE status = ?",
            (InvestigationStatus.RUNNING,)
        )
        row = await cursor.fetchone()
        active_investigations = row['count'] if row else 0

        # Knowledge gaps
        cursor = await conn.execute("SELECT COUNT(*) as count FROM knowledge_gaps")
        row = await cursor.fetchone()
        total_knowledge_gaps = row['count'] if row else 0
        
        # Average investigation time
        cursor = await conn.execute(
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
        ).model_dump()