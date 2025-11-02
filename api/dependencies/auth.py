"""
Authentication dependencies for FastAPI.

This module provides authentication and authorization dependencies
using the database layer and JWT tokens.
"""

from typing import Optional
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .database import get_database
from db import DatabaseAbc
from models.database import User, InvestigationSession
from app.config import get_settings
from app.auth_service import auth_service


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: DatabaseAbc = Depends(get_database)
) -> User:
    """Get the current authenticated user."""
    
    # Verify JWT token
    token_data = auth_service.verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = await db.get_user_by_id(token_data["user_id"])
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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: DatabaseAbc = Depends(get_database)
) -> Optional[User]:
    """Get current user if authenticated, otherwise None."""
    try:
        if not credentials:
            return None
        
        # Verify JWT token
        token_data = auth_service.verify_token(credentials.credentials)
        if not token_data:
            return None
        
        # Get user from database
        user = await db.get_user_by_id(token_data["user_id"])
        return user if user and user.is_active else None
        
    except HTTPException:
        return None


async def get_anonymous_user() -> User:
    """Get the anonymous user for prototype access."""
    # This bypasses authentication entirely for prototype
    from app.auth_service import ANONYMOUS_USER
    return ANONYMOUS_USER


async def get_current_user_or_anonymous(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: DatabaseAbc = Depends(get_database)
) -> User:
    """Get current authenticated user, or anonymous user if no token provided."""
    try:
        if credentials:
            # Try to get authenticated user
            return await get_current_user(credentials, db)
    except HTTPException:
        pass
    
    # Fall back to anonymous user
    return await get_anonymous_user()