"""
Authentication dependencies for FastAPI.

This module provides authentication and authorization dependencies
using the database layer.
"""

from typing import Optional
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .database import get_database
from api.db import DatabaseAbc
from api.models.database import User, InvestigationSession
from api.app.config import get_settings


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: DatabaseAbc = Depends(get_database)
) -> User:
    """Get the current authenticated user."""
    
    # Get session from database
    session = await db.get_session_by_token(credentials.credentials)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from session
    user = await db.get_user_by_id(session.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current authenticated admin user."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def get_optional_user(
    db: DatabaseAbc = Depends(get_database)
) -> Optional[User]:
    """Get current user if authenticated, otherwise None."""
    try:
        # This allows optional authentication
        return await get_current_user(db=db)
    except HTTPException:
        return None