"""
Database abstraction layer for the Enterprise Code Archaeologist.

This module provides a clean interface for database operations,
allowing easy switching between implementations (SQLite, PostgreSQL, etc.).
"""

import abc
from typing import List, Optional, Dict, Any
from datetime import datetime

from api.models.database import (
    User, 
    Project,
    ProjectUser,
    ProjectRole,
    Investigation, 
    KnowledgeGap, 
    SystemConfig,
    InvestigationSession
)


class DatabaseAbc(abc.ABC):
    """Abstract base class for database implementations."""
    
    @abc.abstractmethod
    async def initialize(self) -> None:
        """Initialize database connection and create tables."""
        pass
    
    @abc.abstractmethod
    async def close(self) -> None:
        """Close database connection."""
        pass
    
    # User management
    @abc.abstractmethod
    async def create_user(self, username: str, email: str, hashed_password: str) -> User:
        """Create a new user."""
        pass
    
    @abc.abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        pass
    
    @abc.abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        pass
    
    @abc.abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass
    
    # Project management
    @abc.abstractmethod
    async def create_project(
        self, 
        name: str, 
        description: Optional[str], 
        repository_paths: Optional[List[str]], 
        created_by: int
    ) -> Project:
        """Create a new project."""
        pass
    
    @abc.abstractmethod
    async def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """Get project by ID."""
        pass
    
    @abc.abstractmethod
    async def get_user_projects(self, user_id: int) -> List[Project]:
        """Get all projects accessible to a user."""
        pass
    
    @abc.abstractmethod
    async def update_project(self, project_id: int, **kwargs) -> bool:
        """Update project details."""
        pass
    
    @abc.abstractmethod
    async def delete_project(self, project_id: int) -> bool:
        """Delete a project."""
        pass
    
    # Project user management
    @abc.abstractmethod
    async def add_user_to_project(
        self, 
        project_id: int, 
        user_id: int, 
        role: str
    ) -> ProjectUser:
        """Add a user to a project with a specific role."""
        pass
    
    @abc.abstractmethod
    async def remove_user_from_project(self, project_id: int, user_id: int) -> bool:
        """Remove a user from a project."""
        pass
    
    @abc.abstractmethod
    async def get_project_users(self, project_id: int) -> List[ProjectUser]:
        """Get all users in a project."""
        pass
    
    @abc.abstractmethod
    async def get_user_project_role(self, project_id: int, user_id: int) -> Optional[str]:
        """Get a user's role in a specific project."""
        pass
    
    @abc.abstractmethod
    async def update_user_project_role(
        self, 
        project_id: int, 
        user_id: int, 
        role: str
    ) -> bool:
        """Update a user's role in a project."""
        pass
    
    # Investigation management
    @abc.abstractmethod
    async def create_investigation(
        self, 
        user_id: int, 
        query: str, 
        impact_data: Dict[str, Any],
        project_id: Optional[int] = None
    ) -> Investigation:
        """Create a new investigation record."""
        pass
    
    @abc.abstractmethod
    async def get_investigation_by_id(self, investigation_id: int) -> Optional[Investigation]:
        """Get investigation by ID."""
        pass
    
    @abc.abstractmethod
    async def get_user_investigations(
        self, 
        user_id: int, 
        project_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Investigation]:
        """Get user's recent investigations, optionally filtered by project."""
        pass
    
    @abc.abstractmethod
    async def get_project_investigations(
        self, 
        project_id: int, 
        limit: int = 10
    ) -> List[Investigation]:
        """Get investigations for a specific project."""
        pass
    
    @abc.abstractmethod
    async def update_investigation_status(
        self, 
        investigation_id: int, 
        status: str
    ) -> bool:
        """Update investigation status."""
        pass
    
    # Knowledge gap management
    @abc.abstractmethod
    async def create_knowledge_gap(
        self, 
        investigation_id: int,
        component_name: str,
        gap_type: str,
        description: str,
        suggested_action: str
    ) -> KnowledgeGap:
        """Create a knowledge gap record."""
        pass
    
    @abc.abstractmethod
    async def get_investigation_knowledge_gaps(
        self, 
        investigation_id: int
    ) -> List[KnowledgeGap]:
        """Get knowledge gaps for an investigation."""
        pass
    
    # System configuration
    @abc.abstractmethod
    async def get_config_value(self, key: str) -> Optional[str]:
        """Get configuration value."""
        pass
    
    @abc.abstractmethod
    async def set_config_value(self, key: str, value: str) -> bool:
        """Set configuration value."""
        pass
    
    # Session management
    @abc.abstractmethod
    async def create_session(
        self, 
        user_id: int, 
        session_token: str, 
        expires_at: datetime
    ) -> InvestigationSession:
        """Create a user session."""
        pass
    
    @abc.abstractmethod
    async def get_session_by_token(self, session_token: str) -> Optional[InvestigationSession]:
        """Get session by token."""
        pass
    
    @abc.abstractmethod
    async def delete_session(self, session_token: str) -> bool:
        """Delete session."""
        pass
    
    # Analytics
    @abc.abstractmethod
    async def get_user_stats(self, user_id: int, project_id: Optional[int] = None) -> Dict[str, Any]:
        """Get user statistics, optionally filtered by project."""
        pass
    
    @abc.abstractmethod
    async def get_project_stats(self, project_id: int) -> Dict[str, Any]:
        """Get project-specific statistics."""
        pass
    
    @abc.abstractmethod
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics."""
        pass