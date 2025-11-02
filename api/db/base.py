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
    
    # Investigation management
    @abc.abstractmethod
    async def create_investigation(
        self, 
        user_id: int, 
        query: str, 
        impact_data: Dict[str, Any]
    ) -> Investigation:
        """Create a new investigation record."""
        pass
    
    @abc.abstractmethod
    async def get_investigation_by_id(self, investigation_id: int) -> Optional[Investigation]:
        """Get investigation by ID."""
        pass
    
    @abc.abstractmethod
    async def get_user_investigations(self, user_id: int, limit: int = 10) -> List[Investigation]:
        """Get user's recent investigations."""
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
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics."""
        pass
    
    @abc.abstractmethod
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics."""
        pass