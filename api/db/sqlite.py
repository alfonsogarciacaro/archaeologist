"""
SQLite implementation of the database abstraction layer.

This module provides a lightweight SQLite implementation suitable for
development and small-scale deployments.
"""

import json
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from aiosqlite import Row, connect, Connection

from .base import DatabaseAbc
from models.database import (
    User,
    Project,
    ProjectUser,
    Investigation,
    KnowledgeGap,
    InvestigationSession,
    InvestigationStatus,
    Source,
    UserStats,
    SystemStats,
    Node,
    NodeMetadata
)
from models.jobs import Job, JobType, JobStatus, JobPriority, JobCreate, JobUpdate


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
        
        # Set row_factory to return dictionaries
        self._conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)} # type: ignore
        
        # Enable foreign key constraints
        conn = self._get_connection()
        await conn.execute("PRAGMA foreign_keys = ON")
        
        # Run database migrations
        await self._run_database_migrations()
        
        # Insert default configuration
        await self._insert_default_config()
    
    async def close(self) -> None:
        """Close database connection."""
        if self._conn:
            await self._conn.close()
    
    async def _run_database_migrations(self) -> None:
        """Run database migrations using migration manager."""
        try:
            # Run migrations directly from SQL files
            migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
            
            # Get all migration files
            import glob
            migration_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))
            
            for migration_file in migration_files:
                if os.path.basename(migration_file).startswith("__"):
                    continue
                    
                await self._run_migration_file(migration_file)
                
        except Exception as e:
            # Fallback to legacy migration system if migration manager fails
            print(f"Warning: Migration system failed, using fallback: {e}")
            await self._run_legacy_migrations()
    
    async def _run_migration_file(self, migration_file: str) -> None:
        """Run a single migration file."""
        migration_name = os.path.basename(migration_file)
        print(f"Running migration: {migration_name}")
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Split SQL into individual statements
        statements = self._split_sql_statements(migration_sql)
        
        # Get connection using helper
        conn = self._get_connection()
        
        # Execute each statement
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    await conn.execute(statement)
                except Exception as e:
                    # Log error but continue for idempotent migrations
                    print(f"Statement failed (expected for idempotent migrations): {e}")
        
        await conn.commit()
        print(f"Migration {migration_name} completed successfully")
    
    def _split_sql_statements(self, sql: str) -> list:
        """Split SQL content into individual statements."""
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
    
    async def _run_legacy_migrations(self) -> None:
        """Fallback migration system for backward compatibility."""
        conn = self._get_connection()
        
        # Add metadata column to sources table if it doesn't exist
        try:
            cursor = await conn.execute("PRAGMA table_info(sources)")
            columns = await cursor.fetchall()
            column_names = [col['name'] for col in columns]
            
            if 'metadata' not in column_names:
                await conn.execute("ALTER TABLE sources ADD COLUMN metadata TEXT")
                await conn.commit()
                print("Added metadata column to sources table")
        except Exception as e:
            print(f"Error running legacy migrations: {e}")
    
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
        
        # Create anonymous user if it doesn't exist
        await self._ensure_anonymous_user()
    
    async def _ensure_anonymous_user(self) -> None:
        """Ensure the anonymous user exists in the database."""
        conn = self._get_connection()
        
        # Check if anonymous user already exists
        cursor = await conn.execute("SELECT id FROM users WHERE username = 'anonymous'")
        existing_user = await cursor.fetchone()
        
        if not existing_user:
            # Create the anonymous user with the same hash as in auth_service
            await conn.execute(
                """INSERT INTO users (username, email, hashed_password, is_active, is_admin) 
                   VALUES (?, ?, ?, ?, ?)""",
                ("anonymous", "anonymous@archaeologist.local", 
                 "$2b$12$placeholder_hash_for_anonymous_user_account_no_real_password", 
                 True, False)
            )
            await conn.commit()
    
    # User management
    async def create_user(self, username: str, email: str, hashed_password: str, is_admin: bool = False) -> User:
        """Create a new user."""
        conn = self._get_connection()
        cursor = await conn.execute(
            "INSERT INTO users (username, email, hashed_password, is_admin) VALUES (?, ?, ?, ?)",
            (username, email, hashed_password, is_admin)
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
    
    async def update_user_last_login(self, user_id: int) -> bool:
        """Update the last login timestamp for a user."""
        conn = self._get_connection()
        cursor = await conn.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id,)
        )
        await conn.commit()
        return cursor.rowcount > 0
    
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
        
        kwargs['updated_at'] = datetime.now(timezone.utc).isoformat()
        
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
            (user_id, project_id, query, impact_json, component_count, InvestigationStatus.RUNNING, datetime.now(timezone.utc).isoformat())
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
        investigation_status: Union[str, InvestigationStatus]
    ) -> bool:
        """Update investigation status."""
        conn = self._get_connection()
        
        # Handle both string and enum inputs
        if isinstance(investigation_status, InvestigationStatus):
            status_value = investigation_status.value
            status_enum = investigation_status
        else:
            status_value = investigation_status
            status_enum = InvestigationStatus(investigation_status)
        
        update_fields: Dict[str, Any] = {"status": status_value}
        
        if status_enum == InvestigationStatus.COMPLETED:
            update_fields["completed_at"] = datetime.now(timezone.utc).isoformat()
        elif status_enum == InvestigationStatus.FAILED:
            update_fields["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Calculate execution time if completed
        if status_enum in [InvestigationStatus.COMPLETED, InvestigationStatus.FAILED]:
            cursor = await conn.execute(
                "SELECT started_at FROM investigations WHERE id = ?",
                (investigation_id,)
            )
            row = await cursor.fetchone()
            if row and row['started_at']:
                started_at = datetime.fromisoformat(row['started_at'])
                execution_time = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
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
            (key, value, datetime.now(timezone.utc).isoformat())
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
        if datetime.fromisoformat(row['expires_at']) < datetime.now(timezone.utc):
            await self.delete_session(session_token)
            return None
        
        # Update last accessed
        await conn.execute(
            "UPDATE sessions SET last_accessed = ? WHERE session_token = ?",
            (datetime.now(timezone.utc).isoformat(), session_token)
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

    def row_to_source(self, row: Row) -> Source:
        """Convert a database row to a Source object."""
        row_dict = dict(row)
        if row_dict.get('metadata'):
            row_dict['metadata'] = json.loads(row_dict['metadata'])
        return Source(**row_dict)        

    # Source management
    async def create_source(
        self,
        project_id: int,
        filename: str,
        original_filename: str,
        file_size: int,
        file_type: str,
        content_type: str,
        data_lake_entry_id: str,
        uploaded_by: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Source:
        """Create a new source record."""
        conn = self._get_connection()

        cursor = await conn.execute("""
            INSERT INTO sources (
                project_id, filename, original_filename, file_size,
                file_type, content_type, data_lake_entry_id, metadata, uploaded_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id, filename, original_filename, file_size,
            file_type, content_type, data_lake_entry_id, 
            json.dumps(metadata) if metadata else None,
            uploaded_by
        ))

        source_id = cursor.lastrowid
        await conn.commit()
        
        # Retrieve created source
        cursor = await conn.execute(
            "SELECT * FROM sources WHERE id = ?", (source_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise RuntimeError("Failed to retrieve source after creation.")

        return self.row_to_source(row)

    async def get_project_sources(self, project_id: int) -> List[Source]:
        """Get all sources for a project."""
        conn = self._get_connection()

        cursor = await conn.execute(
            "SELECT * FROM sources WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,)
        )
        rows = await cursor.fetchall()
        
        sources = [self.row_to_source(row) for row in rows]
        
        return sources

    async def get_source_by_id(self, source_id: int) -> Optional[Source]:
        """Get source by ID."""
        conn = self._get_connection()

        cursor = await conn.execute(
            "SELECT * FROM sources WHERE id = ?", (source_id,)
        )
        row = await cursor.fetchone()

        return self.row_to_source(row) if row else None

    async def delete_source(self, source_id: int) -> bool:
        """Delete a source."""
        conn = self._get_connection()
        
        cursor = await conn.execute(
            "DELETE FROM sources WHERE id = ?", (source_id,)
        )
        await conn.commit()
        
        deleted_count = cursor.rowcount
        return deleted_count > 0

    async def update_source_metadata(self, source_id: int, metadata: Dict[str, Any]) -> bool:
        """Update source metadata."""
        conn = self._get_connection()
        
        cursor = await conn.execute(
            "UPDATE sources SET metadata = ? WHERE id = ?",
            (json.dumps(metadata), source_id)
        )
        await conn.commit()
        
        return cursor.rowcount > 0
    
    # Node management
    async def create_node(self, node: Node) -> Node:
        """Create a new node."""
        conn = self._get_connection()
        
        await conn.execute("""
            INSERT INTO nodes (id, project_id, name, type, path, source_type, confidence, metadata, investigation_id, source_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            node.id,
            node.project_id,
            node.name,
            node.type,
            node.path,
            node.source_type,
            node.confidence,
            json.dumps(node.metadata) if node.metadata else None,
            node.investigation_id,
            node.source_id
        ))
        
        await conn.commit()
        
        # Return created node
        created_node = await self.get_node_by_id(node.id)
        if created_node:
            return created_node
        else:
            # Fallback to input node if database query fails
            return node
    
    async def get_node_by_id(self, node_id: str) -> Optional[Node]:
        """Get node by ID."""
        conn = self._get_connection()
        
        cursor = await conn.execute(
            "SELECT * FROM nodes WHERE id = ?", (node_id,)
        )
        row = await cursor.fetchone()
        
        if row:
            # Parse JSON metadata - convert Row to dict first
            row_dict = {key: row[key] for key in row.keys()}
            if row_dict['metadata']:
                row_dict['metadata'] = json.loads(row_dict['metadata'])
            return Node(**row_dict)
        
        return None
    
    async def update_node(self, node_id: str, **kwargs) -> bool:
        """Update node details."""
        conn = self._get_connection()
        
        # Build dynamic update query
        set_clauses = []
        values = []
        
        for key, value in kwargs.items():
            if key in ['name', 'type', 'path', 'source_type', 'confidence']:
                set_clauses.append(f"{key} = ?")
                values.append(value)
            elif key == 'metadata':
                set_clauses.append("metadata = ?")
                values.append(json.dumps(value) if value else None)
        
        if not set_clauses:
            return False
        
        values.append(node_id)
        
        cursor = await conn.execute(
            f"UPDATE nodes SET {', '.join(set_clauses)} WHERE id = ?",
            values
        )
        await conn.commit()
        
        return cursor.rowcount > 0
    
    async def delete_node(self, node_id: str) -> bool:
        """Delete a node."""
        conn = self._get_connection()
        
        cursor = await conn.execute(
            "DELETE FROM nodes WHERE id = ?", (node_id,)
        )
        await conn.commit()
        
        return cursor.rowcount > 0
    
    async def update_node_metadata(self, node_id: str, metadata: Dict[str, Any]) -> bool:
        """Update node metadata."""
        conn = self._get_connection()

        cursor = await conn.execute(
            "UPDATE nodes SET metadata = ? WHERE id = ?",
            (json.dumps(metadata), node_id)
        )
        await conn.commit()

        return cursor.rowcount > 0

    # Job management
    def row_to_job(self, row: Row) -> Job:
        """Convert a database row to a Job object."""
        row_dict = dict(row)

        # Parse JSON fields
        if row_dict.get('job_data'):
            row_dict['job_data'] = json.loads(row_dict['job_data'])
        if row_dict.get('result_data'):
            row_dict['result_data'] = json.loads(row_dict['result_data'])

        return Job(**row_dict)

    async def create_job(self, job_create: JobCreate) -> Job:
        """Create a new job."""
        import uuid
        conn = self._get_connection()

        job_id = str(uuid.uuid4())
        job_data_json = json.dumps(job_create.job_data) if job_create.job_data else None

        cursor = await conn.execute("""
            INSERT INTO jobs (
                id, job_type, status, priority, project_id, user_id,
                source_id, investigation_id, job_data, timeout_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id, job_create.job_type.value, JobStatus.PENDING.value,
            job_create.priority.value, job_create.project_id, job_create.user_id,
            job_create.source_id, job_create.investigation_id,
            job_data_json, job_create.timeout_seconds
        ))

        await conn.commit()

        # Retrieve created job
        created_job = await self.get_job_by_id(job_id)
        if not created_job:
            raise RuntimeError("Failed to retrieve job after creation.")

        return created_job

    async def get_job_by_id(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        conn = self._get_connection()

        cursor = await conn.execute(
            "SELECT * FROM jobs WHERE id = ?", (job_id,)
        )
        row = await cursor.fetchone()

        return self.row_to_job(row) if row else None

    async def get_user_jobs(
        self,
        user_id: int,
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        project_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Job]:
        """Get jobs for a user, with optional filters."""
        conn = self._get_connection()

        # Build query with filters
        query = "SELECT * FROM jobs WHERE user_id = ?"
        params = [user_id]

        if status:
            query += " AND status = ?"
            params.append(status.value)

        if job_type:
            query += " AND job_type = ?"
            params.append(job_type.value)

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()

        return [self.row_to_job(row) for row in rows]

    async def get_project_jobs(
        self,
        project_id: int,
        status: Optional[JobStatus] = None,
        limit: int = 50
    ) -> List[Job]:
        """Get jobs for a project."""
        conn = self._get_connection()

        query = "SELECT * FROM jobs WHERE project_id = ?"
        params = [project_id]

        if status:
            query += " AND status = ?"
            params.append(status.value)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()

        return [self.row_to_job(row) for row in rows]

    async def update_job(self, job_id: str, job_update: JobUpdate) -> bool:
        """Update job status and metadata."""
        conn = self._get_connection()

        # Build dynamic update query
        update_fields = []
        params = []

        if job_update.status:
            update_fields.append("status = ?")
            params.append(job_update.status.value)

            # Update timestamps based on status
            if job_update.status == JobStatus.QUEUED:
                update_fields.append("queued_at = CURRENT_TIMESTAMP")
            elif job_update.status == JobStatus.RUNNING:
                update_fields.append("started_at = CURRENT_TIMESTAMP")
            elif job_update.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                update_fields.append("completed_at = CURRENT_TIMESTAMP")

        if job_update.progress_current is not None:
            update_fields.append("progress_current = ?")
            params.append(job_update.progress_current)

        if job_update.progress_total is not None:
            update_fields.append("progress_total = ?")
            params.append(job_update.progress_total)

        if job_update.progress_message:
            update_fields.append("progress_message = ?")
            params.append(job_update.progress_message)

        if job_update.result_data:
            update_fields.append("result_data = ?")
            params.append(json.dumps(job_update.result_data))

        if job_update.error_message:
            update_fields.append("error_message = ?")
            params.append(job_update.error_message)

        if job_update.worker_id:
            update_fields.append("worker_id = ?")
            params.append(job_update.worker_id)

        if not update_fields:
            return False

        query = f"UPDATE jobs SET {', '.join(update_fields)} WHERE id = ?"
        params.append(job_id)

        cursor = await conn.execute(query, params)
        await conn.commit()

        return cursor.rowcount > 0

    async def get_pending_jobs(self, limit: int = 10) -> List[Job]:
        """Get pending jobs ordered by priority and creation time."""
        conn = self._get_connection()

        cursor = await conn.execute("""
            SELECT * FROM jobs
            WHERE status IN (?, ?)
            ORDER BY
                CASE priority
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'normal' THEN 3
                    WHEN 'low' THEN 4
                END,
                created_at ASC
            LIMIT ?
        """, (JobStatus.PENDING.value, JobStatus.QUEUED.value, limit))

        rows = await cursor.fetchall()
        return [self.row_to_job(row) for row in rows]

    async def increment_job_retry(self, job_id: str) -> bool:
        """Increment job retry count."""
        conn = self._get_connection()

        cursor = await conn.execute(
            "UPDATE jobs SET retry_count = retry_count + 1 WHERE id = ?",
            (job_id,)
        )
        await conn.commit()

        return cursor.rowcount > 0

    async def delete_job(self, job_id: str) -> bool:
        """Delete a job."""
        conn = self._get_connection()

        cursor = await conn.execute(
            "DELETE FROM jobs WHERE id = ?",
            (job_id,)
        )
        await conn.commit()

        return cursor.rowcount > 0

    async def get_job_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get job statistics, optionally filtered by user."""
        conn = self._get_connection()

        # Base query
        base_where = "WHERE 1=1"
        params = []

        if user_id:
            base_where += " AND user_id = ?"
            params.append(user_id)

        # Get counts by status
        cursor = await conn.execute(f"""
            SELECT
                COUNT(*) as total_jobs,
                COUNT(CASE WHEN status = ? THEN 1 END) as pending_jobs,
                COUNT(CASE WHEN status = ? THEN 1 END) as running_jobs,
                COUNT(CASE WHEN status = ? THEN 1 END) as completed_jobs,
                COUNT(CASE WHEN status = ? THEN 1 END) as failed_jobs
            FROM jobs {base_where}
        """, params + [JobStatus.PENDING.value, JobStatus.RUNNING.value, JobStatus.COMPLETED.value, JobStatus.FAILED.value])

        stats_row = await cursor.fetchone()

        # Calculate success rate and average duration
        cursor = await conn.execute(f"""
            SELECT
                AVG(CASE
                    WHEN completed_at IS NOT NULL AND started_at IS NOT NULL
                    THEN (julianday(completed_at) - julianday(started_at)) * 86400
                    ELSE NULL
                END) as avg_duration_seconds,
                COUNT(CASE WHEN status = ? THEN 1 END) * 100.0 / COUNT(*) as success_rate
            FROM jobs {base_where}
        """, params + [JobStatus.COMPLETED.value])

        duration_row = await cursor.fetchone()

        return {
            "total_jobs": stats_row['total_jobs'] if stats_row else 0,
            "pending_jobs": stats_row['pending_jobs'] if stats_row else 0,
            "running_jobs": stats_row['running_jobs'] if stats_row else 0,
            "completed_jobs": stats_row['completed_jobs'] if stats_row else 0,
            "failed_jobs": stats_row['failed_jobs'] if stats_row else 0,
            "avg_duration_seconds": duration_row['avg_duration_seconds'] if duration_row else None,
            "success_rate": duration_row['success_rate'] if duration_row else 0.0
        }
