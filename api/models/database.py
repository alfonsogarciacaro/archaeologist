"""
Database models for the Enterprise Code Archaeologist.

Pydantic models for structured data storage in the relational database.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


class User(BaseModel):
    """User model for authentication and authorization."""
    id: Optional[int] = None
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    hashed_password: str = Field(..., min_length=60)
    is_active: bool = True
    is_admin: bool = False
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class InvestigationStatus(str, Enum):
    """Investigation status values."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Investigation(BaseModel):
    """Investigation record storing user queries and results."""
    id: Optional[int] = None
    user_id: int
    query: str = Field(..., min_length=1, max_length=1000)
    status: InvestigationStatus = InvestigationStatus.PENDING
    impact_data: Optional[Dict[str, Any]] = None
    component_count: Optional[int] = None
    knowledge_gap_count: Optional[int] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None


class KnowledgeGapType(str, Enum):
    """Types of knowledge gaps."""
    MISSING_DEPENDENCY = "missing_dependency"
    UNKNOWN_API = "unknown_api"
    UNCLEAR_RELATIONSHIP = "unclear_relationship"
    OUTDATED_DOCUMENTATION = "outdated_documentation"
    TEAM_INPUT_REQUIRED = "team_input_required"


class KnowledgeGap(BaseModel):
    """Knowledge gap identified during investigation."""
    id: Optional[int] = None
    investigation_id: int
    component_name: str = Field(..., max_length=200)
    gap_type: KnowledgeGapType
    description: str = Field(..., max_length=1000)
    suggested_action: str = Field(..., max_length=1000)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_resolved: bool = False
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class SystemConfig(BaseModel):
    """System configuration key-value pairs."""
    key: str = Field(..., max_length=100)
    value: str = Field(..., max_length=1000)
    description: Optional[str] = Field(None, max_length=500)
    is_sensitive: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class InvestigationSession(BaseModel):
    """User session for tracking active investigations."""
    id: Optional[int] = None
    user_id: int
    session_token: str = Field(..., max_length=255)
    expires_at: datetime
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None


class UserStats(BaseModel):
    """User statistics."""
    total_investigations: int
    completed_investigations: int
    avg_execution_time_ms: Optional[float]
    knowledge_gaps_identified: int
    last_investigation_date: Optional[datetime]


class SystemStats(BaseModel):
    """System-wide statistics."""
    total_users: int
    total_investigations: int
    active_investigations: int
    total_knowledge_gaps: int
    avg_investigation_time_ms: Optional[float]
    most_quied_components: Optional[Dict[str, int]]