from fastapi import APIRouter, HTTPException, status, Depends, Response
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional

from api.app.auth_service import (
    auth_service, 
    authenticate_anonymous,
    get_anonymous_token
)
from api.dependencies.auth import get_current_user, get_optional_user
from api.dependencies.database import get_database
from api.db import DatabaseAbc
from api.models.database import User

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


class TokenResponse(BaseModel):
    """JWT token response model."""
    access_token: str
    token_type: str = "bearer"


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
    Login user and return JWT token.
    
    For the prototype, this always returns the anonymous user regardless
    of credentials provided.
    """
    # For prototype, always authenticate as anonymous
    user, token = authenticate_anonymous()
    
    # Set refresh token as HttpOnly cookie (for production - prototype uses JWT only)
    # response.set_cookie(
    #     key="refresh_token",
    #     value=token,  # In production, this would be separate refresh token
    #     httponly=True,
    #     secure=True,
    #     samesite="strict",
    #     max_age=30 * 24 * 60 * 60  # 30 days
    # )
    
    # Update last login time (would normally check credentials first)
    # await db.update_user_last_login(user.id)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer"
    )


@router.post("/login-anonymous", response_model=TokenResponse)
async def login_anonymous_endpoint(response: Response):
    """
    Authenticate as anonymous user for prototype access.
    
    This endpoint provides immediate access without requiring credentials.
    """
    user, token = authenticate_anonymous()
    
    # Set refresh token as HttpOnly cookie
    # response.set_cookie(
    #     key="refresh_token",
    #     value=token,
    #     httponly=True,
    #     secure=True,
    #     samesite="strict",
    #     max_age=30 * 24 * 60 * 60
    # )
    
    return TokenResponse(
        access_token=token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """
    Refresh JWT token using a valid token.
    
    For the prototype, this always returns a new anonymous token.
    """
    # For prototype, just return a new anonymous token
    # In production, this would validate refresh token cookie
    user, new_token = authenticate_anonymous()
    
    # Set new refresh token cookie
    # response.set_cookie(
    #     key="refresh_token",
    #     value=new_token,
    #     httponly=True,
    #     secure=True,
    #     samesite="strict",
    #     max_age=30 * 24 * 60 * 60
    # )
    
    return TokenResponse(
        access_token=new_token,
        token_type="bearer"
    )


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user information."""
    return current_user


@router.get("/me/optional")
async def get_optional_user_info(
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get current user information if authenticated, otherwise anonymous."""
    if current_user:
        return {"user": current_user, "authenticated": True}
    else:
        # Return anonymous user info
        anon_user, _ = authenticate_anonymous()
        return {"user": anon_user, "authenticated": False}


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """
    Logout current user.
    
    For stateless JWT tokens, this would normally add the token
    to a blacklist. For the prototype, it's a no-op.
    """
    # In a real implementation, you would:
    # 1. Add the token to a blacklist
    # 2. Clear the refresh token cookie
    # response.delete_cookie("refresh_token")
    
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


# Public endpoint that doesn't require authentication
@router.get("/public/token")
async def get_public_token():
    """
    Get a public access token for prototype usage.
    
    This endpoint provides a way to get a valid JWT token without
    any authentication checks, suitable for prototype development.
    """
    token = get_anonymous_token()
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 30 * 24 * 60 * 60  # 30 days in seconds
    }