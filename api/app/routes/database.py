"""
API routes for database operations.

This module provides API endpoints for user management, investigations,
knowledge gaps, and system configuration.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from api.dependencies import get_database, get_current_user, get_current_admin_user
from api.db import DatabaseAbc
from api.models.database import (
    User as DBUser,
    Investigation,
    KnowledgeGap,
    InvestigationStatus,
    KnowledgeGapType,
    UserStats,
    SystemStats
)


# Create router
database_router = APIRouter(prefix="/database", tags=["database"])

# Pydantic models for API requests/responses
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime]

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime

class InvestigationCreate(BaseModel):
    query: str

class InvestigationResponse(BaseModel):
    id: int
    user_id: int
    query: str
    status: str
    component_count: Optional[int]
    knowledge_gap_count: Optional[int]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    execution_time_ms: Optional[int]

class KnowledgeGapCreate(BaseModel):
    component_name: str
    gap_type: str
    description: str
    suggested_action: str

class KnowledgeGapResponse(BaseModel):
    id: int
    investigation_id: int
    component_name: str
    gap_type: str
    description: str
    suggested_action: str
    confidence_score: Optional[float]
    is_resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime]

class ConfigValue(BaseModel):
    key: str
    value: str


# User management endpoints
@database_router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: DatabaseAbc = Depends(get_database)
):
    """Create a new user."""
    # Check if user already exists
    existing_user = await db.get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )
    
    # Hash password (simple implementation for now)
    import bcrypt
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user = await db.create_user(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    return UserResponse(**user.dict())

@database_router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    db: DatabaseAbc = Depends(get_database)
):
    """Authenticate user and return session token."""
    user = await db.get_user_by_username(login_data.username)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    import bcrypt
    if not bcrypt.checkpw(login_data.password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Generate session token
    import secrets
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    await db.create_session(
        user_id=user.id,
        session_token=session_token,
        expires_at=expires_at
    )
    
    return TokenResponse(
        access_token=session_token,
        token_type="bearer",
        expires_at=expires_at
    )

@database_router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: DBUser = Depends(get_current_user)
):
    """Get current user information."""
    return UserResponse(**current_user.dict())

@database_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: DBUser = Depends(get_current_admin_user),
    db: DatabaseAbc = Depends(get_database)
):
    """Get user by ID (admin only)."""
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**user.dict())


# Investigation endpoints
@database_router.get("/investigations", response_model=List[InvestigationResponse])
async def get_user_investigations(
    limit: int = 10,
    current_user: DBUser = Depends(get_current_user),
    db: DatabaseAbc = Depends(get_database)
):
    """Get current user's investigations."""
    investigations = await db.get_user_investigations(current_user.id, limit)
    return [InvestigationResponse(**inv.dict()) for inv in investigations]

@database_router.get("/investigations/{investigation_id}", response_model=InvestigationResponse)
async def get_investigation(
    investigation_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: DatabaseAbc = Depends(get_database)
):
    """Get investigation by ID."""
    investigation = await db.get_investigation_by_id(investigation_id)
    if not investigation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation not found"
        )
    
    # Check if user owns the investigation or is admin
    if investigation.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return InvestigationResponse(**investigation.dict())

@database_router.patch("/investigations/{investigation_id}/status")
async def update_investigation_status(
    investigation_id: int,
    status: str,
    current_user: DBUser = Depends(get_current_admin_user),
    db: DatabaseAbc = Depends(get_database)
):
    """Update investigation status (admin only)."""
    try:
        InvestigationStatus(status)  # Validate status
        success = await db.update_investigation_status(investigation_id, status)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update investigation status"
            )
        return {"status": "updated"}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status}"
        )


# Knowledge gap endpoints
@database_router.get("/investigations/{investigation_id}/knowledge-gaps", response_model=List[KnowledgeGapResponse])
async def get_investigation_knowledge_gaps(
    investigation_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: DatabaseAbc = Depends(get_database)
):
    """Get knowledge gaps for an investigation."""
    # First check if user has access to the investigation
    investigation = await db.get_investigation_by_id(investigation_id)
    if not investigation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation not found"
        )
    
    if investigation.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    knowledge_gaps = await db.get_investigation_knowledge_gaps(investigation_id)
    return [KnowledgeGapResponse(**gap.dict()) for gap in knowledge_gaps]


# Configuration endpoints
@database_router.get("/config/{key}")
async def get_config(
    key: str,
    current_user: DBUser = Depends(get_current_admin_user),
    db: DatabaseAbc = Depends(get_database)
):
    """Get configuration value (admin only)."""
    value = await db.get_config_value(key)
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration key not found"
        )
    
    return {"key": key, "value": value}

@database_router.put("/config/{key}")
async def set_config(
    key: str,
    config_data: ConfigValue,
    current_user: DBUser = Depends(get_current_admin_user),
    db: DatabaseAbc = Depends(get_database)
):
    """Set configuration value (admin only)."""
    success = await db.set_config_value(key, config_data.value)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to set configuration"
        )
    
    return {"key": key, "value": config_data.value}


# Analytics endpoints
@database_router.get("/stats/user")
async def get_user_statistics(
    current_user: DBUser = Depends(get_current_user),
    db: DatabaseAbc = Depends(get_database)
):
    """Get current user statistics."""
    stats = await db.get_user_stats(current_user.id)
    return stats

@database_router.get("/stats/system")
async def get_system_statistics(
    current_user: DBUser = Depends(get_current_admin_user),
    db: DatabaseAbc = Depends(get_database)
):
    """Get system-wide statistics (admin only)."""
    stats = await db.get_system_stats()
    return stats