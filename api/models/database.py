"""
Database models for the Enterprise Code Archaeologist.

Pydantic models for structured data storage in the relational database.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field


class User(BaseModel):
    """User model for authentication and authorization."""
    id: int
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    hashed_password: str = Field(..., min_length=60)
    is_active: bool = True
    is_admin: bool = False
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class Project(BaseModel):
    """Project model for organizing investigations."""
    id: int
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    repository_paths: Optional[List[str]] = None  # List of repo paths included in project
    is_active: bool = True
    created_by: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Source(BaseModel):
    """Source model for uploaded files in projects."""
    id: int
    project_id: int
    filename: str = Field(..., max_length=255)
    original_filename: str = Field(..., max_length=255)
    file_size: int = Field(..., ge=0)
    file_type: str = Field(..., max_length=100)  # MIME type
    content_type: str = Field(..., max_length=50)  # text, zip, etc.
    data_lake_entry_id: str = Field(..., max_length=255)  # Reference to data lake entry
    metadata: Optional[Dict[str, Any]] = None  # User-defined metadata like comments
    uploaded_by: int
    created_at: Optional[datetime] = None


class ProjectUser(BaseModel):
    """Many-to-many relationship between projects and users."""
    id: int
    project_id: int
    user_id: int
    role: str = Field(..., pattern=r'^(owner|admin|member|viewer)$')
    is_active: bool = True
    created_at: Optional[datetime] = None


class ProjectRole(str, Enum):
    """Project role enumeration."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


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
    project_id: Optional[int] = None  # Optional project association
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


class Node(BaseModel):
    """Node model for dependency graph components."""
    id: str
    project_id: Optional[int] = None
    name: str = Field(..., max_length=255)
    type: str = Field(..., max_length=50)  # file, api_endpoint, db_table, repo, etc.
    path: Optional[str] = Field(None, max_length=500)
    source_type: str = Field(..., max_length=50)  # investigation, uploaded_file, etc.
    confidence: float = Field(..., ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None  # User-defined metadata like comments
    investigation_id: Optional[int] = None  # Link to investigation if from analysis
    source_id: Optional[int] = None  # Link to source if uploaded file
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class NodeMetadata(BaseModel):
    """Metadata for nodes in the dependency graph."""
    id: Optional[int] = None
    node_id: str
    key: str = Field(..., max_length=100)
    value: str = Field(..., max_length=1000)
    created_by: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SystemStats(BaseModel):
    """System-wide statistics."""
    total_users: int
    total_investigations: int
    active_investigations: int
    total_knowledge_gaps: int
    avg_investigation_time_ms: Optional[float]
    most_quied_components: Optional[Dict[str, int]]