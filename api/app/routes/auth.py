from fastapi import APIRouter, HTTPException, status, Depends, Response, Cookie
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional

from app.auth_service import (
    auth_service
)
from dependencies.auth import get_current_user, get_current_user_id, get_optional_user
from dependencies.database import get_database
from db import DatabaseAbc
from models.database import User

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


class TokenResponse(BaseModel):
    """JWT token response model."""
    access_token: str
    token_type: str = "bearer"
    user: User


class LoginRequest(BaseModel):
    """Login request model (for future implementation)."""
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Token refresh request model."""


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    response: Response,
    db: DatabaseAbc = Depends(get_database)
):
    """
    Authenticate user with username/password and return JWT token.
    
    Supports regular user authentication and anonymous login.
    """
    username = login_data.username
    password = login_data.password
    
    # Regular user authentication
    user = await db.get_user_by_username(username)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if username != "anonymous" and not auth_service.verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT token for authenticated user
    token = auth_service.create_user_token(user)
    
    # Set refresh token as HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=auth_service.refresh_token_expire_days * 24 * 60 * 60
    )
    
    # Update last login time
    # await db.update_user_last_login(user.id)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None, alias="refresh_token")
):
    """
    Refresh JWT token using refresh token from HttpOnly cookie.
    
    If no refresh token or invalid token, returns 401 error.
    Frontend should handle this by attempting to login as anonymous.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify the refresh token (for JWT stateless, treat same as access token)
    token_data = auth_service.verify_token(refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    from dependencies.database import get_database
    db = await get_database()
    if not db:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error"
        )
    
    user = await db.get_user_by_id(token_data["user_id"])
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate new access token
    new_token = auth_service.create_user_token(user)
    
    # Set new refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=new_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=auth_service.refresh_token_expire_days * 24 * 60 * 60
    )
    
    return TokenResponse(
        access_token=new_token,
        token_type="bearer",
        user=user
    )


class RegisterRequest(BaseModel):
    """User registration request model."""
    username: str
    email: str
    password: str
    
    class Config:
        str_strip_whitespace = True
        str_min_length = 3


@router.post("/register", response_model=TokenResponse)
async def register(
    register_data: RegisterRequest,
    response: Response,
    db: DatabaseAbc = Depends(get_database)
):
    """
    Register a new user and return JWT token.
    
    Creates a new user with the provided credentials and immediately
    authenticates them by returning a JWT token.
    """
    # Check if user already exists
    existing_user = await db.get_user_by_username(register_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    existing_email = await db.get_user_by_email(register_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Create new user (hash password before passing to database)
    hashed_password = auth_service.get_password_hash(register_data.password)
    user = await db.create_user(
        username=register_data.username,
        email=register_data.email,
        hashed_password=hashed_password
    )
    
    # Generate JWT token for the new user
    token = auth_service.create_user_token(user)
    
    # Set refresh token as HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=auth_service.refresh_token_expire_days * 24 * 60 * 60
    )
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user
    )


@router.post("/logout")
async def logout(
    response: Response,
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Logout current user.
    
    For stateless JWT tokens, this would normally add the token
    to a blacklist. For the prototype, it's a no-op.
    """
    # In a real implementation, you would:
    # 1. Add the token to a blacklist
    # 2. Clear the refresh token cookie
    response.delete_cookie("refresh_token")
    
    return {"message": "Successfully logged out"}


@router.get("/validate-token")
async def validate_token(
    current_user: User = Depends(get_current_user)
):
    """
    Validate that the current token is valid and return user info.
    """
    return {
        "valid": True,
        "user": current_user,
        "message": "Token is valid"
    }
